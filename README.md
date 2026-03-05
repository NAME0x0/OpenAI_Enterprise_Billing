# OpenAI Enterprise Billing & Token Management

An **Odoo 19** module that provides granular department-level cost attribution, real-time usage dashboards, automated budget enforcement, and energy/carbon impact tracking for organisations using the OpenAI Enterprise API.

> **Designed with the OpenAI brand identity** — dark-themed dashboard, green accent palette, and clean typography.

---

## Quick Start (3 Commands)

```bash
git clone https://github.com/NAME0x0/OpenAI_Enterprise_Billing.git
cd OpenAI_Enterprise_Billing
docker compose up -d
```

Then open **http://localhost:8069** — that's it.

---

## Table of Contents

1. [Features](#features)
2. [Prerequisites](#prerequisites)
3. [Step 1 — Install Docker](#step-1--install-docker)
4. [Step 2 — Start the Stack](#step-2--start-the-stack)
5. [Step 3 — Create the Odoo Database](#step-3--create-the-odoo-database)
6. [Step 4 — Install the Module](#step-4--install-the-module)
7. [Step 5 — Grant Admin Access to Billing Groups](#step-5--grant-admin-access-to-billing-groups)
8. [Day-to-Day Usage](#day-to-day-usage)
9. [Troubleshooting](#troubleshooting)
10. [Module Structure](#module-structure)
11. [License](#license)

---

## Features

| Area | Capability |
|---|---|
| **Dashboard** | Real-time Chart.js dashboard with KPI cards, bar charts, pie chart, and quota utilisation — all in OpenAI's dark theme |
| **Departments** | Organisational Unit management with monthly token quotas and automatic suspension at limits |
| **Cost Tracking** | Per-request cost attribution by department, model, project, and purpose category |
| **Budget Alerts** | Automated threshold alerts at 80%, 90%, and 100% of budget |
| **Energy & Carbon** | Estimated energy consumption (kWh) and CO₂ emissions per request based on Luccioni et al. (2024) + IEA grid intensity data |
| **21 AI Models** | Pre-configured with 2025/2026 OpenAI models (GPT-4.1, o3, o4-mini, etc.) with accurate token pricing |
| **Reports** | Monthly expenditure reports (CSV/PDF), pivot views, graph views |
| **Audit Trail** | Immutable administrative audit log |
| **Demo Data** | 150 realistic usage log records across 6 departments for immediate exploration |

---

## Prerequisites

- **Operating System**: Windows 10/11, macOS, or Linux
- **RAM**: At least 4 GB free
- **Disk Space**: ~2 GB for Docker images
- **Internet**: Required for downloading Docker images
- **Git**: To clone this repo (or download the ZIP)

---

## Step 1 — Install Docker

Docker runs the Odoo 19 server and PostgreSQL database in isolated containers. No other software is needed.

### Windows

1. Go to **https://www.docker.com/products/docker-desktop/**
2. Click **"Download for Windows"**
3. Run the installer (`Docker Desktop Installer.exe`)
4. During installation, ensure **"Use WSL 2 instead of Hyper-V"** is checked (recommended)
5. Restart your computer when prompted
6. Launch **Docker Desktop** from the Start Menu
7. Wait until the status bar shows **"Docker Desktop is running"** (the whale icon in the system tray should be steady, not animated)

> **Windows requirements**: Windows 10 version 2004+ (Build 19041+) with WSL 2 enabled.
> If WSL 2 is not installed, Docker Desktop will guide you. You can also run `wsl --install` in an admin PowerShell.

### macOS

1. Go to **https://www.docker.com/products/docker-desktop/**
2. Download the `.dmg` for your chip (Apple Silicon or Intel)
3. Drag **Docker** to Applications and launch it
4. Grant permissions when prompted

### Linux (Ubuntu/Debian)

```bash
# Install Docker Engine + Compose plugin
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Allow non-root usage
sudo usermod -aG docker $USER
newgrp docker
```

### Verify Docker is Working

Open a terminal (PowerShell on Windows, Terminal on macOS/Linux) and run:

```bash
docker --version
docker compose version
```

You should see version numbers for both. If you get an error, make sure Docker Desktop is running.

---

## Step 2 — Start the Stack

This repo includes a `docker-compose.yml` that sets up PostgreSQL 15 and Odoo 19 with the correct credentials, networking, and volume mounts — all automatically. It uses the Odoo 19 entrypoint's own default credentials (`odoo`/`odoo`), so there are no custom user configurations that can conflict.

### 2.1 — Clone (or download) this repository

```bash
git clone https://github.com/NAME0x0/OpenAI_Enterprise_Billing.git
cd OpenAI_Enterprise_Billing
```

Or download the ZIP from GitHub and extract it.

### 2.2 — Start both containers

```bash
docker compose up -d
```

This will:
- Pull the `postgres:15` and `odoo:19` images (first time only, ~1.5 GB)
- Create a PostgreSQL database with the correct user and credentials
- Wait for PostgreSQL to be healthy before starting Odoo (via a healthcheck)
- Mount this folder as a custom addons path inside Odoo
- Expose Odoo at **http://localhost:8069**

### 2.3 — Wait for startup

Watch the logs to know when Odoo is ready:

```bash
docker compose logs -f odoo
```

When you see a line like `odoo.http: HTTP service (Werkzeug) running on ...`, Odoo is ready. Press **Ctrl+C** to stop following logs.

---

## Step 3 — Create the Odoo Database

Open your browser and go to:

```
http://localhost:8069
```

You'll see the **database manager** screen. Fill in:

| Field | Value |
|---|---|
| Master Password | `admin` |
| Database Name | `openai_billing` |
| Email | `admin` |
| Password | choose any password (e.g. `admin`) |
| Language | English |
| Country | your country |
| Demo data | checked ✓ |

Click **Create database** and wait 30–60 seconds.

> **Note**: The database name `openai_billing` matches the `docker-compose.yml` configuration. You can use a different name, but make sure to use it consistently when running update commands later.

---

## Step 4 — Install the Module

1. Log into Odoo at `http://localhost:8069`
2. Turn on **Developer Mode**:
   - Go to **Settings** (gear icon in the sidebar)
   - Scroll to the bottom and click **"Activate the developer mode"**
3. Go to **Apps** in the sidebar
4. Click **"Update Apps List"** in the top menu (you may need to click the ☰ hamburger menu to find it). Confirm when prompted.
5. Remove the default `Apps` filter in the search bar
6. Search for **`OpenAI`** or **`openai_billing`**
7. Click **Install** on **"OpenAI Enterprise Billing & Token Management"**
8. Wait for the installation to complete (this loads 150 demo records)

After installation, you'll see **"OpenAI Billing"** appear in the left sidebar.

---

## Step 5 — Grant Admin Access to Billing Groups

The module creates three security groups (User, Manager, Admin). The `post_init_hook` automatically assigns the admin user during fresh installation. If the dashboard shows empty data, manually assign yourself:

**Option A — Via Odoo UI:**

1. Go to **Settings → Users & Companies → Users**
2. Click on your admin user
3. Scroll down to the **"OpenAI Billing"** section
4. Select **Billing Admin**
5. Click **Save**

**Option B — Via terminal (SQL):**

```bash
docker exec -it openai_billing_db psql -U odoo -d openai_billing -c "
INSERT INTO res_groups_users_rel (gid, uid)
SELECT g.id, u.id
FROM res_groups g, res_users u
WHERE g.name IN ('Billing User','Billing Manager','Billing Admin')
  AND u.login = 'admin'
ON CONFLICT DO NOTHING;
"
```

Then hard-refresh the dashboard page (**Ctrl+Shift+R**).

---

## Day-to-Day Usage

### Starting the stack

```bash
cd OpenAI_Enterprise_Billing
docker compose up -d
```

Then open **http://localhost:8069**.

### Stopping the stack

```bash
docker compose down
```

This stops both containers. Your data is preserved in Docker volumes — just `docker compose up -d` again next time.

### Viewing logs

```bash
# Both services
docker compose logs -f

# Odoo only
docker compose logs -f odoo

# Last 50 lines
docker compose logs --tail 50 odoo
```

### Updating the module after code changes

If you edit module files and want to reload:

```bash
docker exec openai_billing_odoo odoo -d openai_billing -u openai_billing --stop-after-init --no-http --db_host=db --db_user=odoo --db_password=odoo
docker compose restart odoo
```

Then **Ctrl+Shift+R** in the browser to clear cached JS/CSS assets.

---

## Troubleshooting

### "FATAL: password authentication failed" or "role does not exist"

The PostgreSQL data volume was initialised with different credentials from a previous run. The `POSTGRES_USER` and init scripts only execute on the **very first** container start. Destroy the stale volume and restart:

```bash
docker compose down -v
docker compose up -d
```

> **Warning**: `docker compose down -v` deletes all database data. Only use this on a first-time setup or if you're okay losing existing data.

**Why this repo is resilient**: The `docker-compose.yml` uses `POSTGRES_USER=odoo` / `POSTGRES_PASSWORD=odoo` — the exact same defaults the Odoo 19 Docker entrypoint uses internally. This means even if environment variables are lost or the entrypoint overrides command-line args, the credentials still match.

### "I see the dashboard but all charts and numbers are empty"

The admin user is not in the billing security groups. Follow [Step 5](#step-5--grant-admin-access-to-billing-groups).

### "I changed the filter and the charts disappeared"

Hard-refresh the browser: **Ctrl+Shift+R** (Windows/Linux) or **Cmd+Shift+R** (macOS). This clears cached JavaScript assets.

### "Module not found in Apps list"

1. Make sure you cloned the repo and ran `docker compose up -d` from **inside the repo folder**
2. Make sure you clicked **Update Apps List** after starting the containers
3. Clear the default `Apps` filter in the search bar before searching

### "Cannot connect to Docker daemon"

Make sure Docker Desktop is running. On Windows, check the system tray for the whale icon.

### "Port 8069 is already in use"

Another service is using port 8069. Either stop it, or edit `docker-compose.yml` and change the ports line:

```yaml
ports:
  - "9069:8069"   # Access Odoo at localhost:9069 instead
```

Then `docker compose up -d` and access Odoo at `http://localhost:9069`.

### Container status check

```bash
docker compose ps
```

Both `openai_billing_db` and `openai_billing_odoo` should show `Up` / `running`. The db should also show `(healthy)`.

### Full reset (nuclear option)

If nothing works, remove everything and start over:

```bash
docker compose down -v --rmi all
docker compose up -d
```

This removes containers, volumes, AND images. It will re-download everything (~1.5 GB).

---

## Module Structure

```
openai_billing/
├── docker-compose.yml       # One-command setup (PostgreSQL + Odoo 19)
├── __manifest__.py          # Module metadata, dependencies, assets
├── __init__.py              # Python package init + post_init_hook
├── controllers/
│   ├── main.py              # Dashboard RPC endpoints (KPIs + charts)
│   └── export.py            # CSV/PDF export controllers
├── models/
│   ├── ai_model.py          # 21 AI model definitions with token pricing
│   ├── api_key.py           # API key management per department
│   ├── audit_trail.py       # Immutable admin action log
│   ├── billing_report.py    # Monthly expenditure report generation
│   ├── grid_intensity.py    # Regional grid carbon intensity (gCO₂/kWh)
│   ├── org_unit.py          # Departments with quotas & auto-suspension
│   ├── project_tag.py       # Project-based cost tagging
│   ├── quota_alert.py       # Budget threshold alerts
│   └── usage_log.py         # Per-request usage records with energy calc
├── views/
│   ├── dashboard_action.xml # OWL client action registration
│   ├── menu.xml             # Application menu hierarchy
│   ├── usage_log_views.xml  # List, form, pivot, graph + analytical actions
│   ├── org_unit_views.xml   # Department management views
│   ├── ai_model_views.xml   # AI model configuration
│   └── ...                  # Other standard Odoo views
├── static/
│   ├── description/
│   │   └── icon.png         # OpenAI-branded module icon
│   └── src/
│       ├── css/
│       │   └── billing_dashboard.css   # Dark theme (OpenAI brand)
│       ├── js/
│       │   └── billing_dashboard.js    # OWL component + Chart.js
│       └── xml/
│           └── billing_dashboard.xml   # Dashboard QWeb template
├── security/
│   ├── security.xml         # User/Manager/Admin groups
│   └── ir.model.access.csv  # Model-level ACL rules
├── data/
│   ├── default_models.xml   # 21 pre-configured AI models
│   ├── grid_intensity_data.xml  # 7 regional carbon intensity records
│   ├── cron_data.xml        # Scheduled actions
│   └── demo_data.xml        # 150 sample usage log records
└── report/
    └── monthly_report.xml   # QWeb report template
```

---

## License

LGPL-3.0 — see Odoo's licensing terms.

**Author**: Afsah
