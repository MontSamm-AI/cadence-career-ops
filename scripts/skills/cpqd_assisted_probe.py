#!/usr/bin/env python3
import json
from pathlib import Path
from datetime import datetime
from playwright.sync_api import sync_playwright

CDP_URL = 'http://127.0.0.1:9222'
URL = 'https://cpqd.recruitee.com/o/pesquisadora-ii-foco-em-inteligencia-artificial?source=LinkedIn'
WORKSPACE = Path(__file__).resolve().parents[2]
OUTDIR = WORKSPACE / 'artifacts' / 'applications' / 'pending'
OUTDIR.mkdir(parents=True, exist_ok=True)
ts = datetime.now().strftime('%Y%m%d_%H%M%S')
out = OUTDIR / f'cpqd_ii_probe_{ts}.json'

result = {
    'timestamp': datetime.now().isoformat(),
    'target_url': URL,
    'steps': [],
    'fields_before': [],
    'fields_after': [],
    'buttons_before': [],
    'buttons_after': [],
    'gates': [],
}

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(CDP_URL)
    ctx = browser.contexts[0] if browser.contexts else browser.new_context()
    page = ctx.new_page()
    page.goto(URL, wait_until='domcontentloaded', timeout=30000)
    page.wait_for_timeout(8000)

    result['steps'].append({'phase': 'loaded', 'url': page.url, 'title': page.title()})
    result['body_excerpt_before'] = page.locator('body').inner_text()[:8000]
    result['buttons_before'] = page.locator('button,a').evaluate_all(
        "els => els.map((e,i)=>({i,tag:e.tagName.toLowerCase(),text:(e.innerText||'').trim(),href:e.href||null,aria:e.getAttribute('aria-label')})).filter(x => x.text || x.href || x.aria).slice(0,150)"
    )
    result['fields_before'] = page.locator('input,textarea,select').evaluate_all(
        "els => els.map((e,i)=>({i,tag:e.tagName.toLowerCase(),type:e.getAttribute('type'),name:e.getAttribute('name'),id:e.id,placeholder:e.getAttribute('placeholder'),required:e.required,value:e.value||''})).slice(0,150)"
    )

    html_lower = page.content().lower()
    for token in ['captcha', 'hcaptcha', 'indeed', 'linkedin', 'apply', 'candidate', 'currículo', 'curriculo']:
        if token in html_lower or token in result['body_excerpt_before'].lower():
            result['gates'].append(token)

    # find application CTA
    cta = None
    patterns = ['candidatar', 'candidate-se', 'aplicar', 'apply', 'linkedin', 'indeed']
    for item in result['buttons_before']:
        t = f"{item.get('text','')} {item.get('aria','')}".lower()
        if any(p in t for p in patterns):
            cta = item
            break
    result['cta_before'] = cta

    if cta and cta['tag'] == 'button':
        try:
            page.locator('button').nth(cta['i']).click(timeout=5000)
            page.wait_for_timeout(6000)
            result['steps'].append({'phase': 'after_cta_click', 'url': page.url, 'title': page.title()})
            result['body_excerpt_after'] = page.locator('body').inner_text()[:10000]
            result['buttons_after'] = page.locator('button,a').evaluate_all(
                "els => els.map((e,i)=>({i,tag:e.tagName.toLowerCase(),text:(e.innerText||'').trim(),href:e.href||null,aria:e.getAttribute('aria-label')})).filter(x => x.text || x.href || x.aria).slice(0,180)"
            )
            result['fields_after'] = page.locator('input,textarea,select').evaluate_all(
                "els => els.map((e,i)=>({i,tag:e.tagName.toLowerCase(),type:e.getAttribute('type'),name:e.getAttribute('name'),id:e.id,placeholder:e.getAttribute('placeholder'),required:e.required,value:e.value||''})).slice(0,180)"
            )
            page.screenshot(path=str(OUTDIR / f'cpqd_ii_probe_after_{ts}.png'), full_page=True)
        except Exception as e:
            result['cta_click_error'] = str(e)

    page.screenshot(path=str(OUTDIR / f'cpqd_ii_probe_before_{ts}.png'), full_page=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(str(out))
