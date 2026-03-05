# OpenAI Enterprise Billing & Token Management

An **Odoo 19** module that provides granular department-level cost attribution, real-time usage dashboards, automated budget enforcement, and energy/carbon impact tracking for organisations using the OpenAI Enterprise API.

> **Designed with the OpenAI brand identity** — dark-themed dashboard, green accent palette, and clean typography.

---

## Table of Contents

1. [Features](#features)
2. [Screenshots](#screenshots)
3. [Prerequisites](#prerequisites)
4. [Step 1 — Install Docker Desktop](#step-1--install-docker-desktop)
5. [Step 2 — Create Docker Containers (First-Time Setup)](#step-2--create-docker-containers-first-time-setup)
6. [Step 3 — Install the Module](#step-3--install-the-module)
7. [Step 4 — Grant Admin Access to Billing Groups](#step-4--grant-admin-access-to-billing-groups)
8. [Running the Instance (After First-Time Setup)](#running-the-instance-after-first-time-setup)
9. [Stopping the Instance](#stopping-the-instance)
10. [Troubleshooting](#troubleshooting)
11. [Module Structure](#module-structure)
12. [License](#license)

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

## Screenshots

After setup, navigate to **OpenAI Billing → Dashboard** in the Odoo sidebar to see the dark-themed dashboard with live charts and KPI cards.

---

## Prerequisites

- **Operating System**: Windows 10/11, macOS, or Linux
- **RAM**: At least 4 GB free
- **Disk Space**: ~2 GB for Docker images
- **Internet**: Required for downloading Docker images

---

## Step 1 — Install Docker Desktop

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
# Install Docker Engine
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
```

You should see something like `Docker version 27.x.x`. If you get an error, make sure Docker Desktop is running.

---

## Step 2 — Create Docker Containers (First-Time Setup)

Open a terminal and run these commands **one at a time** in order.

### 2.1 — Create a Docker Network

```bash
docker network create odoo-net
```

### 2.2 — Start the PostgreSQL Database

```bash
docker run -d \
  --name db \
  --network odoo-net \
  -e POSTGRES_USER=odoo \
  -e POSTGRES_PASSWORD=1234 \
  -e POSTGRES_DB=odoo_docker \
  postgres:15
```

> **Windows PowerShell users** — replace `\` with `` ` `` (backtick) for line continuation, or paste it as one line:
>
> ```powershell
> docker run -d --name db --network odoo-net -e POSTGRES_USER=odoo -e POSTGRES_PASSWORD=1234 -e POSTGRES_DB=odoo_docker postgres:15
> ```

Wait about 10 seconds for the database to initialise.

### 2.3 — Copy the Module to a Known Path

The module folder must be accessible by the Odoo container. Place it somewhere convenient.

**On Windows** — if you cloned or downloaded this repo to `D:\OpenAI_Enterprise_Billing`, the path to mount is:

```
D:\OpenAI_Enterprise_Billing
```

Create a parent folder that Odoo will scan as its custom addons path. For example, create `D:\odoo_custom_addons` and copy this module inside it **renamed to `openai_billing`**:

```powershell
# Windows PowerShell
New-Item -ItemType Directory -Force -Path "D:\odoo_custom_addons"
Copy-Item -Path "D:\OpenAI_Enterprise_Billing" -Destination "D:\odoo_custom_addons\openai_billing" -Recurse -Force
```

**On macOS/Linux**:

```bash
mkdir -p ~/odoo_custom_addons
cp -r /path/to/OpenAI_Enterprise_Billing ~/odoo_custom_addons/openai_billing
```

> **Important**: The folder inside the addons path **must be named `openai_billing`** (matching the module's technical name).

### 2.4 — Start the Odoo 19 Container

**Windows PowerShell:**

```powershell
docker run -d --name odoo_docker --network odoo-net -p 8069:8069 -v D:\odoo_custom_addons:/mnt/extra-addons odoo:19 -- --db_host=db --db_user=odoo --db_password=1234 --database=odoo_docker --addons-path=/mnt/extra-addons,/usr/lib/python3/dist-packages/odoo/addons
```

**macOS / Linux:**

```bash
docker run -d \
  --name odoo_docker \
  --network odoo-net \
  -p 8069:8069 \
  -v ~/odoo_custom_addons:/mnt/extra-addons \
  odoo:19 \
  -- --db_host=db --db_user=odoo --db_password=1234 \
     --database=odoo_docker \
     --addons-path=/mnt/extra-addons,/usr/lib/python3/dist-packages/odoo/addons
```

Wait about 30 seconds for Odoo to fully start.

### 2.5 — Verify Odoo is Running

Open your browser and go to:

```
http://localhost:8069
```

You should see the Odoo login page. If you see a database creation screen instead, fill in:

| Field | Value |
|---|---|
| Master Password | admin |
| Database Name | `odoo_docker` |
| Email | `admin` |
| Password | choose any password (e.g. `admin`) |
| Language | English |
| Country | your country |

Then click **Create database**.

If you already see the login screen, log in with:
- **Email**: `admin`
- **Password**: whatever you set during database creation

---

## Step 3 — Install the Module

1. Log into Odoo at `http://localhost:8069`
2. Turn on **Developer Mode**:
   - Go to **Settings** (gear icon in the sidebar)
   - Scroll to the bottom and click **"Activate the developer mode"**
3. Go to **Apps** in the sidebar
4. Click **"Update Apps List"** in the top menu (you may need to click the ☰ hamburger menu to find it)
5. Remove the default `Apps` filter in the search bar
6. Search for **`OpenAI`** or **`openai_billing`**
7. Click **Install** on **"OpenAI Enterprise Billing & Token Management"**
8. Wait for the installation to complete (this loads 150 demo records)

After installation, you'll see **"OpenAI Billing"** appear in the left sidebar.

---

## Step 4 — Grant Admin Access to Billing Groups

The module creates three security groups (User, Manager, Admin). The `post_init_hook` automatically assigns the admin user during fresh installation. If the dashboard shows empty data, manually assign yourself:

**Option A — Via Odoo UI:**

1. Go to **Settings → Users & Companies → Users**
2. Click on your admin user
3. Scroll down to the **"OpenAI Billing"** section
4. Select **Billing Admin**
5. Click **Save**

**Option B — Via terminal (SQL):**

```bash
docker exec -it db psql -U odoo -d odoo_docker -c "
INSERT INTO res_groups_users_rel (gid, uid)
SELECT g.id, u.id
FROM res_groups g, res_users u
WHERE g.name IN ('Billing User','Billing Manager','Billing Admin')
  AND u.login = 'admin'
ON CONFLICT DO NOTHING;
"
```

Then refresh the dashboard page (Ctrl+Shift+R).

---

## Running the Instance (After First-Time Setup)

Once you've completed the first-time setup above, starting Odoo in the future is just two commands:

```bash
docker start db
docker start odoo_docker
```

Then open **http://localhost:8069** in your browser.

> **Tip**: Wait 5–10 seconds after starting `db` before starting `odoo_docker` so the database is ready.

---

## Stopping the Instance

```bash
docker stop odoo_docker
docker stop db
```

This gracefully shuts down both containers. Your data is preserved — just `docker start` them again next time.

---

## Troubleshooting

### "I see the dashboard but all charts and numbers are empty"

The admin user is not in the billing security groups. Follow [Step 4](#step-4--grant-admin-access-to-billing-groups).

### "I changed the filter and the charts disappeared"

Hard-refresh the browser: **Ctrl+Shift+R** (Windows/Linux) or **Cmd+Shift+R** (macOS). This clears cached JavaScript assets.

### "Module not found in Apps list"

1. Make sure the folder inside the addons path is named exactly **`openai_billing`** (not `OpenAI_Enterprise_Billing`)
2. Make sure you clicked **Update Apps List** after mounting the volume
3. Clear the default `Apps` filter before searching

### "Cannot connect to Docker daemon"

Make sure Docker Desktop is running. On Windows, check the system tray for the whale icon.

### "Port 8069 is already in use"

Another service is using port 8069. Either stop it or map a different port:

```bash
docker run -d --name odoo_docker --network odoo-net -p 9069:8069 ...
```

Then access Odoo at `http://localhost:9069`.

### Viewing Odoo Logs

```bash
docker logs odoo_docker --tail 50
```

### Updating the Module After Code Changes

If you edit module files and need to reload:

```bash
docker exec odoo_docker odoo -d odoo_docker -u openai_billing --stop-after-init --no-http --db_host=db --db_user=odoo --db_password=1234
docker restart odoo_docker
```

Then **Ctrl+Shift+R** in the browser.

---

## Module Structure

```
openai_billing/
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
