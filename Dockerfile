FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code, migrations, and tests
COPY app/ app/
COPY alembic/ alembic/
COPY alembic.ini alembic.ini
COPY tests/ tests/
COPY pytest.ini pytest.ini
COPY requirements-dev.txt requirements-dev.txt
COPY .env.example .env.example

# Expose port
EXPOSE 8090

# Entrypoint script: wait for db, run migrations, start uvicorn
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8090"]
