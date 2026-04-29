
# Minecraft Server Automation & Monitoring

Automated deployment, monitoring, and management of a Minecraft server using modern DevOps tools: Docker Compose, Ansible, GitHub Actions, Prometheus, Grafana, and Python.

---


## Key Features

- **Automated deployment** of Minecraft, Prometheus, and Grafana to a remote Linux server via Ansible and GitHub Actions
- **Monitoring** of Minecraft server (player stats, deaths) with Grafana dashboards 
- **Custom Python exporter** collects Minecraft server metrics (players online, deaths, total players) by querying the server via UDP
- **Configuration management** via Git (server.properties)
- **Persistent world data** – map and player data survive container rebuilds

---

## Quick Start

### 1. Requirements

- Remote Linux server with SSH access
- SSH key without passphrase (for CI/CD)
- GitHub repository secrets configured:
  - `SSH_PRIVATE_KEY`
  - `REMOTE_HOST`

### 2. Clone the repository

```bash
git clone https://github.com/your-username/minecraft-server-automation.git
cd minecraft-server-automation
```

### 3. Configure Minecraft server

Edit the file:
- `minecraft-config/server.properties`

Commit and push changes to `main` – this will trigger automatic deployment.

### 4. Deployment (CI/CD)

1. Push to `main`
2. GitHub Actions runs the Ansible playbook:
   - Installs Docker
   - Copies stack and configuration
   - Restarts Minecraft if `server.properties` changed

### 5. Local run (optional)

```bash
cd stack
docker compose up -d
```

### 6. Dashboards

```bash
http://<server ip>:8080
```

---



## Monitoring & Dashboards

- Prometheus collects Minecraft server metrics (via custom Python exporter, using UDP query protocol)
- Grafana visualizes stats (players online, deaths, etc.) and is accessed via Nginx reverse proxy (for production, consider adding firewall or authentication for security)
- Metrics from **node-exporter** (system metrics) and **cAdvisor** (container metrics) are collected and available in Prometheus for custom Grafana dashboards.

### Example dashboards

Players dashboard:
<img width="1920" height="1200" alt="Screenshot From 2026-04-29 17-20-27" src="https://github.com/user-attachments/assets/9d13e1e0-5835-49d5-9e1b-bc985fff87ef" />

Performance dashboards:
<img width="1920" height="1200" alt="Screenshot From 2026-04-29 17-16-25" src="https://github.com/user-attachments/assets/74ed404c-76cc-4e87-b6e7-7e49ff24a0d3" />

<img width="1920" height="1200" alt="Screenshot From 2026-04-29 17-17-04" src="https://github.com/user-attachments/assets/7dd5431b-3d10-4c25-8366-c8a58d93f1ad" />

---

## Project Structure

- `stack/` – Docker Compose, Prometheus, Grafana, Nginx configs
- `ansible/` – playbook, inventory
- `minecraft-config/` – Minecraft server configuration
- `mc-stats-exporter/` – Python metrics exporter

---

## Author

Filip Mach – [GitHub](https://github.com/fmach24) | [LinkedIn](https://linkedin.com/in/machfilip24)
