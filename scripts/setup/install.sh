#!/usr/bin/env bash
# =============================================================================
# Cadence Career Ops — Full Installation Script (WSL/Ubuntu)
# =============================================================================
# Usage: bash install.sh
# Tested on: Ubuntu 22.04 LTS (WSL2)
# =============================================================================

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
VENV_DIR="$REPO_DIR/.venv/jobhunter"
LOG_FILE="/tmp/cadence_install_$(date +%Y%m%d_%H%M%S).log"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log()   { echo -e "${GREEN}[INSTALL]${NC} $*" | tee -a "$LOG_FILE"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}   $*" | tee -a "$LOG_FILE"; }
error() { echo -e "${RED}[ERROR]${NC}  $*" | tee -a "$LOG_FILE"; exit 1; }

log "=== Cadence Career Ops — Installation ==="
log "Repo: $REPO_DIR"
log "Log:  $LOG_FILE"
echo ""

# --- System packages ---
log "Installing system packages..."
sudo apt-get update -qq
sudo apt-get install -y -qq python3 python3-pip python3-venv curl git jq sqlite3 2>>"$LOG_FILE"
log "System packages OK"

# --- Python virtual environment ---
log "Creating Python venv at $VENV_DIR..."
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"
pip install --upgrade pip --quiet

log "Installing Python dependencies..."
pip install --quiet \
    playwright \
    pandas \
    jobspy \
    requests \
    python-telegram-bot \
    pyyaml \
    jinja2 \
    weasyprint \
    psycopg2-binary \
    python-dotenv

log "Installing Playwright browsers..."
playwright install chromium 2>>"$LOG_FILE"
log "Python environment OK"

# --- OpenClaw ---
log "Checking OpenClaw installation..."
if [ -d "$HOME/.openclaw" ]; then
    warn "~/.openclaw already exists. Skipping OpenClaw installation."
    warn "To reinstall: rm -rf ~/.openclaw && bash install.sh"
else
    log "Installing OpenClaw..."
    if ! command -v node &>/dev/null; then
        log "Installing Node.js..."
        curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - 2>>"$LOG_FILE"
        sudo apt-get install -y nodejs 2>>"$LOG_FILE"
    fi
    log "Node.js version: $(node --version)"
    
    OPENCLAW_DIR="$HOME/openclaw-framework"
    git clone https://github.com/openclaw/openclaw "$OPENCLAW_DIR" 2>>"$LOG_FILE"
    cd "$OPENCLAW_DIR"
    npm install 2>>"$LOG_FILE"
    
    log "Configuring OpenClaw..."
    mkdir -p "$HOME/.openclaw/workspace-linkedin/memory"
    mkdir -p "$HOME/.openclaw/workspace-linkedin/state"
    mkdir -p "$HOME/.openclaw/workspace-linkedin/docs"
    mkdir -p "$HOME/.openclaw/workspace-linkedin/skills"
    mkdir -p "$HOME/.openclaw/workspace-linkedin/artifacts"
    
    cp "$REPO_DIR/system/config/openclaw.example.json" "$HOME/.openclaw/openclaw.json"
    warn "IMPORTANT: Edit ~/.openclaw/openclaw.json with your credentials before running!"
fi
log "OpenClaw OK"

# --- Workspace setup ---
log "Setting up skills workspace..."
SKILLS_TARGET="$HOME/.openclaw/workspace-linkedin/skills"
for script in "$REPO_DIR/scripts/skills/"*.py; do
    cp "$script" "$SKILLS_TARGET/"
done
log "Copied $(ls "$SKILLS_TARGET"/*.py | wc -l) skills to $SKILLS_TARGET"

# --- State files initialization ---
STATE_DIR="$HOME/.openclaw/workspace-linkedin/state"
if [ ! -f "$STATE_DIR/applications_index.json" ]; then
    echo '{"total":0,"applied":[],"pipeline":[],"hold":[]}' > "$STATE_DIR/applications_index.json"
fi
if [ ! -f "$STATE_DIR/follow_up_tracker.json" ]; then
    echo '[]' > "$STATE_DIR/follow_up_tracker.json"
fi
if [ ! -f "$STATE_DIR/auto_apply_queue.json" ]; then
    echo '[]' > "$STATE_DIR/auto_apply_queue.json"
fi
if [ ! -f "$STATE_DIR/linkedin_posts_index.json" ]; then
    echo '{"posts":[]}' > "$STATE_DIR/linkedin_posts_index.json"
fi
log "State files initialized"

# --- CV engine ---
log "Setting up CV engine..."
CV_DIR="$HOME/.openclaw/workspace-linkedin/cv"
mkdir -p "$CV_DIR"
if [ ! -f "$CV_DIR/cv_base.yaml" ]; then
    cp "$REPO_DIR/system/templates/cv_base.example.yaml" "$CV_DIR/cv_base.yaml"
    warn "IMPORTANT: Edit $CV_DIR/cv_base.yaml with your real profile before generating CVs!"
fi
cp "$REPO_DIR/cv-engine/cv_branded_generator.py" "$CV_DIR/" 2>/dev/null || true
log "CV engine OK"

echo ""
log "=== Installation Complete! ==="
echo ""
echo "Next steps:"
echo "  1. Edit ~/.openclaw/openclaw.json with your LLM credentials"
echo "  2. Edit the cv_base.yaml with your real profile data"
echo "  3. Start Chrome with CDP enabled (see setup_chrome_cdp.sh)"
echo "  4. Test the connection: python3 scripts/skills/test_browser.py"
echo "  5. Run job discovery: python3 scripts/skills/linkedin_job_search.py --preset core_br"
echo ""
echo "Docs: $REPO_DIR/docs/guides/INSTALLATION.md"
