#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from typing import Any, Dict, List

from playwright.sync_api import sync_playwright

from auto_apply_lib import CDP_URL, detect_job_id, load_profile, load_queue, now_iso, save_queue

QUERY_PRESETS = {
    'core_br': [
        'https://www.linkedin.com/jobs/search/?f_AL=true&f_TPR=r604800&keywords=AI%20Automation&location=Brazil',
        'https://www.linkedin.com/jobs/search/?f_AL=true&f_TPR=r604800&keywords=n8n&location=Brazil',
        'https://www.linkedin.com/jobs/search/?f_AL=true&f_TPR=r604800&keywords=workflow%20automation&location=Brazil',
    ],
    'fresh_br': [
        'https://www.linkedin.com/jobs/search/?f_AL=true&f_TPR=r86400&keywords=AI%20Automation&location=Brazil',
        'https://www.linkedin.com/jobs/search/?f_AL=true&f_TPR=r86400&keywords=automation%20engineer&location=Brazil',
    ]
}


def classify_cv_key(title: str, location: str) -> str:
    t = (title or '').lower()
    l = (location or '').lower()
    if 'n8n' in t:
        return 'brazil_n8n_automation'
    if any(x in l for x in ['brazil', 'brasil', 'sp']):
        return 'brazil_ai_automation'
    return 'international_ai_automation'


def collect_cards(page) -> List[Dict[str, Any]]:
    return page.evaluate(r"""() => {
      const nodes = [...document.querySelectorAll('a[href*="/jobs/view/"]')];
      const seen = new Set();
      const out = [];
      for (const a of nodes) {
        const href = a.href || '';
        const m = href.match(/\/jobs\/view\/(\d+)/);
        if (!m) continue;
        const jobId = m[1];
        if (seen.has(jobId)) continue;
        seen.add(jobId);
        const card = a.closest('li, .job-card-container, .jobs-search-results__list-item, .artdeco-entity-lockup, .job-card-list');
        const text = (card?.innerText || a.innerText || '').trim();
        out.push({ job_id: jobId, url: href, text });
      }
      return out.slice(0, 80);
    }""")


def parse_text_blob(text: str) -> Dict[str, Any]:
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    title = lines[0] if lines else ''
    dedup = []
    for line in lines[1:]:
        if line == title or line == f'{title} with verification':
            continue
        dedup.append(line)
    company = dedup[0] if len(dedup) > 0 else ''
    location = dedup[1] if len(dedup) > 1 else ''
    low = text.lower()
    easy_apply = 'candidatura simplificada' in low or 'easy apply' in low
    applied = 'candidatou-se' in low or 'applied' in low
    viewed = 'visualizado' in low or 'visto' in low
    return {
        'role': title,
        'company': company,
        'location': location,
        'easy_apply': easy_apply,
        'already_applied': applied,
        'viewed': viewed,
    }


def extract_detail_state(page) -> Dict[str, Any]:
    info = page.evaluate(r'''() => {
      const elements = [...document.querySelectorAll('button, a')].map((b, i) => ({
        i,
        tag: b.tagName.toLowerCase(),
        text: (b.innerText || '').trim(),
        aria: b.getAttribute('aria-label') || '',
        href: b.getAttribute('href') || ''
      }));
      const body = document.body?.innerText || '';
      return { elements, body };
    }''')
    normalized = [f"{b.get('text','')} {b.get('aria','')} {b.get('href','')}".lower() for b in info['elements']]
    easy_apply_available = any(
        (
            'usar a candidatura simplificada' in t or
            'candidatura simplificada à vaga' in t or
            'openSDUIApplyFlow'.lower() in t or
            ('easy apply' in t and 'filter' not in t)
        ) and 'filtro' not in t
        for t in normalized
    )
    already_applied = 'candidatou-se' in info['body'].lower() or 'application submitted' in info['body'].lower()
    return {
        'easy_apply_available': easy_apply_available,
        'already_applied': already_applied,
    }


def title_allowed(title: str, profile) -> bool:
    low = (title or '').lower()
    blocked = [k.lower() for k in profile.raw['job_preferences'].get('blocked_keywords', [])]
    blocked += ['test automation', 'automation test', 'qa automation', 'testing engineer', 'rpa']
    return not any(b in low for b in blocked)


def score_priority(title: str, company: str) -> int:
    low = f'{title} {company}'.lower()
    score = 10
    if 'ai automation' in low or 'automation specialist' in low:
        score -= 6
    if 'ai' in low and 'automation' in low:
        score -= 4
    if 'n8n' in low or 'workflow' in low or 'agents' in low:
        score -= 3
    if 'engineer' in low or 'developer' in low:
        score -= 1
    return max(1, score)


def search(preset: str) -> Dict[str, Any]:
    profile = load_profile()
    queue = load_queue()
    existing_ids = {item.get('linkedin_job_id') for item in queue.get('items', [])}
    found = []
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP_URL)
        ctx = browser.contexts[0] if browser.contexts else browser.new_context()
        for url in QUERY_PRESETS[preset]:
            page = ctx.new_page()
            page.goto(url, wait_until='domcontentloaded', timeout=30000)
            page.wait_for_timeout(3000)
            cards = collect_cards(page)
            seen_local = set()
            for idx, card in enumerate(cards):
                job_id = card['job_id'] or detect_job_id(card['url'])
                if not job_id or job_id in existing_ids or job_id in seen_local:
                    continue
                seen_local.add(job_id)
                parsed = parse_text_blob(card['text'])
                if not parsed['role'] or not title_allowed(parsed['role'], profile):
                    continue
                try:
                    page.goto(card['url'], wait_until='domcontentloaded', timeout=30000)
                    page.wait_for_timeout(1800)
                except Exception:
                    continue
                state = extract_detail_state(page)
                if not state['easy_apply_available'] or state['already_applied']:
                    continue
                found.append({
                    'company': parsed['company'],
                    'role': parsed['role'],
                    'linkedin_job_id': job_id,
                    'url': card['url'],
                    'location': parsed['location'],
                    'easy_apply': True,
                    'status': 'queued',
                    'priority': score_priority(parsed['role'], parsed['company']),
                    'cv_key': classify_cv_key(parsed['role'], parsed['location']),
                    'notes': f'Queued from preset {preset}',
                })
                existing_ids.add(job_id)
    queue['items'].extend(found)
    queue['updated_at'] = now_iso()
    save_queue(queue)
    return {'preset': preset, 'queued': len(found), 'items': found}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--preset', default='core_br', choices=sorted(QUERY_PRESETS))
    args = ap.parse_args()
    print(json.dumps(search(args.preset), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
