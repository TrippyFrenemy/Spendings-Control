# Dockerfile
FROM python:3.11-slim

# Set working directory in container
WORKDIR /app

# Install system dependencies required for Python packages
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create directory for logs
RUN mkdir -p /app/logs

CMD ["alembic", "revision"]
CMD ["alembic", "revision", "--autogenerate"]
CMD ["alembic", "upgrade", "head"]
# Command to run the application
CMD ["python", "main.py"]
