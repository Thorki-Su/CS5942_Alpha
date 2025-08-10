#!/usr/bin/env bash
set -o errexit  # Stop execution when encountering errors
pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate