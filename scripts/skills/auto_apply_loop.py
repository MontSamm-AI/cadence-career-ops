#!/home/monts/.venv/jobhunter/bin/python
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from auto_apply_lib import WORKSPACE, load_queue, load_rules

PY = sys.executable
SKILLS = WORKSPACE / 'skills'


def run_cmd(args):
    cp = subprocess.run(args, cwd=str(WORKSPACE), capture_output=True, text=True)
    if cp.returncode != 0:
        raise RuntimeError(cp.stderr or cp.stdout)
    return json.loads(cp.stdout)


def process_queue(limit: int, dry_run: bool = False):
    queue = load_queue()
    processed = []
    items = sorted(queue.get('items', []), key=lambda x: (x.get('priority', 999), x.get('company', '')))
    for item in items:
        if len(processed) >= limit:
            break
        if item.get('status') not in {'queued', 'in_progress', 'review_ready', 'needs_review'}:
            continue
        args = [PY, str(SKILLS / 'linkedin_easy_apply_runner.py'), '--job-id', item['linkedin_job_id']]
        if dry_run:
            args.append('--dry-run')
        result = run_cmd(args)
        processed.append(result)
    return processed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--preset', default='core_br')
    ap.add_argument('--discover', action='store_true')
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    rules = load_rules()
    limit = rules['batch_limits']['target_submissions_per_round']
    discovered = None
    if args.discover:
        discovered = run_cmd([PY, str(SKILLS / 'linkedin_job_search.py'), '--preset', args.preset])
    processed = process_queue(limit=limit, dry_run=args.dry_run)
    hygiene = run_cmd([PY, str(SKILLS / 'tab_hygiene.py'), '--close-done'])
    print(json.dumps({
        'discovered': discovered,
        'processed': processed,
        'hygiene': hygiene,
    }, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
