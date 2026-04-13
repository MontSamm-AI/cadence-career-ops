#!/home/monts/.venv/jobhunter/bin/python
import json
from pathlib import Path
from datetime import datetime
from playwright.sync_api import sync_playwright

CDP_URL = 'http://127.0.0.1:9222'
URL = 'https://www.hubxp.com.br/vagas/114'
OUTDIR = Path('/home/monts/.openclaw/workspace-linkedin/artifacts/applications/pending')
OUTDIR.mkdir(parents=True, exist_ok=True)
ts = datetime.now().strftime('%Y%m%d_%H%M%S')
out = OUTDIR / f'hubxp_wait_probe_{ts}.json'

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(CDP_URL)
    page = None
    for ctx in browser.contexts:
        for pg in ctx.pages:
            if URL in pg.url:
                page = pg
                break
        if page:
            break
    if not page:
        page = browser.contexts[0].new_page()
        page.goto(URL, wait_until='domcontentloaded', timeout=30000)

    page.reload(wait_until='domcontentloaded', timeout=30000)
    page.wait_for_timeout(12000)

    data = {
        'title': page.title(),
        'url': page.url,
        'body_excerpt': page.locator('body').inner_text()[:12000],
        'h1s': page.locator('h1,h2,h3').evaluate_all("els => els.map(e => (e.innerText||'').trim()).filter(Boolean).slice(0,50)"),
        'buttons': page.locator('button').evaluate_all("els => els.map((b,i)=>({i,text:(b.innerText||'').trim(),aria:b.getAttribute('aria-label'),type:b.getAttribute('type')})).filter(x => x.text || x.aria).slice(0,100)"),
        'links': page.locator('a').evaluate_all("els => els.map((a,i)=>({i,text:(a.innerText||'').trim(),href:a.href})).filter(x => x.text || x.href).slice(0,150)"),
        'fields': page.locator('input,textarea,select').evaluate_all("els => els.map((e,i)=>({i,tag:e.tagName.toLowerCase(),type:e.getAttribute('type'),name:e.getAttribute('name'),id:e.id,placeholder:e.getAttribute('placeholder'),required:e.required})).slice(0,100)"),
    }
    page.screenshot(path=str(OUTDIR / f'hubxp_wait_probe_{ts}.png'), full_page=True)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    print(str(out))
