#!/usr/bin/env bash
# Pull latest, reinstall deps, migrate, restart. See SPEC.md chapter 33.
set -euo pipefail

cd /opt/birthly
sudo -u birthly git pull
sudo -u birthly .venv/bin/pip install -r requirements.txt
sudo -u birthly .venv/bin/alembic upgrade head
sudo systemctl restart birthly
