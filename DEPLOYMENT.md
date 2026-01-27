# Deployment Guide

This guide explains how to deploy the **AI Powered Enterprise Guardrails** solution to a cloud environment so it can process 24/7 webhooks without running on your local machine.

## Prerequisites
- A Cloud Provider account (e.g., [Render](https://render.com), [Heroku](https://heroku.com), [Railway](https://railway.app)).
- Docker (if deploying to a VPS/VM).

---

## Architecture Recap
You need to deploy two services:
1.  **Backend (Python/FastAPI)**: The heavy lifter. Runs scans and calls the LLM.
2.  **GitHub App (Node.js)**: The connector. Receives webhooks and posts comments.

---

## 🚀 Option 1: Deploy with Docker (Recommended for VPS/AWS)

We have provided a `docker-compose.yml` file in the root directory.

1.  **Ensure Environment Variables are Set**:
    Make sure you have your `.env` files created effectively in the subdirectories:
    *   `backend/.env`: Contains `GEMINI_API_KEY`.
    *   `github-app/.env`: Contains `APP_ID`, `WEBHOOK_SECRET`, `PRIVATE_KEY`.
    *(The `docker-compose.yml` is configured to read these files directly).*

2.  **Run with Docker Compose**:
    **Crucial**: You must run this command from the **project root directory** (where `docker-compose.yml` is located), NOT inside `github-app` or `backend`.

    ```bash
    # Go to root
    cd .. 
    
    # Run Docker Compose (Note: use 'docker compose' for newer Docker versions)
    docker compose up -d --build
    ```

3.  **Expose to Public (The "Webhook URL")**:
    Your GitHub App container is listening on port `3000` on your server/machine. You need a public HTTPS URL to point GitHub to.

    #### Option A: Cloudflare Tunnel (Recommended for Security)
    Cloudflare Tunnel creates a secure link without opening firewall ports.
    1.  Install `cloudflared` on your server.
    2.  Run: `cloudflared tunnel --url http://localhost:3000`
    3.  Copy the generated URL (e.g., `https://random-name.trycloudflare.com`).
    4.  Use this as your Webhook URL in GitHub.

    #### Option B: Nginx Reverse Proxy (Standard for VPS)
    If you have a domain and Nginx installed:
    1.  Configure Nginx to proxy traffic from `your-domain.com` to `localhost:3000`.
    2.  Secure it with Certbot (Let's Encrypt).
    3.  Use `https://your-domain.com/api/github/webhooks` in GitHub.

    #### Option C: ngrok (For Quick Testing)
    If you just want to test the Docker container quickly:
    1.  **Sign up** at [ngrok.com](https://ngrok.com/signup) (it's free).
    2.  Get your **Authtoken** from the dashboard.
    3.  Run: `ngrok config add-authtoken <YOUR_TOKEN>`
    4.  Run: `ngrok http 3000`

---

## ☁️ Option 2: Deploy to Render.com (Easiest Free/Cheap Option)

Render is great because it handles HTTPS and build steps automatically.

### Step 1: Deploy Backend (Web Service)
1.  Create a **New Web Service**.
2.  Connect your repository.
3.  **Root Directory**: `backend`
4.  **Environment**: `Python 3`
5.  **Build Command**: `pip install -r requirements.txt`
6.  **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port 10000`
7.  **Environment Variables**:
    *   `GEMINI_API_KEY`: Your key.
8.  **Deploy**.
    *   Copy the URL (e.g., `https://ai-guardrails-backend.onrender.com`).

### Step 2: Deploy GitHub App (Web Service)
1.  Create another **New Web Service**.
2.  Connect the same repository.
3.  **Root Directory**: `github-app`
4.  **Environment**: `Node`
5.  **Build Command**: `npm install && npm run build`
6.  **Start Command**: `npm start`
7.  **Environment Variables**:
    *   `APP_ID`: From GitHub App Settings.
    *   `WEBHOOK_SECRET`: From GitHub App Settings.
    *   `PRIVATE_KEY`: Your .pem file content (ensure newlines are preserved).
    *   `BACKEND_URL`: **Important!** Set this to your Backend URL from Step 1 + `/api/v1` (e.g., `https://ai-guardrails-backend.onrender.com/api/v1`).
8.  **Deploy**.
    *   Copy *this* service's URL (e.g., `https://ai-guardrails-app.onrender.com`).

---

## 🔗 Final Step: Connect GitHub to Real Deployment

Once you have your **Deployed App URL** (e.g., `https://ai-guardrails-app.onrender.com`):

1.  Go to **GitHub Developer Settings -> GitHub Apps -> Your App**.
2.  Find **Webhook URL**.
3.  **Replace** the `smee.io` URL with your new deployed URL (from Cloudflare, Nginx, or **ngrok**).
    *   **Append**: `/api/github/webhooks`
    *   Example (Cloud): `https://ai-guardrails-app.onrender.com/api/github/webhooks`
    *   Example (ngrok): `https://abcd-123.ngrok-free.app/api/github/webhooks`
4.  **Save Changes**.

**Done!** Your app is now live. You can close your local terminal, and GitHub will send events directly to your cloud deployment.
