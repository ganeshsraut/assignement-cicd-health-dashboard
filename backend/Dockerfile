# ========= Build stage (deps layer) =========
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc curl build-essential libpq-dev \
 && rm -rf /var/lib/apt/lists/*

# 👇 Context is ./backend, so copy from root of context
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# ========= Runtime =========
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends libpq-dev \
 && rm -rf /var/lib/apt/lists/*

COPY --from=base /usr/local/lib/python3.11 /usr/local/lib/python3.11
COPY --from=base /usr/local/bin /usr/local/bin

# 👇 Context is ./backend, so copy the whole app directory
COPY . /app

EXPOSE 8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
