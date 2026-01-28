# Base image with Python
FROM python:3.12-slim

# Install system dependencies including Node.js and Supervisor
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    supervisor \
    net-tools \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# --- Backend Setup ---
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# --- GitHub App Setup ---
COPY github-app/package.json github-app/package-lock.json ./github-app/
WORKDIR /app/github-app
RUN npm ci

# Copy Source Code
WORKDIR /app
COPY backend ./backend
COPY github-app ./github-app
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.template.conf
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Build GitHub App (TypeScript -> JS)
WORKDIR /app/github-app
RUN npm run build

# Expose ports
EXPOSE 8000

# Set Default Env Vars
ENV PORT=8000
ENV HOST=0.0.0.0
ENV BACKEND_URL=http://127.0.0.1:8000/api/v1

# Start via script to handle PORT injection
CMD ["/start.sh"]
