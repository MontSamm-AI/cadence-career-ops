#!/home/monts/.venv/jobhunter/bin/python
import json
from pathlib import Path
from datetime import datetime
from playwright.sync_api import sync_playwright

CDP_URL = 'http://127.0.0.1:9222'
TARGET_URL = 'https://www.hubxp.com.br/vagas/114'
WORKSPACE = Path('/home/monts/.openclaw/workspace-linkedin')
ART = WORKSPACE / 'artifacts' / 'applications' / 'pending'
ART.mkdir(parents=True, exist_ok=True)

ts = datetime.now().strftime('%Y%m%d_%H%M%S')
out_json = ART / f'hubxp_probe_{ts}.json'
out_png = ART / f'hubxp_probe_{ts}.png'
out_html = ART / f'hubxp_probe_{ts}.html'

result = {
    'timestamp': datetime.now().isoformat(),
    'target_url': TARGET_URL,
    'steps': [],
    'fields': [],
    'buttons': [],
    'links': [],
    'apply_route': None,
    'gates': [],
}

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(CDP_URL)
    page = None
    for ctx in browser.contexts:
        for pg in ctx.pages:
            if TARGET_URL in pg.url:
                page = pg
                break
        if page:
            break
    if not page:
        ctx = browser.contexts[0]
        page = ctx.new_page()
        page.goto(TARGET_URL, wait_until='domcontentloaded', timeout=30000)
    page.wait_for_timeout(4000)

    result['title'] = page.title()
    result['final_url'] = page.url
    result['steps'].append({'phase': 'loaded', 'url': page.url, 'title': page.title()})

    page.screenshot(path=str(out_png), full_page=True)
    out_html.write_text(page.content(), encoding='utf-8')

    result['buttons'] = page.locator('button').evaluate_all(
        "els => els.map((b,i)=>({i, text:(b.innerText||'').trim(), type:b.getAttribute('type'), aria:b.getAttribute('aria-label')})).filter(x => x.text || x.aria).slice(0,80)"
    )
    result['links'] = page.locator('a').evaluate_all(
        "els => els.map((a,i)=>({i, text:(a.innerText||'').trim(), href:a.href})).filter(x => x.text || x.href).slice(0,120)"
    )
    result['fields'] = page.locator('input, textarea, select').evaluate_all(
        "els => els.map((e,i)=>({i, tag:e.tagName.toLowerCase(), type:e.getAttribute('type'), name:e.getAttribute('name'), id:e.id, placeholder:e.getAttribute('placeholder'), value:e.value||'', required:e.required})).slice(0,120)"
    )

    body_text = page.locator('body').inner_text()[:6000]
    result['body_excerpt'] = body_text

    for token in ['captcha', 'hcaptcha', 'recaptcha', 'linkedin', 'indeed', 'candidate', 'currículo', 'curriculo', 'apply', 'candidatar']:
        if token.lower() in body_text.lower() or token.lower() in page.content().lower():
            result['gates'].append(token)

    # try to identify apply CTA without submitting
    candidate = None
    cta_patterns = ['candidatar', 'apply', 'enviar candidatura', 'quero me candidatar', 'inscrever', 'iniciar candidatura']
    for btn in result['buttons']:
        text = f"{btn.get('text','')} {btn.get('aria','')}".lower()
        if any(p in text for p in cta_patterns):
            candidate = {'kind': 'button', **btn}
            break
    if not candidate:
        for link in result['links']:
            text = f"{link.get('text','')} {link.get('href','')}".lower()
            if any(p in text for p in cta_patterns):
                candidate = {'kind': 'link', **link}
                break
    result['apply_route'] = candidate

    # if there is a non-submit next step, click it and inspect, otherwise stop safely
    if candidate and candidate['kind'] == 'button' and candidate.get('text'):
        try:
            locator = page.locator('button').nth(candidate['i'])
            locator.click(timeout=5000)
            page.wait_for_timeout(4000)
            result['steps'].append({'phase': 'after_cta_click', 'url': page.url, 'title': page.title()})
            result['post_click_fields'] = page.locator('input, textarea, select').evaluate_all(
                "els => els.map((e,i)=>({i, tag:e.tagName.toLowerCase(), type:e.getAttribute('type'), name:e.getAttribute('name'), id:e.id, placeholder:e.getAttribute('placeholder'), value:e.value||'', required:e.required})).slice(0,150)"
            )
            result['post_click_buttons'] = page.locator('button').evaluate_all(
                "els => els.map((b,i)=>({i, text:(b.innerText||'').trim(), type:b.getAttribute('type'), aria:b.getAttribute('aria-label')})).filter(x => x.text || x.aria).slice(0,100)"
            )
            result['post_click_body_excerpt'] = page.locator('body').inner_text()[:6000]
            page.screenshot(path=str(ART / f'hubxp_probe_after_click_{ts}.png'), full_page=True)
        except Exception as e:
            result['cta_click_error'] = str(e)

    out_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(str(out_json))
