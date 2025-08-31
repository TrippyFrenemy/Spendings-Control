#!/bin/sh

echo "⏳ Waiting for DB to be ready..."
sleep 2

alembic revision
alembic revision --autogenerate -m "Auto migration"

echo "⚙️ Running Alembic migrations..."
alembic upgrade head

echo "🚀 Starting telegram bot..."
exec python main.py
