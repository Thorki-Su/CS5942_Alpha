#!/usr/bin/env bash
set -o errexit  # 遇到错误时停止执行
pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate