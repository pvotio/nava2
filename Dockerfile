FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    ACCEPT_EULA=Y

WORKDIR /code

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl gnupg ca-certificates apt-transport-https \
    build-essential gcc \
    unixodbc unixodbc-dev \
    libgssapi-krb5-2 libssl3 \
 && rm -rf /var/lib/apt/lists/*

RUN set -eux; \
    curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > /usr/share/keyrings/microsoft.gpg; \
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" > /etc/apt/sources.list.d/microsoft.list; \
    apt-get update; \
    apt-get install -y --no-install-recommends msodbcsql18; \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
