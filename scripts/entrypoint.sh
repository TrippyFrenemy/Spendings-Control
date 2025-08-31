#!/bin/sh

echo "⏳ Waiting for DB to be ready..."
sleep 2

echo "⚙️ Running Alembic migrations..."
alembic upgrade head

echo "🚀 Starting telegram bot..."
exec python main.py
