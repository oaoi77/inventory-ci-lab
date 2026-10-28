# Jenkins CI/CD on Ubuntu WSL2 - starter repository

This is a student starter project for a hands-on CI/CD laboratory. Jenkins is **installed directly as an Ubuntu service** in WSL2; the Flask inventory API is containerized with Docker.

## Repository structure
- `app/main.py`: Flask API (`/`, `/health`, `/api/items`, `/api/items/<id>`)
- `tests/test_api.py`: starter pytest tests
- `Dockerfile`: non-root production web container using Gunicorn
- `Jenkinsfile`: declarative CI/CD pipeline stored as code
- `requirements*.txt`: Python dependencies

## Prerequisites
Ubuntu 24.04 under WSL2, systemd enabled, Python 3, Git, Jenkins with Java 21, Docker with a working Ubuntu WSL CLI/daemon connection. Docker Desktop WSL integration or a native Docker Engine install can be used; do not start both daemons. Keep this repository in the Linux file system, not `/mnt/c`.

See the companion PDF for full installation instructions and the required graded challenges.

## Local verification
```bash
sudo apt update && sudo apt install -y python3-venv python3-pip git curl
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m pytest -v

docker build -t inventory-api:manual .
docker run -d --name inventory-manual -p 127.0.0.1:5050:5000 inventory-api:manual
curl -fsS http://127.0.0.1:5050/health
docker rm -f inventory-manual
```

## Jenkins setup
Create a Pipeline job; choose `Pipeline script from SCM`, Git, your GitHub repo URL, branch `*/main`, script path `Jenkinsfile`. Set credentials only if private. Ensure Jenkins can run Docker: `sudo usermod -aG docker jenkins && sudo systemctl restart jenkins`; then verify with `sudo -u jenkins docker ps`. Note: membership in `docker` grants root-equivalent host control; use this only in an isolated personal lab environment.

## Important limitations
Starter pipeline is for a local, isolated teaching environment. It intentionally uses one host, test-before-deploy, and a short interruption during live container replacement. It does **not** implement production-grade secrets, immutable dependencies, automatic rollback, vulnerability scanning, or a deployment approval gate: these are graded extension tasks.

## Troubleshooting
- Port 8080 already used: change Jenkins port via `sudo systemctl edit jenkins` using `[Service]` and `Environment="JENKINS_PORT=8081"`.
- Port 5050 used: `docker ps` and remove prior lab containers.
- Jenkins `permission denied` for Docker socket: verify daemon is running, group membership and restart Jenkins.
- Python venv fails: install `python3-venv`.
- Jenkins cannot checkout: check `main` branch, Git plugin, credential permissions.
