#!/usr/bin/env python3
"""
cv_branded_generator.py — Gerador de CV Branded em PDF
Sami Monteleone Career Pipeline · v1.4 · 2026-04-09

Pipeline: cv_base.yaml → Jinja2 HTML template → Playwright PDF (Chrome headless)

Dependências (já no venv jobhunter):
    pip install playwright jinja2 pyyaml
    playwright install chromium  # se necessário

Uso (rodar a partir do WSL com venv ativado):
    python cv_branded_generator.py --preset clt-ptbr --job "AI Automation Engineer"
    python cv_branded_generator.py --preset upwork-en --job "n8n Specialist" --company "Acme Corp"
    python cv_branded_generator.py --preset clt-ptbr --job "Especialista IA" --output-dir ./output/pdf/
    python cv_branded_generator.py --list-presets
    python cv_branded_generator.py --html-only --preset clt-ptbr --job "Test"
"""

import argparse
import os
import sys
import re
from pathlib import Path
from datetime import datetime

import yaml

# ─────────────────────────────────────────────
# CAMINHOS BASE
# ─────────────────────────────────────────────
SCRIPT_DIR   = Path(__file__).parent.resolve()
YAML_PATH    = SCRIPT_DIR / "cv_base.yaml"
TEMPLATES_DIR = SCRIPT_DIR / "cv_templates"
OUTPUT_BASE  = SCRIPT_DIR / "output" / "pdf"

# ─────────────────────────────────────────────
# PRESETS — configuração por tipo de vaga
# ─────────────────────────────────────────────
PRESETS = {
    "clt-ptbr": {
        "lang": "pt-br",
        "template": "cv_branded.html.j2",
        "summary_variant": "ptbr",
        "include_gtm": False,
        "max_projects": 3,
        "max_exp": None,        # todas as experiências
        "max_skills_per_cat": 6,  # limita pills por categoria no sidebar
        "stack_cats_show": ["orchestration_agents", "channels_integrations", "infrastructure", "development"],
        "highlight_skills": ["n8n", "OpenAI API (GPT-4o / GPT-4o-mini)",
                              "Anthropic Claude API", "Docker Swarm",
                              "Evolution API (WhatsApp Business)",
                              "PostgreSQL", "RAG — Retrieval-Augmented Generation", "Python"],
        "bullets_preset": "clt-ptbr",
        "description": "CV formal PT-BR para vagas CLT — foco em projetos em produção e stack técnica"
    },
    "pj-ptbr": {
        "lang": "pt-br",
        "template": "cv_branded.html.j2",
        "summary_variant": "ptbr",
        "include_gtm": True,
        "max_projects": 3,
        "max_exp": None,
        "max_skills_per_cat": 6,
        "stack_cats_show": ["orchestration_agents", "channels_integrations", "infrastructure", "development"],
        "highlight_skills": ["n8n", "OpenAI API (GPT-4o / GPT-4o-mini)", "Docker Swarm", "Playwright",
                              "Evolution API (WhatsApp Business)", "PostgreSQL"],
        "bullets_preset": "pj-ptbr",
        "description": "CV PT-BR para PJ/freelancer — autonomia e resultado em destaque"
    },
    "upwork-en": {
        "lang": "en",
        "template": "cv_branded.html.j2",
        "summary_variant": "en",
        "include_gtm": False,
        "max_projects": 4,
        "max_exp": 2,           # foco nas 2 últimas experiências
        "max_skills_per_cat": 7,
        "stack_cats_show": ["orchestration_agents", "channels_integrations", "infrastructure", "development"],
        "highlight_skills": ["n8n", "OpenAI API (GPT-4o / GPT-4o-mini)", "Python", "Playwright",
                              "Docker Swarm", "LangChain", "PostgreSQL",
                              "Model Context Protocol (MCP)"],
        "bullets_preset": "upwork-en",
        "description": "CV EN para Upwork/Toptal — stack e portfolio em destaque"
    },
    "consultivo-ptbr": {
        "lang": "pt-br",
        "template": "cv_branded.html.j2",
        "summary_variant": "consultive",
        "include_gtm": True,
        "max_projects": 3,
        "max_exp": None,
        "max_skills_per_cat": 5,
        "stack_cats_show": ["orchestration_agents", "channels_integrations", "infrastructure"],
        "highlight_skills": ["n8n", "OpenAI API (GPT-4o / GPT-4o-mini)", "Model Context Protocol (MCP)",
                              "Evolution API (WhatsApp Business)", "SPIN Selling"],
        "bullets_preset": "consultivo-ptbr",
        "description": "CV consultivo PT-BR — GTM + impacto de negócio em destaque"
    },
    "linkedin-ptbr": {
        "lang": "pt-br",
        "template": "cv_branded.html.j2",
        "summary_variant": "ptbr",
        "include_gtm": False,
        "max_projects": 2,
        "max_exp": 2,
        "max_skills_per_cat": 5,
        "stack_cats_show": ["orchestration_agents", "channels_integrations", "infrastructure"],
        "highlight_skills": ["n8n", "OpenAI API (GPT-4o / GPT-4o-mini)", "Docker Swarm",
                              "Evolution API (WhatsApp Business)", "Python"],
        "bullets_preset": "linkedin-ptbr",
        "description": "CV ultra-resumido para LinkedIn Easy Apply — máximo impacto em 1 página"
    },
    "cpqd": {
        "lang": "pt-br",
        "template": "cv_branded.html.j2",
        "summary_variant": "ptbr",
        "include_gtm": False,
        "max_projects": 3,
        "max_exp": None,
        "max_skills_per_cat": 7,
        "stack_cats_show": ["orchestration_agents", "channels_integrations", "infrastructure", "development"],
        "highlight_skills": ["Python", "LangChain", "RAG — Retrieval-Augmented Generation",
                              "OpenAI API (GPT-4o / GPT-4o-mini)", "Anthropic Claude API",
                              "Docker Swarm", "PostgreSQL", "Model Context Protocol (MCP)"],
        "bullets_preset": "cpqd",  # mostra bullets com include_in_cv: cpqd
        "description": "CV PT-BR para vagas de pesquisa/CPQD — raciocínio sistêmico + IA em produção + trajetória"
    },

    # ── AUTOMAÇÃO / ENGENHARIA (vagas industriais, transformação digital) ────
    "automation-ptbr": {
        "lang": "pt-br",
        "template": "cv_branded.html.j2",
        "summary_variant": "automation_eng",
        "include_gtm": False,
        "max_projects": 3,
        "max_exp": None,
        "max_skills_per_cat": 6,
        "stack_cats_show": ["orchestration_agents", "channels_integrations", "infrastructure", "development"],
        "highlight_skills": ["n8n", "Python", "PostgreSQL", "Docker Swarm", "Playwright",
                              "OpenAI API (GPT-4o / GPT-4o-mini)", "Evolution API (WhatsApp Business)"],
        "bullets_preset": "automation-ptbr",
        "max_bullets_per_exp": [3, 2, 2],   # atual: 3, mercedes: 2 (inclui vba+doc), rhodia: 2 (cogeneracao+indicadores)
        "max_metrics": 3,
        "max_edu": 3,   # inclui UNICAMP (automação industrial)
        "compact": True,
        "description": "CV para vagas de automação/engenharia/transformação digital — framing de Engenheiro, não AI-first"
    },

    # ── MASTER BASE CVs v1 — com projetos (2 páginas) ────────────────────────
    "master-ptbr": {
        "lang": "pt-br",
        "template": "cv_branded.html.j2",
        "summary_variant": "ptbr",
        "include_gtm": False,
        "max_projects": 3,
        "max_exp": None,
        "max_skills_per_cat": 5,
        "stack_cats_show": ["orchestration_agents", "channels_integrations", "infrastructure", "development"],
        "highlight_skills": ["n8n", "OpenAI API (GPT-4o / GPT-4o-mini)", "Anthropic Claude API",
                              "Evolution API (WhatsApp Business)", "Docker Swarm",
                              "PostgreSQL", "Python", "Playwright"],
        "bullets_preset": "master-ptbr",
        "max_bullets_per_exp": [3, 2, 1],
        "max_metrics": 3,
        "max_edu": 2,
        "compact": True,
        "description": "CV master PT-BR com projetos — 2 páginas"
    },
    "master-en": {
        "lang": "en",
        "template": "cv_branded.html.j2",
        "summary_variant": "en",
        "include_gtm": False,
        "max_projects": 3,
        "max_exp": None,
        "max_skills_per_cat": 5,
        "stack_cats_show": ["orchestration_agents", "channels_integrations", "infrastructure", "development"],
        "highlight_skills": ["n8n", "OpenAI API (GPT-4o / GPT-4o-mini)", "Anthropic Claude API",
                              "Evolution API (WhatsApp Business)", "Docker Swarm",
                              "PostgreSQL", "Python", "Playwright"],
        "bullets_preset": "master-en",
        "max_bullets_per_exp": [3, 2, 1],
        "max_metrics": 3,
        "max_edu": 2,
        "compact": True,
        "description": "CV master EN com projetos — 2 páginas"
    },

    # ── MASTER BASE CVs v2 — sem projetos (alvo 1 página) ────────────────────
    "master-ptbr-1p": {
        "lang": "pt-br",
        "template": "cv_branded.html.j2",
        "summary_variant": "ptbr",
        "include_gtm": False,
        "max_projects": 0,
        "no_projects": True,
        "max_exp": None,
        "max_skills_per_cat": 4,
        "stack_cats_show": ["orchestration_agents", "channels_integrations", "infrastructure", "development"],
        "highlight_skills": ["n8n", "OpenAI API (GPT-4o / GPT-4o-mini)", "Anthropic Claude API",
                              "Evolution API (WhatsApp Business)", "Docker Swarm",
                              "PostgreSQL", "Python", "Playwright"],
        "bullets_preset": "master-ptbr",
        "max_bullets_per_exp": [3, 2, 1],
        "max_metrics": 3,
        "max_edu": 2,
        "compact": True,
        "description": "CV master PT-BR 1 PÁGINA — sem projetos, com Rhodia resumida"
    },
    "master-en-1p": {
        "lang": "en",
        "template": "cv_branded.html.j2",
        "summary_variant": "en",
        "include_gtm": False,
        "max_projects": 0,
        "no_projects": True,
        "max_exp": None,
        "max_skills_per_cat": 5,
        "stack_cats_show": ["orchestration_agents", "channels_integrations", "infrastructure", "development"],
        "highlight_skills": ["n8n", "OpenAI API (GPT-4o / GPT-4o-mini)", "Anthropic Claude API",
                              "Evolution API (WhatsApp Business)", "Docker Swarm",
                              "PostgreSQL", "Python", "Playwright"],
        "bullets_preset": "master-en",
        "max_bullets_per_exp": [3, 2, 1],
        "max_metrics": 3,
        "max_edu": 2,
        "compact": True,
        "description": "CV master EN 1 PAGE — without projects section"
    }
}


# ─────────────────────────────────────────────
# FILTROS JINJA2 CUSTOMIZADOS
# ─────────────────────────────────────────────
def format_date(value):
    """Converte 'YYYY-MM' ou 'YYYY' para 'Mês/YYYY'."""
    if not value:
        return ""
    value = str(value)
    if re.match(r"^\d{4}-\d{2}$", value):
        try:
            from datetime import datetime
            dt = datetime.strptime(value, "%Y-%m")
            months_pt = ["Jan","Fev","Mar","Abr","Mai","Jun",
                         "Jul","Ago","Set","Out","Nov","Dez"]
            return f"{months_pt[dt.month-1]}/{dt.year}"
        except Exception:
            return value
    elif re.match(r"^\d{4}$", value):
        return value
    return value


def slugify(text):
    """Gera slug para nome de arquivo."""
    text = str(text).lower()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")


# ─────────────────────────────────────────────
# CARREGAR CV BASE
# ─────────────────────────────────────────────
def load_cv_base(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# ─────────────────────────────────────────────
# PREPARAR CONTEXTO PARA O TEMPLATE
# ─────────────────────────────────────────────
def prepare_context(cv: dict, preset_cfg: dict, preset_name: str = "", job_title: str = "", company: str = "") -> dict:
    lang = preset_cfg["lang"]
    max_exp = preset_cfg.get("max_exp")
    max_proj = preset_cfg.get("max_projects", 10)
    include_gtm = preset_cfg.get("include_gtm", False)
    highlight_skills = preset_cfg.get("highlight_skills", [])
    summary_variant = preset_cfg.get("summary_variant", "ptbr")
    max_skills_per_cat = preset_cfg.get("max_skills_per_cat", 99)
    stack_cats_show = preset_cfg.get("stack_cats_show", None)  # None = all except excluded
    bullets_preset = preset_cfg.get("bullets_preset", preset_name)
    max_bullets_per_exp = preset_cfg.get("max_bullets_per_exp", None)  # list of ints or None
    max_metrics = preset_cfg.get("max_metrics", None)
    max_edu = preset_cfg.get("max_edu", None)
    compact = preset_cfg.get("compact", False)
    no_projects = preset_cfg.get("no_projects", False)

    # --- Experiências (limitar se necessário; filtrar bullets por include_in_cv) ---
    experience_raw = cv.get("experience", [])
    if max_exp:
        experience_raw = experience_raw[:max_exp]

    experience = []
    for exp_idx, exp in enumerate(experience_raw):
        exp_copy = dict(exp)
        # Filtrar bullets: incluir apenas se include_in_cv não está definido,
        # ou se o preset atual está na lista
        filtered_bullets = []
        for bullet in exp.get("bullets", []):
            inc = bullet.get("include_in_cv")
            if inc is None:
                filtered_bullets.append(bullet)
            elif isinstance(inc, list) and bullets_preset in inc:
                filtered_bullets.append(bullet)
            elif isinstance(inc, bool) and inc:
                filtered_bullets.append(bullet)
        # Aplicar limite por experiência (max_bullets_per_exp)
        if max_bullets_per_exp is not None:
            limit = max_bullets_per_exp[exp_idx] if exp_idx < len(max_bullets_per_exp) else max_bullets_per_exp[-1]
            filtered_bullets = filtered_bullets[:limit]
        exp_copy["bullets"] = filtered_bullets
        experience.append(exp_copy)

    # --- Projetos (apenas highlights até max_projects) ---
    all_projects = cv.get("projects", [])
    # Em modo compact: usar description_short quando disponível
    if compact:
        processed_projects = []
        for p in all_projects:
            p_copy = dict(p)
            if lang == "en":
                short = p.get("description_short_en")
                if short:
                    p_copy["description_en"] = short
            else:
                short = p.get("description_short_ptbr")
                if short:
                    p_copy["description_ptbr"] = short
            processed_projects.append(p_copy)
        all_projects = processed_projects
    highlight_projects = [p for p in all_projects if p.get("highlight", False)]
    projects = highlight_projects[:max_proj]
    if len(projects) < max_proj:
        non_highlight = [p for p in all_projects if not p.get("highlight", False)]
        projects += non_highlight[:max_proj - len(projects)]

    # --- Stack (marcar highlights; filtrar categorias; limitar itens) ---
    stack = cv.get("stack", {})
    stack_prepared = {}
    excluded_always = ["engineering_foundation"]
    if not include_gtm:
        excluded_always.append("gtm_business")

    for cat_key, cat_data in stack.items():
        if cat_key in excluded_always:
            continue
        if stack_cats_show is not None and cat_key not in stack_cats_show:
            continue
        entries = []
        for item in cat_data.get("items", []):
            item_copy = dict(item)
            item_copy["is_highlight"] = item["name"] in highlight_skills
            entries.append(item_copy)
        # Highlight first, then rest — respect max_skills_per_cat
        highlights = [e for e in entries if e["is_highlight"]]
        others = [e for e in entries if not e["is_highlight"]]
        limited = (highlights + others)[:max_skills_per_cat]
        stack_prepared[cat_key] = {
            "label": cat_data.get("label", cat_key),
            "label_en": cat_data.get("label_en", cat_data.get("label", cat_key)),
            "entries": limited
        }

    # --- Sumário ---
    summary_raw = cv.get("summary", {})
    if summary_variant == "consultive":
        summary_text = summary_raw.get("consultive", summary_raw.get("ptbr", ""))
    elif summary_variant == "automation_eng":
        summary_text = summary_raw.get("automation_eng", summary_raw.get("ptbr", ""))
    elif lang == "en":
        summary_text = summary_raw.get("en", summary_raw.get("ptbr", ""))
    else:
        summary_text = summary_raw.get("ptbr", "")

    # --- Métricas (limitar quantidade se compact) ---
    all_metrics = cv.get("metrics", [])
    verified_metrics = [m for m in all_metrics if m.get("verified", True)]
    if max_metrics is not None:
        verified_metrics = verified_metrics[:max_metrics]

    # --- Educação (limitar se compact) ---
    education = cv.get("education", [])
    if max_edu is not None:
        education = education[:max_edu]

    return {
        "meta": cv.get("meta", {}),
        "identity": cv.get("identity", {}),
        "summary": {"text": summary_text.strip(), **summary_raw},
        "stack": stack_prepared,
        "experience": experience,
        "projects": projects,
        "education": education,
        "certifications": cv.get("certifications", []),
        "languages": cv.get("languages", []),
        "metrics": verified_metrics,
        "positioning": cv.get("positioning", {}),
        "lang": lang,
        "preset": preset_name,
        "compact": compact,
        "no_projects": no_projects,
        "job_title": job_title,
        "company": company,
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }


# ─────────────────────────────────────────────
# GERAR HTML
# ─────────────────────────────────────────────
def render_html(context: dict, template_name: str) -> str:
    try:
        from jinja2 import Environment, FileSystemLoader, select_autoescape
    except ImportError:
        print("[ERRO] Jinja2 não instalado. Execute: pip install jinja2")
        sys.exit(1)

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["format_date"] = format_date
    env.filters["truncate"] = lambda s, l=80, kill=True, end="...": (s[:l] + end if len(s) > l and kill else s)

    template = env.get_template(template_name)
    return template.render(**context)


# ─────────────────────────────────────────────
# GERAR PDF via Playwright (Chrome headless)
# ─────────────────────────────────────────────
def render_pdf(html_content: str, output_path: Path) -> bool:
    """
    Usa Playwright + Chromium headless para renderizar HTML → PDF.
    Produce output fiel ao design CSS, incluindo gradientes e fontes web.
    """
    # Salvar HTML temporário
    import tempfile
    tmp_html = Path(tempfile.mktemp(suffix=".html"))
    tmp_html.write_text(html_content, encoding="utf-8")

    # Tentar Playwright primeiro (melhor qualidade)
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(f"file://{tmp_html}", wait_until="networkidle")
            # Aguardar fontes carregarem
            page.wait_for_timeout(1500)
            page.pdf(
                path=str(output_path),
                format="A4",
                margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
                print_background=True,
                prefer_css_page_size=True,
            )
            browser.close()
        tmp_html.unlink(missing_ok=True)
        return True

    except ImportError:
        print("[AVISO] Playwright não instalado.")
        print("        Execute: pip install playwright && playwright install chromium")
    except Exception as e:
        print(f"[AVISO] Playwright falhou: {e}")
        print("        Tentando fallback xhtml2pdf...")

    # Fallback: xhtml2pdf (pure Python, menor qualidade mas funciona)
    try:
        from xhtml2pdf import pisa
        with open(output_path, "wb") as out_f:
            result = pisa.CreatePDF(html_content, dest=out_f,
                                    encoding="utf-8")
        if not result.err:
            tmp_html.unlink(missing_ok=True)
            return True
        else:
            print(f"[ERRO xhtml2pdf] Erros na conversão: {result.err}")
    except ImportError:
        print("[AVISO] xhtml2pdf não disponível.")

    # Último recurso: salvar HTML
    html_path = output_path.with_suffix(".html")
    html_path.write_text(html_content, encoding="utf-8")
    print(f"[HTML]  Salvo como HTML: {html_path}")
    print(f"        Para converter manualmente: abra no Chrome e use Ctrl+P → Salvar como PDF")
    tmp_html.unlink(missing_ok=True)
    return False


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Gera CV branded PDF a partir de cv_base.yaml",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python cv_branded_generator.py --preset clt-ptbr --job "AI Automation Engineer"
  python cv_branded_generator.py --preset upwork-en --job "n8n Specialist" --company "Acme"
  python cv_branded_generator.py --list-presets
        """
    )
    parser.add_argument("--preset", "-p", default="clt-ptbr",
                        choices=list(PRESETS.keys()),
                        help="Preset de formatação")
    parser.add_argument("--job", "-j", default="",
                        help="Cargo alvo (aparece no CV)")
    parser.add_argument("--company", "-c", default="",
                        help="Empresa alvo (opcional)")
    parser.add_argument("--output-dir", "-o", default=None,
                        help="Diretório de saída (default: ./output/pdf/)")
    parser.add_argument("--html-only", action="store_true",
                        help="Gerar apenas HTML (sem PDF)")
    parser.add_argument("--list-presets", action="store_true",
                        help="Lista presets disponíveis")
    parser.add_argument("--cv-path", default=None,
                        help="Caminho alternativo para cv_base.yaml")

    args = parser.parse_args()

    if args.list_presets:
        print("\n=== PRESETS DISPONÍVEIS ===\n")
        for name, cfg in PRESETS.items():
            print(f"  {name:<20} {cfg['description']}")
        print()
        return

    # Caminhos
    cv_path   = Path(args.cv_path) if args.cv_path else YAML_PATH
    out_dir   = Path(args.output_dir) if args.output_dir else OUTPUT_BASE
    out_dir.mkdir(parents=True, exist_ok=True)

    # Verificar arquivos
    if not cv_path.exists():
        print(f"[ERRO] cv_base.yaml não encontrado em: {cv_path}")
        sys.exit(1)

    preset_cfg = PRESETS[args.preset]
    template_name = preset_cfg["template"]

    if not (TEMPLATES_DIR / template_name).exists():
        print(f"[ERRO] Template não encontrado: {TEMPLATES_DIR / template_name}")
        sys.exit(1)

    # Carregar dados
    print(f"[LOAD]  cv_base.yaml carregado")
    cv = load_cv_base(cv_path)

    # Preparar contexto
    context = prepare_context(cv, preset_cfg, args.preset, args.job, args.company)
    print(f"[OK]    Contexto preparado — preset: {args.preset} | lang: {preset_cfg['lang']}")

    # Gerar HTML
    print(f"[HTML]  Renderizando template {template_name}...")
    html = render_html(context, template_name)

    # Nome do arquivo de saída
    job_slug   = slugify(args.job) if args.job else "cv"
    date_str   = datetime.now().strftime("%Y%m%d")
    filename   = f"CV_SamiMonteleone_{args.preset}_{job_slug}_{date_str}"

    if args.html_only:
        html_path = out_dir / f"{filename}.html"
        html_path.write_text(html, encoding="utf-8")
        print(f"[HTML]  {html_path}")
        return

    # Gerar PDF
    pdf_path = out_dir / f"{filename}.pdf"
    print(f"[PDF]   Gerando {pdf_path.name}...")
    success = render_pdf(html, pdf_path)

    if success:
        size_kb = pdf_path.stat().st_size // 1024
        print(f"\n[OK]  CV gerado com sucesso!")
        print(f"      Arquivo : {pdf_path}")
        print(f"      Tamanho : {size_kb} KB")
        print(f"      Preset  : {args.preset}")
        print(f"      Cargo   : {args.job or '(genérico)'}")
        print(f"      Empresa : {args.company or '(não especificada)'}")
    else:
        print(f"\n[AVISO] PDF não gerado — verifique instalação do WeasyPrint.")
        print(f"        HTML intermediário salvo para revisão.")


if __name__ == "__main__":
    main()
