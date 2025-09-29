FROM node:24.6.0-trixie-slim

WORKDIR /app

#### Removed packages
# libgconf-2-4 \
# libgl1-mesa-glx \
# libappindicator1 \

RUN apt-get update && apt-get install -y \
    wget \
    gpg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | gpg --dearmor > /usr/share/keyrings/google-linux-keyring.gpg \
    && sh -c 'echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-linux-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google.list' \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && apt-get update -y \
    && apt-get upgrade -y \
    && npm update -g npm

COPY package*.json ./

RUN npm install

COPY . .

CMD ["npm", "start"]


# FROM node:24.6.0-trixie-slim

# WORKDIR /app

# #### Removed packages
# # libgconf-2-4 \
# # libgl1-mesa-glx \
# # libappindicator1 \

# RUN apt-get update && apt-get install -y \
#     libatk1.0-0 \
#     libatk-bridge2.0-0 \
#     libcups2 \
#     libdrm2 \
#     libxkbcommon-x11-0 \
#     libxcomposite1 \
#     libxrandr2 \
#     libgbm1 \
#     libpangocairo-1.0-0 \
#     libpango-1.0-0 \
#     libcairo2 \
#     libasound2 \
#     libatspi2.0-0 \
#     libnss3 \
#     libxss1 \
#     libxi6 \
#     fonts-liberation \
#     wget \
#     gpg \
#     xdg-utils \
#     && apt-get clean \
#     && rm -rf /var/lib/apt/lists/* \
#     && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | gpg --dearmor > /usr/share/keyrings/google-linux-keyring.gpg \
#     && sh -c 'echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-linux-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google.list' \
#     && apt-get update \
#     && apt-get install -y google-chrome-stable \
#     && apt-get update -y \
#     && apt-get upgrade -y \
#     && npm update -g npm

# COPY package*.json ./

# RUN npm install

# COPY . .

# CMD ["npm", "start"]


