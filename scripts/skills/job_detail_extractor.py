#!/usr/bin/env python3
"""
job_detail_extractor.py — Extração estruturada de vagas via CDP
Cadence Profissional · Onda 1 · v1.0 · 2026-04-06

Abre uma URL de vaga no Chrome via CDP, extrai campos estruturados
(título, empresa, requisitos, apply mode) e salva artefatos.

Uso:
    python3 job_detail_extractor.py --url "https://linkedin.com/jobs/..."
    python3 job_detail_extractor.py --url URL --save-artifacts
    python3 job_detail_extractor.py --scan-tabs  # extrai de abas abertas
"""

import json
import sys
import time
import argparse
from datetime import datetime
from pathlib import Path

# Caminhos
WORKSPACE = Path(__file__).parent.parent
JOBS_DIR = WORKSPACE / "artifacts" / "browser" / "jobs"
SCREENSHOTS_DIR = WORKSPACE / "artifacts" / "browser" / "screenshots"
HTML_DIR = WORKSPACE / "artifacts" / "browser" / "html"
for d in [JOBS_DIR, SCREENSHOTS_DIR, HTML_DIR]:
    d.mkdir(parents=True, exist_ok=True)

CDP_URL = "http://127.0.0.1:9222"

# Seletores LinkedIn Jobs
LINKEDIN_SELECTORS = {
    "title": [
        ".job-details-jobs-unified-top-card__job-title h1",
        ".jobs-unified-top-card__job-title h1",
        "[class*='job-title'] h1",
        "h1.t-24",
    ],
    "company": [
        ".job-details-jobs-unified-top-card__company-name a",
        ".jobs-unified-top-card__company-name a",
        ".topcard__org-name-link",
    ],
    "location": [
        ".job-details-jobs-unified-top-card__bullet",
        ".jobs-unified-top-card__bullet",
        ".topcard__flavor--bullet",
    ],
    "description": [
        ".jobs-description__content",
        ".jobs-box__html-content",
        "#job-details",
        ".description__text",
    ],
    "easy_apply": [
        "button[aria-label*='Easy Apply']",
        "button.jobs-apply-button",
        ".jobs-apply-button",
    ],
    "apply_button": [
        "button[aria-label*='Apply']",
        ".jobs-apply-button",
        "a[href*='apply']",
    ],
}

# Seletores para ATS externos genéricos
GENERIC_SELECTORS = {
    "title": ["h1", ".job-title", "[class*='position']", "[class*='job-title']"],
    "company": [".company", "[class*='company']", "[class*='employer']"],
    "description": ["[class*='description']", "[class*='requirements']", "main"],
}


def detect_platform(url: str) -> str:
    url = url.lower()
    if "linkedin.com/jobs" in url:
        return "linkedin"
    elif "recruitee.com" in url:
        return "recruitee"
    elif "greenhouse.io" in url:
        return "greenhouse"
    elif "lever.co" in url:
        return "lever"
    elif "workday.com" in url:
        return "workday"
    elif "gupy.io" in url:
        return "gupy"
    elif "pandape" in url or "infojobs" in url:
        return "pandape"
    elif "hubxp.com.br" in url:
        return "hubxp"
    elif "upwork.com" in url:
        return "upwork"
    else:
        return "generic"


def extract_with_playwright(url: str, save_artifacts: bool = True) -> dict:
    """Extrai dados estruturados de uma vaga via Playwright + CDP."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return {"error": "Playwright não instalado"}

    platform = detect_platform(url)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = url.split("/")[-1][:30].replace("?", "_").replace("=", "_")

    result = {
        "url": url,
        "platform": platform,
        "timestamp": datetime.now().isoformat(),
        "title": None,
        "company": None,
        "location": None,
        "description": None,
        "apply_mode": "unknown",  # easy_apply | external | manual
        "has_easy_apply": False,
        "external_apply_url": None,
        "salary": None,
        "remote_mode": None,
        "seniority": None,
        "artifacts": {},
    }

    try:
        with sync_playwright() as p:
            # Tentar conectar a aba existente primeiro
            browser = p.chromium.connect_over_cdp(CDP_URL)
            target_page = None

            for ctx in browser.contexts:
                for page in ctx.pages:
                    if url in page.url or page.url in url:
                        target_page = page
                        break

            # Se não encontrou aba existente, abrir nova
            if not target_page:
                ctx = browser.contexts[0] if browser.contexts else browser.new_context()
                target_page = ctx.new_page()
                target_page.goto(url, wait_until="networkidle", timeout=15000)
                time.sleep(2)

            page = target_page

            # Screenshot
            if save_artifacts:
                ss_path = SCREENSHOTS_DIR / f"job_{platform}_{ts}_{slug}.png"
                page.screenshot(path=str(ss_path), full_page=True)
                result["artifacts"]["screenshot"] = str(ss_path)

            # HTML
            if save_artifacts:
                html_content = page.content()
                html_path = HTML_DIR / f"job_{platform}_{ts}_{slug}.html"
                html_path.write_text(html_content, encoding="utf-8")
                result["artifacts"]["html"] = str(html_path)

            # Extração de campos
            selectors = LINKEDIN_SELECTORS if platform == "linkedin" else GENERIC_SELECTORS

            for field, sel_list in selectors.items():
                if field in ["easy_apply", "apply_button"]:
                    continue
                for sel in sel_list:
                    try:
                        el = page.query_selector(sel)
                        if el:
                            text = el.inner_text().strip()
                            if text and len(text) > 1:
                                result[field] = text[:5000] if field == "description" else text[:200]
                                break
                    except Exception:
                        continue

            # Verificar Easy Apply
            for sel in LINKEDIN_SELECTORS["easy_apply"]:
                try:
                    el = page.query_selector(sel)
                    if el and el.is_visible():
                        result["has_easy_apply"] = True
                        result["apply_mode"] = "easy_apply"
                        break
                except Exception:
                    continue

            # Se não tem Easy Apply, verificar apply externo
            if not result["has_easy_apply"]:
                for sel in LINKEDIN_SELECTORS["apply_button"]:
                    try:
                        el = page.query_selector(sel)
                        if el:
                            href = el.get_attribute("href") or ""
                            if href and "linkedin.com" not in href:
                                result["apply_mode"] = "external_ats"
                                result["external_apply_url"] = href
                            else:
                                result["apply_mode"] = "linkedin_apply"
                            break
                    except Exception:
                        continue

            # Detectar remote/híbrido no título ou localização
            title_loc = f"{result.get('title','') or ''} {result.get('location','') or ''}".lower()
            if any(w in title_loc for w in ["remote", "remoto", "anywhere"]):
                result["remote_mode"] = "remote"
            elif any(w in title_loc for w in ["hybrid", "híbrido"]):
                result["remote_mode"] = "hybrid"
            elif result.get("location"):
                result["remote_mode"] = "onsite"

            browser.close()

    except Exception as e:
        result["error"] = str(e)

    # Salvar JSON
    if save_artifacts:
        json_path = JOBS_DIR / f"job_{platform}_{ts}_{slug}.json"
        json_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
        result["artifacts"]["json"] = str(json_path)

    return result


def format_for_telegram(job: dict) -> str:
    """Formata extração de vaga para mensagem Telegram."""
    if "error" in job and not job.get("title"):
        return f"❌ Erro na extração: {job['error']}"

    apply_icon = {"easy_apply": "⚡", "external_ats": "🔗", "linkedin_apply": "🔵"}.get(
        job.get("apply_mode"), "❓"
    )

    lines = [
        f"📋 VAGA EXTRAÍDA — {job.get('platform','?').upper()}",
        f"**{job.get('title') or 'Título não extraído'}**",
        f"🏢 {job.get('company') or 'Empresa não extraída'}",
        f"📍 {job.get('location') or 'Local não extraído'} | {job.get('remote_mode','?')}",
        f"{apply_icon} Apply mode: {job.get('apply_mode','?')}",
    ]

    if job.get("external_apply_url"):
        lines.append(f"🔗 ATS: {job['external_apply_url'][:80]}")

    desc = job.get("description", "")
    if desc:
        lines.append(f"\n📝 Descrição (resumo):\n{desc[:500]}...")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Job Detail Extractor via CDP")
    parser.add_argument("--url", help="URL da vaga para extrair")
    parser.add_argument("--scan-tabs", action="store_true", help="Escanear abas abertas")
    parser.add_argument("--save-artifacts", action="store_true", default=True)
    parser.add_argument("--telegram", action="store_true", help="Formato Telegram")
    args = parser.parse_args()

    if args.url:
        result = extract_with_playwright(args.url, save_artifacts=args.save_artifacts)
        if args.telegram:
            print(format_for_telegram(result))
        else:
            print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.scan_tabs:
        # Importar recon para listar abas
        sys.path.insert(0, str(Path(__file__).parent))
        from browser_recon import run_recon
        recon = run_recon(jobs_only=True)
        for tab in recon.get("tabs", []):
            if tab["is_job_page"] and tab["url"]:
                print(f"\n--- Extraindo: {tab['title'][:60]} ---")
                result = extract_with_playwright(tab["url"], save_artifacts=True)
                if args.telegram:
                    print(format_for_telegram(result))
                else:
                    print(json.dumps({k: v for k, v in result.items() if k != "description"}, indent=2))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
