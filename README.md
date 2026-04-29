
# Minecraft Server Automation & Monitoring

Automated deployment, monitoring, and management of a Minecraft server using modern DevOps tools: Docker Compose, Ansible, GitHub Actions, Prometheus, Grafana, and Python.

---

## Key Features

- **Automated deployment** of Minecraft, Prometheus, and Grafana to a remote Linux server via Ansible and GitHub Actions
- **Monitoring** of Minecraft server (player stats, TPS, resource usage) with Grafana dashboards
- **Custom Python exporter** for Minecraft metrics
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

---

## Monitoring & Dashboards

- Prometheus collects Minecraft server metrics (via custom Python exporter)
- Grafana visualizes stats (online players, TPS, CPU/RAM usage)

### Example dashboards

![Players dashboard](./screenshots/grafana-players.png)
![Performance dashboard](./screenshots/grafana-performance.png)

---

## Project Structure

- `stack/` – Docker Compose, Prometheus, Grafana, Nginx configs
- `ansible/` – playbook, inventory
- `minecraft-config/` – Minecraft server configuration
- `mc-stats-exporter/` – Python metrics exporter

---

## Highlights

- Full automation of deployment and monitoring
- Integration of custom metrics with Prometheus and Grafana
- Real-world DevOps toolchain in action

---

## Author

Filip Mach – [GitHub](https://github.com/fmach24) | [LinkedIn](https://linkedin.com/in/machfilip24)