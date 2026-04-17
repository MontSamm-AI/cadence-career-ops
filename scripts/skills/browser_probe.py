#!/usr/bin/env python3
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

CDP_URL = 'http://127.0.0.1:9222'
REPO_ROOT = Path(__file__).resolve().parents[2]
OUT = REPO_ROOT / 'browser_probe_output.json'

result = {
    'cdp_url': CDP_URL,
    'contexts': [],
    'jobs_probe': {}
}

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(CDP_URL)
    for i, ctx in enumerate(browser.contexts):
        ctx_info = {'index': i, 'pages': []}
        for j, page in enumerate(ctx.pages):
            ctx_info['pages'].append({
                'index': j,
                'url': page.url,
                'title': page.title()
            })
        result['contexts'].append(ctx_info)

    ctx = browser.contexts[0]
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.goto('https://www.linkedin.com/jobs/', wait_until='domcontentloaded', timeout=30000)
    page.wait_for_timeout(5000)

    result['jobs_probe']['final_url'] = page.url
    result['jobs_probe']['title'] = page.title()
    result['jobs_probe']['easy_apply_texts'] = page.locator("text=/Easy Apply|Candidatura simplificada/i").all_inner_texts()[:10]
    result['jobs_probe']['job_card_links'] = page.locator("a[href*='/jobs/view/']").evaluate_all(
        "els => els.slice(0,10).map(a => ({text:(a.innerText||'').trim(), href:a.href}))"
    )
    result['jobs_probe']['buttons'] = page.locator('button').evaluate_all(
        "els => els.slice(0,40).map(b => (b.innerText||'').trim()).filter(Boolean)"
    )

OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2))
print(str(OUT))
