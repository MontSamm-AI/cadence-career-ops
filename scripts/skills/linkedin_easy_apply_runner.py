#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from auto_apply_lib import (
    CDP_URL,
    load_compensation_reference,
    load_profile,
    now_iso,
    update_index_with_result,
    update_queue_item,
    write_artifact,
)

SAFE_YES_PATTERNS = [
    r"automation",
    r"workflow",
    r"n8n",
    r"remote",
    r"presencial",
    r"on[- ]?site",
    r"available.*immediately",
    r"hybrid",
    r"h[ií]brid",
    r"modelo h[ií]brido",
    r"modelo presencial",
    r"contractor",
    r"llm",
    r"nlp",
    r"generative",
    r"genai",
    r"ia generativa",
    r"api",
    r"technical test",
    r"teste t[eé]cnico",
    r"segmento de tecnologia",
    r"technology segment",
    r"multiagentes?",
    r"multiagents?",
    r"agentic",
    r"ai agents?",
]
ENGLISH_PATTERNS = [r"english", r"ingl[eê]s"]
ADVANCED_ENGLISH_BOOL_PATTERNS = [r"advanced english", r"ingl[eê]s avan[cç]ado"]
AUTOMATION_YEARS_PATTERNS = [r"years?.*(automation|workflow|n8n|agentic)", r"building automated workflows"]
AI_YEARS_PATTERNS = [r"years?.*(ai|artificial intelligence|llm|genai|machine learning|prompt|chatbots?|conversational ai)", r"how many years.*(ai|artificial intelligence|llm|genai|chatbots?)", r"h[áa] quantos anos.*(ia|intelig[eê]ncia artificial|llm|chatbots?)"]
IT_YEARS_PATTERNS = [r"years?.*(\bit\b|information technology|tecnologia da informa[cç][aã]o|\bti\b|jira)", r"how many years.*(information technology|\bit\b|\bti\b|jira)", r"h[áa] quantos anos.*(jira|tecnologia da informa[cç][aã]o|\bti\b)"]
DEV_YEARS_PATTERNS = [r"years?.*(coding|programming|software development|python|back[- ]?end|javascript|visual studio code|vscode)", r"how many years.*(coding|programming|software development|python|back[- ]?end|javascript|visual studio code|vscode)", r"h[áa] quantos anos.*(python|back[- ]?end|javascript|visual studio code|vscode)"]
COMPENSATION_PATTERNS = [
    r"\bsalary\b",
    r"\bcompensation\b",
    r"pretens[aã]o salarial",
    r"pretens[aã]o",
    r"remunera[cç][aã]o",
    r"expected salary",
    r"desired compensation",
    r"sal[aá]rio",
]
ALWAYS_SENSITIVE_PATTERNS = [
    r"work authorization",
    r"\bvisa\b",
    r"\bsponsorship\b",
    r"\brelocation\b",
    r"security clearance",
    r"\bveteran\b",
    r"\bdisability\b",
]
SAFE_NO_PATTERNS = {
    r"power\s*bi": "power_bi",
    r"power\s*automate": "power_automate",
    r"power\s*apps?": "power_apps",
    r"uipath": "uipath",
    r"databricks": "databricks",
    r"ecossistema aws|sagemaker|bedrock": "aws_bedrock_sagemaker",
    r"machine learning e/ou ci[êe]ncia de dados|ci[êe]ncia de dados|data science": "ml_data_science_core",
}


def question_has(patterns: List[str], text: str) -> bool:
    return any(re.search(p, text, re.I) for p in patterns)


def numeric_hint_for_input(inp, low: str) -> bool:
    inp_type = (inp.get_attribute('type') or '').lower()
    return inp_type == 'number' or 'numeric' in low or 'salary' in low or 'compensation' in low or 'pretens' in low or 'remunera' in low


def boolish_answer(value: str) -> str:
    return 'Yes' if str(value).strip().lower() in {'yes', 'sim', 'true'} else 'No'


def desired_answer_for_block(block: str, job: Dict[str, Any], profile, compensation) -> Tuple[str | None, float | None]:
    low = block.lower()

    if question_has(ADVANCED_ENGLISH_BOOL_PATTERNS, low):
        return 'Yes', None
    if question_has(ENGLISH_PATTERNS, low):
        return 'Professional', None
    if question_has(AI_YEARS_PATTERNS, low):
        return profile.experience_defaults.get('ai_applied_years_numeric', '2'), None
    if question_has(IT_YEARS_PATTERNS, low) or question_has(DEV_YEARS_PATTERNS, low):
        return profile.experience_defaults.get('it_years_numeric', '4'), None
    if question_has(AUTOMATION_YEARS_PATTERNS, low):
        return profile.experience_defaults.get('workflow_automation_years_numeric', '3'), None
    if question_has(COMPENSATION_PATTERNS, low):
        comp = compensation.compensation_answer(job, low)
        return comp['answer'], comp['amount']
    for pattern, skill_key in SAFE_NO_PATTERNS.items():
        if re.search(pattern, low, re.I):
            return boolish_answer(profile.skills_truth_defaults.get(skill_key, 'No')), None
    if question_has(SAFE_YES_PATTERNS, low):
        return 'Yes', None
    return None, None


def maybe_answer_select(sel, block: str, job: Dict[str, Any], profile, compensation) -> Tuple[str | None, str | None]:
    options = sel.locator('option')
    option_texts = [options.nth(j).inner_text().strip() for j in range(options.count())]
    desired, target_amount = desired_answer_for_block(block, job, profile, compensation)
    if not desired:
        return None, None

    target = None
    desired_low = desired.lower()
    if target_amount is not None:
        target = compensation.range_choice(option_texts, target_amount)
    elif desired_low in {'yes', 'sim'}:
        target = next((t for t in option_texts if t.lower() in {'yes', 'sim'}), None)
    elif desired_low in {'no', 'não', 'nao'}:
        target = next((t for t in option_texts if t.lower() in {'no', 'não', 'nao'}), None)
    else:
        target = next((t for t in option_texts if desired_low in t.lower() or t.lower().startswith(desired_low)), None)

    return target, desired


def answer_comboboxes(dlg, job: Dict[str, Any], profile, compensation) -> List[Dict[str, str]]:
    answered = []
    combos = dlg.locator('[role="combobox"]')
    for i in range(combos.count()):
        combo = combos.nth(i)
        try:
            block = combo.get_attribute('aria-label') or combo.locator('xpath=ancestor::*[self::div or self::fieldset][1]').inner_text().strip()
            desired, _ = desired_answer_for_block(block, job, profile, compensation)
            if not desired:
                continue
            combo.click()
            dlg.page.wait_for_timeout(300)
            option = dlg.page.get_by_role('option', name=re.compile(rf'^{re.escape(desired)}$', re.I))
            if option.count() == 0 and desired.lower() == 'yes':
                option = dlg.page.get_by_role('option', name=re.compile(r'^(yes|sim)$', re.I))
            if option.count() == 0 and desired.lower() == 'no':
                option = dlg.page.get_by_role('option', name=re.compile(r'^(no|não|nao)$', re.I))
            if option.count() == 0:
                option = dlg.page.locator(f'text=/^{re.escape(desired)}$/i')
            if option.count() > 0:
                option.first.click()
                answered.append({'question': block[:160], 'answer': desired})
        except Exception:
            continue
    return answered


def answer_radio_groups(dlg, job: Dict[str, Any], profile, compensation) -> List[Dict[str, str]]:
    answered = []
    groups = dlg.locator('fieldset, [role="radiogroup"]')
    seen = set()
    for i in range(groups.count()):
        group = groups.nth(i)
        try:
            block = group.inner_text().strip()
        except Exception:
            continue
        low = block.lower()
        if not block or low in seen:
            continue
        seen.add(low)
        desired, _ = desired_answer_for_block(block, job, profile, compensation)
        if not desired:
            continue
        candidates = [desired]
        if desired.lower() == 'yes':
            candidates = ['Yes', 'Sim']
        elif desired.lower() == 'no':
            candidates = ['No', 'Não', 'Nao']
        clicked = False
        for label in candidates:
            try:
                option = group.get_by_text(re.compile(rf'^\s*{re.escape(label)}\s*$', re.I))
                if option.count() > 0:
                    option.first.click(force=True)
                    answered.append({'question': block[:160], 'answer': desired})
                    clicked = True
                    break
            except Exception:
                continue
        if clicked:
            continue
        radios = group.locator('input[type="radio"], [role="radio"]')
        for j in range(radios.count()):
            radio = radios.nth(j)
            meta = ' '.join([
                radio.get_attribute('value') or '',
                radio.get_attribute('aria-label') or '',
                radio.inner_text() if hasattr(radio, 'inner_text') else '',
            ]).strip().lower()
            if any(c.lower() in meta for c in candidates):
                try:
                    radio.click(force=True)
                    answered.append({'question': block[:160], 'answer': desired})
                    break
                except Exception:
                    continue
    return answered


def page_for_job(browser, job: Dict[str, Any]):
    job_id = job['linkedin_job_id']
    for ctx in browser.contexts:
        for page in ctx.pages:
            if f"currentJobId={job_id}" in page.url or f"/jobs/view/{job_id}" in page.url:
                page.bring_to_front()
                return page
    ctx = browser.contexts[0] if browser.contexts else browser.new_context()
    page = ctx.new_page()
    target_url = job.get('url') or f'https://www.linkedin.com/jobs/view/{job_id}/'
    page.goto(target_url, wait_until='domcontentloaded', timeout=30000)
    page.wait_for_timeout(1800)
    return page


def open_easy_apply(page):
    page.bring_to_front()
    candidates = page.locator('button, a')
    for i in range(candidates.count()):
        el = candidates.nth(i)
        label = f"{el.inner_text()} {el.get_attribute('aria-label') or ''} {el.get_attribute('href') or ''}".strip().lower()
        if (
            'usar a candidatura simplificada' in label or
            'candidatura simplificada à vaga' in label or
            'opensduiapplyflow=true' in label or
            (('candidatura simplificada' in label or 'easy apply' in label) and 'filtro' not in label)
        ):
            try:
                el.click()
                page.wait_for_timeout(1800)
                return True
            except Exception:
                href = el.get_attribute('href')
                if href:
                    page.goto(href, wait_until='domcontentloaded', timeout=30000)
                    page.wait_for_timeout(1800)
                    return True
                continue
    return False


def dialog(page):
    selectors = [
        '[role="dialog"]',
        '.jobs-easy-apply-modal',
        '.artdeco-modal',
        'div[aria-label*="Candidate-se" i]',
        'div[aria-label*="Apply to" i]',
    ]
    last_err = None
    for sel in selectors:
        dlg = page.locator(sel).last
        try:
            dlg.wait_for(timeout=3000)
            return dlg
        except Exception as e:
            last_err = e
    raise last_err or RuntimeError('Easy Apply dialog not found')


def extract_dialog_snapshot(dlg) -> Dict[str, Any]:
    return dlg.evaluate(
        """(el) => ({
            text: (el.innerText || '').slice(0, 5000),
            buttons: [...el.querySelectorAll('button')].map(b => ({text:(b.innerText||'').trim(), aria:b.getAttribute('aria-label')||''})).slice(0, 40),
            inputs: [...el.querySelectorAll('input, textarea, select')].map(i => ({tag:i.tagName.toLowerCase(), type:i.type||'', name:i.name||'', id:i.id||'', placeholder:i.placeholder||'', value:i.value||'', aria:i.getAttribute('aria-label')||''})).slice(0, 60)
        })"""
    )


def choose_email(dlg, profile) -> str:
    target = profile.primary_email
    selects = dlg.locator('select')
    for i in range(selects.count()):
        sel = selects.nth(i)
        try:
            options = sel.locator('option')
            texts = [options.nth(j).inner_text().strip() for j in range(options.count())]
            if any(target in t for t in texts):
                for text in texts:
                    if target in text:
                        sel.select_option(label=text)
                        return target
        except Exception:
            pass
    email_inputs = dlg.locator('input[type="email"], input[autocomplete="email"], input[id*="email" i], input[name*="email" i]')
    if email_inputs.count() > 0:
        inp = email_inputs.first
        current = inp.input_value().strip()
        if current != target:
            inp.fill(target)
        return target
    return target


def choose_phone(dlg, profile) -> str:
    phone_inputs = dlg.locator('input[type="tel"], input[autocomplete="tel"], input[id*="phone" i], input[name*="phone" i]')
    if phone_inputs.count() > 0:
        inp = phone_inputs.first
        current = inp.input_value().strip()
        if not current or "5715" not in current:
            inp.fill(profile.phone_e164)
    return profile.phone_e164


def advance(dlg) -> str:
    buttons = dlg.locator('button')
    preferred = [
        'avançar', 'próxima', 'next', 'continue',
        'revisar', 'revise', 'review',
        'enviar candidatura', 'submit application', 'enviar', 'submit',
        'concluído', 'done'
    ]
    meta = buttons.evaluate_all(
        """(els) => els.map((b, i) => ({
            i,
            text: ((b.innerText || '') + ' ' + (b.getAttribute('aria-label') || '')).trim().toLowerCase(),
            disabled: !!b.disabled || b.getAttribute('aria-disabled') === 'true'
        }))"""
    )
    for wanted in preferred:
        for item in meta:
            if wanted in item['text'] and not item['disabled']:
                try:
                    buttons.nth(item['i']).click()
                    return wanted
                except Exception:
                    continue
    raise RuntimeError("No actionable advance/review/submit button found")


def choose_cv(dlg, job: Dict[str, Any], profile) -> str:
    cv = profile.cv_for_job(job)
    desired = cv['file']
    if desired.endswith('.pdf'):
        desired_alt = desired
    else:
        desired_alt = desired + '.pdf'
    labels = dlg.locator('text=/CV_SamiMonteleone/i')
    found = False
    for i in range(labels.count()):
        text = labels.nth(i).inner_text().strip()
        if desired in text or desired_alt in text:
            found = True
            container = labels.nth(i).locator('xpath=ancestor::*[self::div or self::li][1]')
            radio = container.locator('input[type="radio"], [role="radio"]')
            if radio.count() > 0:
                try:
                    radio.first.check(force=True)
                except Exception:
                    radio.first.click(force=True)
            return cv['path']
    upload = dlg.get_by_role('button', name=re.compile('Upload resume|carregar curr[ií]culo', re.I))
    if upload.count() > 0:
        with dlg.page.expect_file_chooser() as fc_info:
            upload.first.click()
        fc_info.value.set_files(cv['path'])
        return cv['path']
    if labels.count() > 0:
        fallback_text = labels.first.inner_text().strip()
        return fallback_text
    if found:
        return cv['path']
    raise RuntimeError(f"Desired CV not found and upload unavailable: {desired}")


def answer_safe_questions(dlg, job: Dict[str, Any], profile) -> Tuple[List[Dict[str, str]], List[str]]:
    answered = []
    blockers = []
    compensation = load_compensation_reference()
    text = dlg.inner_text().lower()
    for pat in ALWAYS_SENSITIVE_PATTERNS:
        if re.search(pat, text, re.I):
            blockers.append(f"sensitive_question:{pat}")
    if blockers:
        return answered, blockers

    inputs = dlg.locator('input:not([type="hidden"]):not([type="radio"]):not([type="checkbox"]):not([type="file"]):not([type="submit"]):not([type="button"]), textarea')
    for i in range(inputs.count()):
        inp = inputs.nth(i)
        try:
            label_block = inp.locator('xpath=ancestor::*[self::div or self::fieldset][1]').inner_text().strip()
        except Exception:
            label_block = ''
        field_meta = ' '.join([
            label_block,
            inp.get_attribute('aria-label') or '',
            inp.get_attribute('placeholder') or '',
            inp.get_attribute('name') or '',
            inp.get_attribute('id') or '',
        ]).strip()
        low = field_meta.lower()
        value = None
        numeric_hint = numeric_hint_for_input(inp, low)
        if question_has(AI_YEARS_PATTERNS, low) or question_has(IT_YEARS_PATTERNS, low) or question_has(DEV_YEARS_PATTERNS, low) or question_has(AUTOMATION_YEARS_PATTERNS, low):
            numeric_hint = True
        if re.search(r'current location', low):
            value = 'Brazil'
        elif question_has(COMPENSATION_PATTERNS, low):
            value = compensation.compensation_answer(job, low, numeric_only=numeric_hint)['answer']
        elif any(re.search(p, low) for p in ENGLISH_PATTERNS):
            value = profile.raw['approved_short_answers']['english_proficiency']
        elif question_has(AI_YEARS_PATTERNS, low):
            value = profile.experience_defaults['ai_applied_years_numeric'] if numeric_hint else profile.experience_defaults['ai_applied_years_text']
        elif question_has(IT_YEARS_PATTERNS, low):
            value = profile.experience_defaults['it_years_numeric'] if numeric_hint else profile.experience_defaults['it_years_text']
        elif question_has(DEV_YEARS_PATTERNS, low):
            value = profile.experience_defaults['it_years_numeric'] if numeric_hint else profile.experience_defaults['it_years_text']
        elif question_has(AUTOMATION_YEARS_PATTERNS, low):
            value = profile.experience_defaults['workflow_automation_years_numeric'] if numeric_hint else profile.experience_defaults['workflow_automation_years_text']
        elif any(re.search(pattern, low, re.I) for pattern in SAFE_NO_PATTERNS):
            for pattern, skill_key in SAFE_NO_PATTERNS.items():
                if re.search(pattern, low, re.I):
                    value = profile.skills_truth_defaults.get(skill_key, 'No')
                    break
        elif any(re.search(p, low) for p in SAFE_YES_PATTERNS):
            value = 'Yes'
        current_value = inp.input_value().strip()
        should_fill = not current_value or (numeric_hint and not re.fullmatch(r'\d+(\.\d+)?', current_value))
        if value is not None and should_fill:
            inp.fill(value)
            answered.append({'question': field_meta[:160], 'answer': value})

    selects = dlg.locator('select')
    for i in range(selects.count()):
        sel = selects.nth(i)
        try:
            block = sel.locator('xpath=ancestor::*[self::div or self::fieldset][1]').inner_text().strip()
            target, answer_key = maybe_answer_select(sel, block, job, profile, compensation)
            if target:
                sel.select_option(label=target)
                answered.append({'question': block[:160], 'answer': answer_key or target})
        except Exception:
            pass
    answered.extend(answer_comboboxes(dlg, job, profile, compensation))
    answered.extend(answer_radio_groups(dlg, job, profile, compensation))
    return answered, blockers


def run_job(job: Dict[str, Any], dry_run: bool = False) -> Dict[str, Any]:
    profile = load_profile()
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP_URL)
        page = page_for_job(browser, job)
        body_text = (page.locator('body').inner_text() or '').lower()
        if any(marker in body_text for marker in ['candidatou-se', 'candidatura enviada', 'status da candidatura']):
            result = {
                'job_id': job['linkedin_job_id'],
                'status': 'applied',
                'started_at': now_iso(),
                'url': page.url,
                'company': job.get('company'),
                'role': job.get('role'),
                'email_used': profile.primary_email,
                'phone_used': profile.phone_e164,
                'answered_questions': [],
                'steps': [{'at': now_iso(), 'snapshot': 'already applied detected on page'}],
                'source': 'linkedin_easy_apply',
                'notes': 'Page already showed applied state.'
            }
            write_artifact('applied', {**job, **result})
            update_queue_item(job['linkedin_job_id'], {'status': 'applied', 'applied_at': now_iso(), 'notes': result['notes']})
            update_index_with_result(job, result)
            return result
        try:
            dlg = dialog(page)
        except Exception:
            if not open_easy_apply(page):
                body_text = (page.locator('body').inner_text() or '').lower()
                if any(marker in body_text for marker in ['candidatou-se', 'candidatura enviada', 'status da candidatura']):
                    result = {
                        'job_id': job['linkedin_job_id'],
                        'status': 'applied',
                        'started_at': now_iso(),
                        'url': page.url,
                        'company': job.get('company'),
                        'role': job.get('role'),
                        'email_used': profile.primary_email,
                        'phone_used': profile.phone_e164,
                        'answered_questions': [],
                        'steps': [{'at': now_iso(), 'snapshot': 'already applied detected on page'}],
                        'source': 'linkedin_easy_apply',
                        'notes': 'Page already showed applied state.'
                    }
                    write_artifact('applied', {**job, **result})
                    update_queue_item(job['linkedin_job_id'], {'status': 'applied', 'applied_at': now_iso(), 'notes': result['notes']})
                    update_index_with_result(job, result)
                    return result
                raise RuntimeError('Easy Apply button not found and dialog not open')
            dlg = dialog(page)
        result = {
            'job_id': job['linkedin_job_id'],
            'status': 'in_progress',
            'started_at': now_iso(),
            'url': page.url,
            'company': job.get('company'),
            'role': job.get('role'),
            'email_used': profile.primary_email,
            'phone_used': profile.phone_e164,
            'answered_questions': [],
            'steps': [],
            'source': 'linkedin_easy_apply',
        }
        for _ in range(8):
            snap = extract_dialog_snapshot(dlg)
            result['steps'].append({'at': now_iso(), 'snapshot': snap['text'][:1200]})
            lower = snap['text'].lower()
            choose_email(dlg, profile)
            choose_phone(dlg, profile)
            if 'resume' in lower or 'currículo' in lower or 'curriculo' in lower:
                cv_path = choose_cv(dlg, job, profile)
                result['cv_used'] = Path(cv_path).name
            answered, blockers = answer_safe_questions(dlg, job, profile)
            result['answered_questions'].extend(answered)
            if blockers:
                result['status'] = 'blocked'
                result['blocker_reason'] = ', '.join(blockers)
                result['notes'] = f"Blocked for human decision: {result['blocker_reason']}"
                break
            if re.search(r'(application submitted|candidatura enviada|your application was sent|successfully submitted|foi enviada)', lower, re.I):
                result['status'] = 'applied'
                break
            action = advance(dlg)
            result['steps'].append({'at': now_iso(), 'action': action})
            page.wait_for_timeout(1200)
            try:
                dlg = dialog(page)
            except Exception:
                body_text = (page.locator('body').inner_text() or '').lower()
                if any(marker in body_text for marker in ['candidatura enviada', 'status da candidatura', 'foi enviada']):
                    result['status'] = 'applied'
                    result['steps'].append({'at': now_iso(), 'snapshot': 'applied state detected after action'})
                    break
                raise
        else:
            result['status'] = 'needs_review'
            result['notes'] = 'Loop limit reached before confirmation.'

        if dry_run and result['status'] == 'applied':
            result['status'] = 'review_ready'
            result['notes'] = 'Dry-run prevented final submission classification.'

        if result['status'] == 'applied':
            result['notes'] = 'Easy Apply advanced to confirmation.'
        artifact_status = 'applied' if result['status'] == 'applied' else 'blocked' if result['status'] == 'blocked' else 'in_progress'
        write_artifact(artifact_status, {**job, **result})
        update_queue_item(job['linkedin_job_id'], {
            'status': result['status'],
            'applied_at': now_iso() if result['status'] == 'applied' else job.get('applied_at'),
            'notes': result.get('notes', job.get('notes', '')),
        })
        if result['status'] in {'applied', 'blocked'}:
            update_index_with_result(job, result)
        return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--job-json', help='Inline JSON for a queue item')
    ap.add_argument('--job-id', help='LinkedIn job id to find in queue')
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()

    from auto_apply_lib import load_queue
    queue = load_queue()
    job = None
    if args.job_json:
        job = json.loads(args.job_json)
    elif args.job_id:
        for item in queue.get('items', []):
            if item.get('linkedin_job_id') == args.job_id:
                job = item
                break
    if not job:
        raise SystemExit('Job not found. Use --job-id or --job-json.')
    print(json.dumps(run_job(job, dry_run=args.dry_run), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
