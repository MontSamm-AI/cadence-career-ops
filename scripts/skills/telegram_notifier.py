#!/usr/bin/env python3
"""
telegram_notifier.py — Envio de notificações para Telegram
Cadence Profissional · Onda 1 · v1.0 · 2026-04-06

Envia mensagens formatadas ao chat do Sami via bot Telegram.
Token do bot: configurado em TELEGRAM_BOT_TOKEN env var ou config.json

Uso:
    python3 telegram_notifier.py --message "Texto"
    python3 telegram_notifier.py --type vagas --data vagas.json
    python3 telegram_notifier.py --test    # testa conexão

Config:
    Definir TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID como variáveis de ambiente
    OU criar /home/monts/.openclaw/workspace-linkedin/config.json com:
    {
        "telegram_bot_token": "TOKEN_AQUI",
        "telegram_chat_id": "CHAT_ID_AQUI"
    }
"""

import json
import os
import sys
import argparse
import urllib.request
import urllib.parse
from datetime import datetime
from pathlib import Path

WORKSPACE = Path(__file__).parent.parent
CONFIG_PATH = WORKSPACE / "config.json"
CONFIG_LOCAL_PATH = WORKSPACE / "config.local.json"
ENV_LOCAL_PATH = WORKSPACE / ".env.local"


def _load_env_local():
    if not ENV_LOCAL_PATH.exists():
        return
    try:
        for line in ENV_LOCAL_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith('#') or '=' not in line:
                continue
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and value and not os.environ.get(key):
                os.environ[key] = value
    except Exception:
        pass


def load_config() -> dict:
    """Carrega configuração de env, .env.local, config.local.json e config.json não sensível."""
    _load_env_local()
    config = {
        "bot_token": os.environ.get("TELEGRAM_BOT_TOKEN", ""),
        "chat_id": os.environ.get("TELEGRAM_CHAT_ID", ""),
    }
    if CONFIG_LOCAL_PATH.exists():
        try:
            file_config = json.loads(CONFIG_LOCAL_PATH.read_text(encoding="utf-8"))
            config["bot_token"] = file_config.get("telegram_bot_token", config["bot_token"])
            config["chat_id"] = file_config.get("telegram_chat_id", config["chat_id"])
        except Exception:
            pass
    if CONFIG_PATH.exists():
        try:
            file_config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            config["chat_id"] = file_config.get("telegram", {}).get("chat_id", config["chat_id"])
        except Exception:
            pass
    return config


def send_message(text: str, parse_mode: str = "Markdown") -> dict:
    """Envia mensagem via Telegram Bot API."""
    config = load_config()

    if not config["bot_token"] or not config["chat_id"]:
        return {
            "ok": False,
            "error": "TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID não configurados.\n"
                     "Configure em config.json ou variáveis de ambiente.\n"
                     f"Config path: {CONFIG_PATH}"
        }

    url = f"https://api.telegram.org/bot{config['bot_token']}/sendMessage"
    payload = json.dumps({
        "chat_id": config["chat_id"],
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True,
    }).encode("utf-8")

    try:
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return {"ok": False, "error": f"HTTP {e.code}: {e.read().decode()}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def format_vagas(data: list) -> str:
    """Formata lista de vagas para Telegram."""
    ts = datetime.now().strftime("%d/%m %H:%M")
    lines = [f"🎯 *TOP VAGAS — {ts}*", ""]
    for i, vaga in enumerate(data[:5], 1):
        score = vaga.get("match_score", 0)
        icon = "🟢" if score >= 75 else ("🟡" if score >= 60 else "🔴")
        lines.append(f"{i}. {icon} *[{score}/100]* {vaga.get('title','?')}")
        lines.append(f"   🏢 {vaga.get('company','?')} | {vaga.get('location','?')}")
        url = vaga.get('job_url','')
        if url:
            lines.append(f"   🔗 {url[:60]}")
        matched = vaga.get("skills_matched","")
        if matched:
            lines.append(f"   ✅ {str(matched)[:80]}")
        lines.append("")

    total = len(data)
    gte70 = len([v for v in data if v.get("match_score",0) >= 70])
    lines.append(f"📊 Total: {total} | Score≥70: {gte70}")
    lines.append("\nResponda `/analisar [ID]` para análise completa")
    return "\n".join(lines)


def format_application_request(job: dict, cv_preset: str, score: int) -> str:
    """Formata pedido de aprovação de candidatura."""
    return (
        f"📋 *REVISÃO DE CANDIDATURA*\n\n"
        f"*{job.get('title','?')}*\n"
        f"🏢 {job.get('company','?')}\n"
        f"📍 {job.get('location','?')}\n"
        f"⚡ Apply mode: {job.get('apply_mode','?')}\n"
        f"📊 Score: {score}/100\n"
        f"📄 CV: preset `{cv_preset}`\n\n"
        f"_[Screenshot do formulário enviado em seguida]_\n\n"
        f"✅ `/confirmar {job.get('id','')}` — ENVIAR\n"
        f"❌ `/cancelar {job.get('id','')}` — DESCARTAR"
    )


def format_health_check(results: dict) -> str:
    """Formata resultado de health check."""
    def icon(ok): return "✅" if ok else "❌"
    lines = [
        f"🏥 *HEALTH CHECK — {datetime.now().strftime('%d/%m %H:%M')}*",
        "",
        f"{icon(results.get('cdp'))} Chrome CDP (127.0.0.1:9222)",
        f"{icon(results.get('venv'))} Python venv jobhunter",
        f"{icon(results.get('vps'))} VPS montsam.site",
        f"{icon(results.get('n8n'))} n8n.montsam.site",
        f"{icon(results.get('linkedin'))} LinkedIn logado",
    ]
    all_ok = all(results.values())
    lines.append(f"\n{'🟢 Sistema OK — pronto para operar' if all_ok else '🔴 Atenção: há falhas'}")
    return "\n".join(lines)


def setup_config(bot_token: str, chat_id: str):
    """Salva configuração sensível em config.local.json (ignorado pelo git)."""
    existing = {}
    if CONFIG_LOCAL_PATH.exists():
        try:
            existing = json.loads(CONFIG_LOCAL_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    existing["telegram_bot_token"] = bot_token
    existing["telegram_chat_id"] = chat_id
    CONFIG_LOCAL_PATH.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"✅ Configuração sensível salva em {CONFIG_LOCAL_PATH}")


def main():
    parser = argparse.ArgumentParser(description="Telegram Notifier — Cadence Profissional")
    parser.add_argument("--message", "-m", help="Mensagem a enviar")
    parser.add_argument("--test", action="store_true", help="Testar conexão")
    parser.add_argument("--setup", action="store_true", help="Configurar bot token")
    parser.add_argument("--bot-token", help="Token do bot (para --setup)")
    parser.add_argument("--chat-id", help="Chat ID (para --setup)")
    args = parser.parse_args()

    if args.setup:
        if not args.bot_token or not args.chat_id:
            print("Use: --setup --bot-token TOKEN --chat-id CHAT_ID")
            sys.exit(1)
        setup_config(args.bot_token, args.chat_id)
        return

    if args.test:
        ts = datetime.now().strftime("%d/%m/%Y %H:%M")
        result = send_message(f"🤖 *Cadence Profissional* — Conexão Telegram validada\n_{ts}_")
        if result.get("ok"):
            print("✅ Mensagem enviada com sucesso")
        else:
            print(f"❌ Falha: {result.get('error', result)}")
        return

    if args.message:
        result = send_message(args.message)
        if result.get("ok"):
            print("✅ Enviado")
        else:
            print(f"❌ {result.get('error', result)}")
        return

    parser.print_help()


if __name__ == "__main__":
    main()
