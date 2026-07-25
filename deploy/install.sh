#!/usr/bin/env bash
# Idempotent installer for Birthly. Targets a clean Ubuntu 22.04/24.04 host.
# See SPEC.md chapter 33.
set -euo pipefail

APP_USER=birthly
APP_DIR=/opt/birthly

sudo apt update
sudo apt install -y python3.12 python3.12-venv python3-pip sqlite3 git

id -u "$APP_USER" &>/dev/null || sudo useradd -r -s /bin/false -d "$APP_DIR" "$APP_USER"
sudo mkdir -p "$APP_DIR" "$APP_DIR/data/backups" "$APP_DIR/data/logs"
sudo chown -R "$APP_USER:$APP_USER" "$APP_DIR"
sudo chmod 700 "$APP_DIR/data"

cd "$APP_DIR"
sudo -u "$APP_USER" python3.12 -m venv .venv
sudo -u "$APP_USER" .venv/bin/pip install --upgrade pip
sudo -u "$APP_USER" .venv/bin/pip install -r requirements.txt

if [ ! -f .env ]; then
  sudo -u "$APP_USER" cp .env.example .env
  echo "⚠️  ערוך את .env והכנס BOT_TOKEN, ואז הרץ שוב"
  exit 1
fi
sudo chmod 600 .env

sudo -u "$APP_USER" .venv/bin/alembic upgrade head

sudo cp deploy/birthly.service /etc/systemd/system/
sudo cp deploy/logrotate.birthly /etc/logrotate.d/birthly
sudo systemctl daemon-reload
sudo systemctl enable --now birthly
sudo systemctl status birthly --no-pager
