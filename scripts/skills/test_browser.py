#!/usr/bin/env python3
"""
Test browser connection via Chrome CDP (port 9222)
Run: source ~/.venv/jobhunter/bin/activate && python3 test_browser.py
"""
import sys
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print('ERROR: Activate venv first: source ~/.venv/jobhunter/bin/activate')
    sys.exit(1)

CDP_URL = 'http://127.0.0.1:9222'

def test_connection():
    import urllib.request
    try:
        with urllib.request.urlopen(f'{CDP_URL}/json/version', timeout=3) as r:
            import json
            info = json.loads(r.read())
            print(f'Chrome version: {info.get("Browser","?")}')
            return True
    except Exception as e:
        print(f'Chrome CDP not reachable at {CDP_URL}')
        print('Run your Chrome CDP launcher on Windows first')
        return False

if not test_connection():
    sys.exit(1)

print('Connecting via Playwright...')
with sync_playwright() as p:
    try:
        browser = p.chromium.connect_over_cdp(CDP_URL)
        contexts = browser.contexts
        print(f'Browser connected: {len(contexts)} context(s)')
        for ctx in contexts:
            for page in ctx.pages:
                print(f'  Tab: {page.url[:80]}')
        print('Browser connection: OK')
    except Exception as e:
        print(f'Connection failed: {e}')
