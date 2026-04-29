# Minecraft Server (Docker + Ansible + GitHub Actions)

This repo deploys a Minecraft server stack to a remote Linux host using Ansible and GitHub Actions.

## What gets deployed
- Minecraft server (itzg/minecraft-server)
- Prometheus
- Grafana

## Folder layout
- stack/ - Docker Compose stack
- ansible/ - Ansible playbook and inventory
- minecraft-config/ - server.properties managed in Git

## Requirements
- Remote Linux host with SSH access
- SSH key without a passphrase (or CI will fail)
- GitHub repo secrets set

## GitHub Secrets
Set these in your GitHub repository:
- SSH_PRIVATE_KEY: private key used for SSH
- REMOTE_HOST: IP or hostname of the server

## Inventory
The inventory uses a template variable from CI:

ansible/inventory.ini:
- ansible_host is set from REMOTE_HOST by the workflow

## How deploy works
1) Push to main
2) GitHub Actions runs the Ansible playbook
3) Playbook:
   - installs Docker
   - creates /home/minecraft/app
   - copies stack and server.properties
   - restarts Minecraft if server.properties changed

## Configure server.properties
Edit:
- minecraft-config/server.properties

Then push to main. The playbook copies it to:
- /home/minecraft/app/config/server.properties

The container mounts it as:
- /data/server.properties

## World data (map)
The world is stored on the server at:
- /home/minecraft/app/mc-data

This folder is mounted into the container as /data, so the map survives container rebuilds.

## Local run (optional)
If you want to test locally:

```
cd stack
docker compose up -d
```

## Troubleshooting
Check container logs:

```
docker logs --tail=200 mc-server
```

**Deployment, persistence and reset behaviour (detailed)**

This section explains exactly how the stack is deployed, which files are persisted across container restarts, and what will be lost when containers are recreated.

- Top-level workflow
   - You push to `main` → GitHub Actions runs `ansible-playbook` (see `.github/workflows/deploy.yml`).
   - `ansible/playbook.yml` on the remote host:
      - Installs `docker` and `docker-compose`.
      - Ensures a `minecraft` user and the `{{ app_path }}` directories exist.
      - Copies the repository `stack/` and `minecraft-config/server.properties` into `{{ app_path }}` on the host.
      - Runs `docker compose up -d` (playbook is configured to recreate containers when the `stack` copy changes or when files change).
      - When `server.properties` changes the playbook restarts only the Minecraft container.

- What is mounted (persistent on host)
   - `stack/docker-compose.yml` mounts these host folders into containers:
      - `./mc-data:/data` (Minecraft world, player data, `usercache.json`, `stats/*.json`) — this is the primary persistence point for world and player statistics.
      - `./config/server.properties:/data/server.properties` — the server configuration; editing this file in the repo and redeploying will apply the config.
      - `./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro` — Prometheus config file is mounted (read‑only) so you manage scraping targets in Git.
      - `prometheus_data:/prometheus` — Prometheus TSDB is stored in a Docker named volume `prometheus_data` (recommended). Use `docker volume ls` and `docker volume inspect prometheus_data` to inspect or migrate data. To instead keep TSDB on the host, change the compose file to `./prometheus/data:/prometheus`.
      - `./nginx/default.conf:/etc/nginx/conf.d/default.conf:ro` — nginx proxy config for Grafana (if you keep `grafana-proxy`).
   - `node-exporter` and `cadvisor` mount host system paths (`/proc`, `/sys`, `/var/lib/docker` etc.) read-only — these are read-only system mounts and not persisted by Docker.

- What is persistent vs what resets
   - Persistent (won't be lost when a container restarts or is recreated): anything under host-mounted folders listed above (most important: `mc-data`, `config/server.properties`, `prometheus/prometheus.yml`).
   - Not persistent (will be lost if you remove and recreate the container) unless you add explicit volumes:
      - Prometheus TSDB (time-series database) — this repo now mounts `./prometheus/data:/prometheus` and Prometheus is configured to use `/prometheus` as its TSDB path (see `docker-compose.yml` `--storage.tsdb.path`). That means historical metrics are persisted on the host and survive container recreation. Retention is controlled by `--storage.tsdb.retention.time` (currently set to `5d` in the compose file).
      - Grafana database (dashboards, users, preferences) — this repo stores Grafana data in a Docker named volume `grafana_data:/var/lib/grafana` (recommended). Inspect with `docker volume ls` and `docker volume inspect grafana_data`. To store Grafana DB on the host instead, change the compose file to `./grafana/data:/var/lib/grafana`.
      - Grafana provisioning — this repo mounts `./grafana/provisioning:/etc/grafana/provisioning:ro`. Place datasource YAMLs in `grafana/provisioning/datasources` and dashboard JSON files in `grafana/provisioning/dashboards` to have Grafana auto-load them at startup.
      - Any files stored inside container image layers (not mounted) are ephemeral across container recreate.

- Why you saw `down` for the old target
   - Prometheus reads its `prometheus.yml` at startup and keeps its configuration in memory. If you update the mounted file on disk but do not reload or restart the Prometheus process, Prometheus will continue scraping the old targets.
   - `docker compose up -d` does not always recreate containers when only file contents mounted into the container change. To ensure the running process sees the new config you must either:
      - Ask Prometheus to reload via `POST /-/reload` (preferred, no restart), or
      - Recreate/restart the Prometheus container so the new process reads the updated file.
   - The playbook has been updated to either run a reload or recreate so the change is applied on deploy.

- Best practices and recommendations
   - Do NOT publish the exporter port (9225) or Prometheus port publicly unless you need to. Prometheus can scrape exporters internally through docker network. If you must expose metrics externally, protect them (VPN, reverse proxy with auth, firewall rules).
   - Add persistent host volumes for Prometheus TSDB and Grafana data if you want metrics and dashboards to survive container recreation.
   - Keep secrets out of repository: `server.properties` currently contains `rcon.password` and a management secret. For public repos move these into secrets or use Ansible templates + vault or environment variables.
   - Use `/-/reload` for Prometheus when possible (fast, no downtime). Use container recreate only if reload is not available.

- How to check status and logs (quick commands)
   - Show container status:
      ```bash
      cd stack
      docker compose ps
      ```
   - Check exporter `/metrics` (from Prometheus container or host if published):
      ```bash
      docker compose exec prometheus sh -c "wget -qO- http://mc-stats-exporter:9225/metrics | head -n 40"
      # or from host (if port published):
      curl -s http://<HOST>:9225/metrics | head -n 40
      ```
   - Check Prometheus active targets and health via API:
      ```bash
      docker compose exec prometheus sh -c "wget -qO- http://localhost:9090/api/v1/targets" | jq '.data.activeTargets[] | {scrapeUrl: .scrapeUrl, health: .health, labels: .labels}'
      ```
   - Check logs:
      ```bash
      docker compose logs -f mc-stats-exporter
      docker compose logs -f prometheus
      docker compose logs -f grafana
      ```

- Quick Ansible deployment notes
   - The playbook copies `stack/` into `{{ app_path }}` and runs `docker compose up -d`.
   - Playbook now attempts to reload Prometheus (via `POST /-/reload`) when config changes and falls back to restart if reload fails; this prevents the `down` target problem.
   - If you prefer minimal downtime, rely on Prometheus reload; if you prefer a guaranteed fresh start for all containers use recreate.

If you want I can also:
- Add host volumes for Prometheus and Grafana and update `docker-compose.yml` to persist data, and
- Add an Ansible task to template `server.properties` from secrets rather than committing plaintext secrets.

Check that server.properties is the one being used:

```
head -n 5 /home/minecraft/app/config/server.properties
docker exec -it mc-server sh -c "head -n 5 /data/server.properties"
```
