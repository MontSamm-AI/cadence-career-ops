# VPS Setup Guide

## Cadence Career Ops — Persistent Layer on Hetzner/Docker Swarm

---

## Overview

The VPS is the **persistent brain** of the system. It runs continuously, holding your CRM data, orchestrating workflows, and providing long-running services that the local WSL environment cannot reliably provide.

**Current VPS**: Hetzner Cloud, Debian 13, Docker Swarm mode

This guide assumes you have a fresh VPS and want to replicate the production setup.

---

## Requirements

- VPS with 4+ GB RAM, 2+ vCPUs (Hetzner CX22 or equivalent)
- Debian 12+ or Ubuntu 22+
- Domain name (for Traefik TLS — optional but recommended)

---

## Step 1: Initial Server Setup

```bash
# SSH into your VPS
ssh root@YOUR_VPS_IP

# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com | sh
systemctl enable docker

# Initialize Docker Swarm
docker swarm init --advertise-addr YOUR_VPS_IP

# Create shared network
docker network create --driver overlay --attachable network_swarm_public
docker network create --driver overlay --attachable network_swarm_internal

# Create data directories
mkdir -p /opt/stacks /data/workspace /data/openclaw
```

---

## Step 2: Deploy Core Infrastructure

### Traefik (Reverse Proxy + TLS)

```bash
# Create traefik stack file
cat > /opt/stacks/traefik.yaml << 'EOF'
version: '3.8'
services:
  traefik:
    image: traefik:v3
    command:
      - "--providers.docker=true"
      - "--providers.docker.swarmmode=true"
      - "--providers.docker.exposedbydefault=false"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.letsencrypt.acme.tlschallenge=true"
      - "--certificatesresolvers.letsencrypt.acme.email=YOUR_EMAIL"
      - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - /opt/stacks/letsencrypt:/letsencrypt
    networks:
      - network_swarm_public
    deploy:
      placement:
        constraints: [node.role == manager]

networks:
  network_swarm_public:
    external: true
EOF

docker stack deploy -c /opt/stacks/traefik.yaml traefik
```

### PostgreSQL

```bash
cat > /opt/stacks/postgres.yaml << 'EOF'
version: '3.8'
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_PASSWORD: YOUR_SECURE_PASSWORD
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - network_swarm_internal
    deploy:
      replicas: 1

volumes:
  postgres_data:

networks:
  network_swarm_internal:
    external: true
EOF

docker stack deploy -c /opt/stacks/postgres.yaml postgres
```

### n8n

```bash
cat > /opt/stacks/n8n.yaml << 'EOF'
version: '3.8'
services:
  editor:
    image: n8nio/n8n:latest
    environment:
      - N8N_HOST=n8n.YOUR_DOMAIN
      - N8N_PROTOCOL=https
      - DB_TYPE=postgresdb
      - DB_POSTGRESDB_HOST=postgres
      - DB_POSTGRESDB_DATABASE=n8n
      - DB_POSTGRESDB_USER=postgres
      - DB_POSTGRESDB_PASSWORD=YOUR_SECURE_PASSWORD
      - N8N_ENCRYPTION_KEY=YOUR_ENCRYPTION_KEY
    networks:
      - network_swarm_public
      - network_swarm_internal
    deploy:
      labels:
        - "traefik.enable=true"
        - "traefik.http.routers.n8n.rule=Host(`n8n.YOUR_DOMAIN`)"
        - "traefik.http.routers.n8n.tls.certresolver=letsencrypt"
        - "traefik.http.services.n8n.loadbalancer.server.port=5678"

networks:
  network_swarm_public:
    external: true
  network_swarm_internal:
    external: true
EOF

docker stack deploy -c /opt/stacks/n8n.yaml n8n
```

---

## Step 3: Install OpenClaw VPS Agent

```bash
# Install OpenClaw on VPS
curl -fsSL https://openclaw.dev/install.sh | bash

# Configure
mkdir -p /data/openclaw
cp /path/to/openclaw.vps.example.json /data/openclaw/openclaw.json
# Edit with your Groq API key and Telegram bot token

# Set up workspace
mkdir -p /data/workspace
# Copy SOUL.md, USER.md, TOOLS.md, IDENTITY.md to /data/workspace/
```

---

## Step 4: Career Tracker Database

```bash
# Connect to PostgreSQL and create schema
docker exec -it $(docker ps -q -f name=postgres_postgres) psql -U postgres

# In psql:
CREATE DATABASE career_tracker;
\c career_tracker

CREATE SCHEMA career;

CREATE TABLE career.job_applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    linkedin_job_id TEXT UNIQUE,
    company TEXT,
    role TEXT,
    location TEXT,
    url TEXT,
    status TEXT,
    stage TEXT,
    applied_date DATE,
    source TEXT,
    cv_used TEXT,
    score INTEGER,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE career.inbound_email_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID REFERENCES career.job_applications(id),
    event_type TEXT,  -- confirmed, interview, rejection, assessment, recruiter_reply
    email_subject TEXT,
    email_from TEXT,
    received_at TIMESTAMPTZ,
    raw_snippet TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE career.linkedin_posts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    post_id TEXT UNIQUE,
    topic TEXT,
    language TEXT,
    published_at TIMESTAMPTZ,
    url TEXT,
    image_path TEXT,
    copy_snippet TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

\q
```

---

## Step 5: Verify Stack Health

```bash
# Check all services are running
docker service ls

# Expected output (all should show 1/1 or N/N):
# traefik_traefik        1/1
# postgres_postgres      1/1
# n8n_editor             1/1
# openclaw_gateway       1/1
# ...

# Check logs for any service
docker service logs postgres_postgres --tail 20
docker service logs n8n_editor --tail 20
```

---

## Production Stack (Reference)

The current production stack runs 14 services:

```
traefik         — Reverse proxy + TLS
postgres        — PostgreSQL 16 (5 databases)
redis           — Redis cache
n8n_editor      — n8n workflow editor
n8n-workers     — n8n execution workers
openclaw_gateway — VPS agent runtime
portainer       — Container management UI
evolution       — WhatsApp API (Evolution API v2)
paperclip       — Document management
pgadmin         — PostgreSQL admin
redisinsight    — Redis management
alianca_api     — Custom FastAPI backend
```

---

## SSH Access

```bash
# From WSL
ssh -i ~/.ssh/id_ed25519_vps root@YOUR_VPS_IP

# Useful commands
docker service ls                                    # Service health
docker service logs SERVICE_NAME --tail 50           # Service logs
docker stack deploy -c /opt/stacks/FILE.yaml NAME    # Deploy/update stack
docker stack ls                                      # List stacks
```

---

## Security Checklist

- [ ] Change all default passwords before deploying
- [ ] Use strong random tokens for n8n encryption key and API keys
- [ ] Restrict Postgres to internal network only (no public port)
- [ ] Enable UFW: allow only ports 22, 80, 443
- [ ] Use SSH key auth only (disable password auth)
- [ ] Regularly rotate API keys and bot tokens
