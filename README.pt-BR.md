# Cadence Career Ops 🎯

[![Status](https://img.shields.io/badge/status-operational-31d0aa?style=flat-square)](./docs/showcase/RESULTS.md)
[![Python](https://img.shields.io/badge/python-3.11+-blue?style=flat-square)](./scripts/skills/)
[![Licença: MIT](https://img.shields.io/badge/licença-MIT-yellow?style=flat-square)](./LICENSE)

> **Sistema de automação de carreira com IA** — da descoberta de vagas até o Easy Apply, geração adaptativa de CV, tracking de candidaturas e arquitetura híbrida local + VPS.

Construído sobre o framework de agentes [OpenClaw](https://openclaw.dev). Opera um browser real (Chrome via CDP) contra a UI autenticada do LinkedIn, com uma VPS persistente como "cérebro" para CRM, workflows e observabilidade.

---

## O Que É Isso

Um **pipeline completo de operações de carreira** — não um demo ou bot de spam. É um sistema em produção, construído e operado por [Sami Monteleone](https://linkedin.com/in/sami-monteleone) para resolver o problema real de gerenciar uma busca de emprego de alto sinal e alta velocidade com precisão e auditabilidade.

```
┌─────────────────────────────────────────────────────────────────┐
│                    CADENCE CAREER OPS                           │
│                                                                 │
│  Chrome Windows ←── CDP ──→ WSL/Ubuntu (Agente Cadence)        │
│        │                           │                           │
│   UI do LinkedIn               14 Scripts Python               │
│   Formulários Easy Apply       Estado JSON local               │
│   Sessão autenticada           Gate Telegram (aprovação humana)│
│                                ↕                               │
│                           VPS (Hetzner)                        │
│                           PostgreSQL CRM                        │
│                           Workflows n8n                         │
│                           Docker Swarm (14 serviços)            │
└─────────────────────────────────────────────────────────────────┘
```

### O Que Está Operacional Hoje

| Capacidade | Status | Detalhes |
|---|---|---|
| Descoberta de vagas via browser | ✅ Operacional | Busca LinkedIn via CDP real |
| Scoring 4D de vagas | ✅ Operacional | fit, stretch, strategic, value |
| LinkedIn Easy Apply | ✅ Comprovado | Preenchimento completo + salário + seleção de CV |
| Gate humano de aprovação | ✅ Operacional | Aprovação via Telegram antes de qualquer envio |
| Tracking de candidaturas | ✅ Operacional | Índice JSON + follow-up tracker |
| Geração adaptativa de CV | ✅ Operacional | YAML → PDF com branding (24 variantes geradas) |
| Dashboard HTML | ✅ Operacional | Dashboard local autocontido a partir dos state files |
| Postagem de conteúdo LinkedIn | ✅ Comprovado | Fluxo completo: tópico → imagem → copy → publicação |
| Camada persistente na VPS | ✅ Rodando | Docker Swarm com 14 serviços na Hetzner |
| CRM PostgreSQL | 🔄 Em andamento | Schema pronto, sincronização em andamento |
| Intake Gmail via n8n | 🔄 Em andamento | Arquitetura definida |

---

## Quick Start

### Pré-requisitos

- WSL2 (Ubuntu 22+) no Windows
- Python 3.11+ com ambiente virtual
- Chrome/Chromium com [CDP habilitado](./docs/guides/LINKEDIN_SETUP.md)
- [OpenClaw](https://openclaw.dev) instalado localmente

### 3 Passos

```bash
# 1. Clonar e configurar
git clone https://github.com/MontSamm-AI/cadence-career-ops.git
cd cadence-career-ops
cp system/config/openclaw.example.json ~/.openclaw/openclaw.json
# Editar com seus modelos e tokens

# 2. Instalar dependências Python
python3 -m venv .venv/jobhunter
source .venv/jobhunter/bin/activate
pip install playwright pandas jobspy
playwright install chromium

# 3. Configurar perfil e executar
cp system/templates/cv_base.example.yaml cv_base.yaml
# Editar com seus dados reais
python3 scripts/skills/linkedin_job_search.py --preset core_br
```

Guia completo: [INSTALLATION.md](./docs/guides/INSTALLATION.md)

---

## Arquitetura

O sistema usa um **modelo híbrido** — separando propositalmente as responsabilidades:

- **Local (WSL + Windows)** → executor com browser: Chrome CDP, Easy Apply, postagens no LinkedIn, revisão visual, upload de arquivos
- **VPS (Hetzner/Docker Swarm)** → cérebro persistente: CRM PostgreSQL, workflows n8n, schedulers, alertas, dashboard, memória de longo prazo

Esta separação é uma decisão arquitetural central: o LinkedIn exige uma **sessão de browser autenticada** que não pode ser replicada server-side sem proxy de auth complexo. A VPS faz o que infra persistente faz melhor.

Detalhes completos: [SYSTEM_OVERVIEW.md](./docs/architecture/SYSTEM_OVERVIEW.md)

---

## Os 14 Scripts Python

O diretório `scripts/skills/` contém o núcleo operacional:

| Script | Papel |
|---|---|
| `linkedin_easy_apply_runner.py` | Automação completa do Easy Apply (604 linhas) |
| `auto_apply_loop.py` | Orquestra a fila de candidaturas |
| `auto_apply_lib.py` | Utilitários compartilhados, perfil, lógica de compensação |
| `linkedin_job_search.py` | Descoberta de vagas via CDP do LinkedIn |
| `job_detail_extractor.py` | Extração estruturada de detalhes de vagas |
| `browser_recon.py` | Reconhecimento de abas do Chrome |
| `browser_probe.py` | Probe de browser de uso geral |
| `application_guard.py` | Gate de segurança pré-candidatura |
| `tab_hygiene.py` | Gerencia abas abertas pós-candidatura |
| `render_applications_dashboard.py` | Renderiza dashboard HTML a partir do estado |
| `telegram_notifier.py` | Envia alertas Telegram formatados |
| `cpqd_assisted_probe.py` | Probe específico para ATS (CPQD) |
| `cpqd_fill_prepare.py` | Preparação de formulário específico (CPQD) |
| `hubxp_probe.py` / `hubxp_probe_wait.py` | Probes específicos (HubXP) |

---

## Motor de CV

O sistema de CV adaptativo converte um perfil YAML estruturado em PDFs com branding:

```
cv_base.yaml  →  cv_branded_generator.py  →  CV_Sami_[preset]_[cargo]_[data].pdf
```

Presets: `clt-ptbr`, `master-en`, `master-ptbr`, `upwork-en`, `automation-ptbr`, `cpqd`

24 variantes de CV foram geradas para diferentes cargos e mercados.

Detalhes: [CV_SYSTEM.md](./docs/guides/CV_SYSTEM.md)

---

## Segurança e Ética

Este sistema é construído com segurança no núcleo:

- **Gate humano**: toda candidatura requer aprovação explícita via Telegram antes do envio
- **Rate limiting**: máximo 5 candidaturas/dia via automação, delays de 30–120s entre ações
- **Threshold de score**: score mínimo de 65/100 para qualquer candidatura ser enfileirada
- **Claims proibidos**: verificações em runtime previnem afirmações falsas
- **Horário restrito**: sistema respeita a janela 07h–23h no horário de Brasília
- **Keywords bloqueadas**: QA automation, test automation, RPA e cargos não relacionados são filtrados automaticamente

---

## Resultados

- **40+ candidaturas** rastreadas em múltiplos ATS e LinkedIn
- **24 variantes de CV** geradas em 6 presets de perfil
- **1 post no LinkedIn** publicado de ponta a ponta
- **0 claims falsos** submetidos — toda resposta é validada contra `cv_base.yaml`
- **Sistema de scoring 4D** filtrando centenas de vagas descobertas para uma fila de alto sinal

Detalhes: [RESULTS.md](./docs/showcase/RESULTS.md)

---

## Construído Por

**Sami Monteleone** — Engenheira de automação de IA aplicada, construtora de agentes, arquiteta de workflows.

- 🔗 [LinkedIn](https://linkedin.com/in/sami-monteleone)
- 📧 samisaulomonteleone@gmail.com
- 🌍 São Paulo, Brasil | Aberta a posições remotas internacionais

> Este projeto é um artefato de portfólio vivo — demonstra engenharia de IA aplicada, automação de browser, orquestração de agentes, infraestrutura híbrida e Python em nível de produção, tudo em um contexto operacional real.

---

## Licença

MIT — veja [LICENSE](./LICENSE).
