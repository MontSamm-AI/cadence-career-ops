#!/usr/bin/env python3
import json
import os
from pathlib import Path
from datetime import datetime
from playwright.sync_api import sync_playwright

CDP_URL = 'http://127.0.0.1:9222'
URL = 'https://cpqd.recruitee.com/o/pesquisadora-ii-foco-em-inteligencia-artificial?source=LinkedIn'
WORKSPACE = Path(__file__).resolve().parents[2]
OUTDIR = WORKSPACE / 'artifacts' / 'applications' / 'reviewed'
OUTDIR.mkdir(parents=True, exist_ok=True)
ts = datetime.now().strftime('%Y%m%d_%H%M%S')
out = OUTDIR / f'cpqd_ii_prepare_{ts}.json'

NAME = os.environ.get('CADENCE_CANDIDATE_NAME', 'Candidate Name')
EMAIL = os.environ.get('CADENCE_CANDIDATE_EMAIL', 'candidate@example.com')
PHONE = os.environ.get('CADENCE_CANDIDATE_PHONE', '+55 11 90000-0000')
CV_PATH = os.environ.get('CADENCE_CV_PATH', '/path/to/cv.pdf')

result = {
    'timestamp': datetime.now().isoformat(),
    'target_url': URL,
    'contact_payload': {'name': NAME, 'email': EMAIL, 'phone': PHONE, 'cv_path': CV_PATH},
    'questions': [],
    'filled': [],
    'gates': [],
    'submit_present': False,
}

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(CDP_URL)
    ctx = browser.contexts[0] if browser.contexts else browser.new_context()
    page = ctx.new_page()
    page.goto(URL, wait_until='domcontentloaded', timeout=30000)
    page.wait_for_timeout(7000)

    # Fill base contact fields
    for sel, value in [
        ("input[name='candidate.name']", NAME),
        ("input[name='candidate.email']", EMAIL),
        ("input[name='candidate.phone']", PHONE),
    ]:
        try:
            page.locator(sel).fill(value, timeout=5000)
            result['filled'].append({'selector': sel, 'value': value})
        except Exception as e:
            result['filled'].append({'selector': sel, 'error': str(e)})

    # Upload CV if possible
    try:
        cv_file = Path(CV_PATH)
        if cv_file.exists():
            page.locator("input[name='candidate.cv']").set_input_files(str(cv_file))
            result['filled'].append({'selector': "input[name='candidate.cv']", 'value': str(cv_file)})
        else:
            result['filled'].append({'selector': "input[name='candidate.cv']", 'error': 'CV path not configured or file not found'})
    except Exception as e:
        result['filled'].append({'selector': "input[name='candidate.cv']", 'error': str(e)})

    # Extract question labels and options
    q_blocks = page.locator('fieldset, [role="group"], .form-group, label').all()
    seen = set()
    for i in range(min(len(q_blocks), 80)):
        try:
            txt = q_blocks[i].inner_text().strip()
            if txt and len(txt) > 3 and txt not in seen:
                seen.add(txt)
                if any(k in txt.lower() for k in ['nome completo', 'e-mail', 'celular']):
                    continue
                result['questions'].append({'index': i, 'text': txt[:1000]})
        except Exception:
            pass

    # Try to collect labels by input names
    inputs = page.locator('input, textarea, select').all()
    structured = []
    for el in inputs[:120]:
        try:
            name = el.get_attribute('name')
            typ = el.get_attribute('type')
            idv = el.get_attribute('id') or ''
            placeholder = el.get_attribute('placeholder')
            req = el.is_enabled()
            label_txt = ''
            if idv:
                try:
                    label = page.locator(f"label[for='{idv}']").first
                    if label.count() > 0:
                        label_txt = label.inner_text().strip()
                except Exception:
                    pass
            structured.append({'name': name, 'type': typ, 'id': idv, 'placeholder': placeholder, 'label': label_txt, 'enabled': req})
        except Exception:
            pass
    result['structured_fields'] = structured

    html_lower = page.content().lower()
    for token in ['captcha', 'hcaptcha', 'indeed', 'linkedin']:
        if token in html_lower:
            result['gates'].append(token)

    result['submit_present'] = page.locator("button:has-text('Enviar')").count() > 0
    page.screenshot(path=str(OUTDIR / f'cpqd_ii_prepare_{ts}.png'), full_page=True)
    result['body_excerpt'] = page.locator('body').inner_text()[:12000]
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(str(out))
