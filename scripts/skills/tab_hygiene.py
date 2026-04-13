#!/home/monts/.venv/jobhunter/bin/python
from __future__ import annotations

import argparse
import json

from playwright.sync_api import sync_playwright

from auto_apply_lib import CDP_URL, load_queue

KEEP_URL_PATTERNS = [
    'linkedin.com/jobs/search/',
    'linkedin.com/jobs/collections/',
]
IGNORE_URL_PATTERNS = [
    'about:blank',
    'doubleclick',
    'recaptcha',
    'googleads',
]


def run(close_done: bool = False):
    queue = load_queue()
    active_ids = {
        item.get('linkedin_job_id')
        for item in queue.get('items', [])
        if item.get('status') in {'queued', 'in_progress', 'review_ready', 'needs_review'}
    }
    report = {'kept': [], 'closed': [], 'ignored': []}
    kept_search_hub = False
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP_URL)
        for ctx in browser.contexts:
            for page in list(ctx.pages):
                url = page.url
                if any(x in url for x in IGNORE_URL_PATTERNS):
                    report['ignored'].append(url)
                    continue
                keep = False
                if 'linkedin.com/jobs/view/' in url or 'currentJobId=' in url:
                    keep = any(job_id and job_id in url for job_id in active_ids)
                elif any(x in url for x in KEEP_URL_PATTERNS):
                    keep = not kept_search_hub
                    if keep:
                        kept_search_hub = True
                if keep:
                    report['kept'].append(url)
                elif close_done:
                    report['closed'].append(url)
                    page.close()
                else:
                    report['ignored'].append(url)
    return report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--close-done', action='store_true')
    args = ap.parse_args()
    print(json.dumps(run(close_done=args.close_done), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
