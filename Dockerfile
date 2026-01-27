# Base image with Python
FROM python:3.12-slim

# Install system dependencies including Node.js and Supervisor
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    supervisor \
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
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Build GitHub App (TypeScript -> JS)
WORKDIR /app/github-app
RUN npm run build

# Expose ports (Render only accepts one, usually 3000 for the app)
# Expose configured port (Railway will override PORT, we just need to let it)
# EXPOSE 3000 - Removed to avoid confusing Railway routing

# Expose configured port (Railway will override PORT, we just need to let it)
EXPOSE 8000

# Set Default Env Vars (can be overridden)
ENV PORT=8000
ENV HOST=0.0.0.0
ENV BACKEND_URL=http://localhost:8123/api/v1

# Start Supervisor
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
