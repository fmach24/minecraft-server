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

Check that server.properties is the one being used:

```
head -n 5 /home/minecraft/app/config/server.properties
docker exec -it mc-server sh -c "head -n 5 /data/server.properties"
```
