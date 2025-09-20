FROM python:3.11-slim

WORKDIR /code

RUN apt-get update && apt-get install -y     build-essential curl gcc gnupg unixodbc unixodbc-dev     && rm -rf /var/lib/apt/lists/*

RUN curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > microsoft.gpg &&     install -o root -g root -m 644 microsoft.gpg /usr/share/keyrings/ &&     sh -c 'echo "deb [arch=amd64 signed-by=/usr/share/keyrings/microsoft.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" > /etc/apt/sources.list.d/microsoft.list' &&     apt-get update && ACCEPT_EULA=Y apt-get install -y msodbcsql18 &&     rm -rf /var/lib/apt/lists/* microsoft.gpg

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1
