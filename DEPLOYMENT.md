# Deployment Guide

This guide explains how to deploy the **AI Powered Enterprise Guardrails** solution to a cloud environment so it can process 24/7 webhooks without running on your local machine.

## Prerequisites
- A Cloud Provider account (e.g., [Render](https://render.com), [Heroku](https://heroku.com), [Railway](https://railway.app)).
- Docker (if deploying to a VPS/VM).

---
---

## 🛑 Step 0: Setting Up Version Control (First Time Only)

Before deploying, you must ensure your code is safely stored in a Git repository (like GitHub).

### 1. Initialize Git (If not already done)
Open your terminal in the project root:
```bash
# Initialize git
git init

# We have provided a .gitignore file to exclude secrets (.env) and dependencies.
# Verify it exists:
ls -a .gitignore
```

### 2. Commit Your Code
```bash
git add .
git commit -m "Initial commit for AI Guardrails"
```

### 3. Push to a New GitHub Repository
1.  Go to [github.com/new](https://github.com/new).
2.  Name your repository (e.g., `ai-guardrails-enterprise`).
3.  **Do not** initialize with README or .gitignore (you already have them).
4.  Click **Create repository**.
5.  Copy the commands under "…or push an existing repository from the command line":

```bash
git remote add origin https://github.com/YOUR_USERNAME/ai-guardrails-enterprise.git
git branch -M main
git push -u origin main
```

---
## Architecture Recap
You need to deploy two services:
1.  **Backend (Python/FastAPI)**: The heavy lifter. Runs scans and calls the LLM.
2.  **GitHub App (Node.js)**: The connector. Receives webhooks and posts comments.

---

## 🚀 Option 1: Deploy with Docker (Recommended for VPS/AWS)

We have provided a `docker-compose.yml` file in the root directory.

1.  **Set Environment Variables**:
    Create a `.env` file in the root (where `docker-compose.yml` is) with all your secrets:
    ```env
    GEMINI_API_KEY=your_gemini_key
    APP_ID=12345
    WEBHOOK_SECRET=development
    PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----...-----END RSA PRIVATE KEY-----"
    ```

2.  **Run with Docker Compose**:
    ```bash
    docker-compose up -d --build
    ```

3.  **Expose to Public (Using ngrok)**:
    Since your app is running locally on port 3000, GitHub cannot reach it directly. You need a tunnel.
    
    1.  Install [ngrok](https://ngrok.com/download).
    2.  Run:
        ```bash
        ngrok http 3000
        ```
    3.  Copy the `https` URL provided (e.g., `https://random-id.ngrok-free.app`).
    4.  **Your Webhook URL**: Append `/api/github/webhooks`
        *   Example: `https://random-id.ngrok-free.app/api/github/webhooks`

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

## 🐋 Option 3: Unified Single Service (Best for Costs on Render/Railway)

You can run both the Backend and GitHub App in a **single Docker container** (one service = lower cost). We have provided a unified `Dockerfile` in the root directory for this.

### Steps for Render.com

1.  **Create New Web Service**.
2.  Connect your repository.
3.  **Runtime**: `Docker`.
4.  **Root Directory**: `.` (Leave default).
5.  **Environment Variables**:
    *   `GEMINI_API_KEY`: Your Gemini Key.
    *   `OPENAI_API_KEY`: Your OpenAI Key (Optional).
    *   `LLM_PROVIDER`: `gemini` or `openai`.
    *   `APP_ID`: From GitHub App.
    *   `WEBHOOK_SECRET`: From GitHub App.
    *   `PRIVATE_KEY`: Your .pem file content (use `\n` for newlines if pasting).
    *   `BACKEND_URL`: `http://localhost:8000/api/v1` (Default, no need to change).
    *   `PORT`: `3000` (Default).
6.  **Deploy**.
    *   Render will build the Docker image, processing both Python and Node.js setups.
    *   It will start `supervisord`, which runs both your services.
7.  **Webhook Setup**:
    *   Use the Service URL provided by Render (e.g., `https://ai-guardrails.onrender.com`) for your GitHub App Webhook URL: `https://ai-guardrails.onrender.com/api/github/webhooks`.

### Steps for Railway.app

1.  **New Project** -> **Deploy from GitHub repo**.
2.  Select your `ai-guardrails-enterprise` repository.
3.  **Variables**: Go to the **Variables** tab and add:
    *   `GEMINI_API_KEY`: Your Gemini Key.
    *   `OPENAI_API_KEY`: Your OpenAI Key (Optional).
    *   `LLM_PROVIDER`: `gemini` or `openai`.
    *   `APP_ID`: From GitHub App.
    *   `WEBHOOK_SECRET`: From GitHub App.
    *   `PRIVATE_KEY`: Your .pem file content.
        *   **Note**: Railway handles multi-line variables well. Just paste the private key as is.
    *   `BACKEND_URL`: `http://localhost:8000/api/v1`
4.  **Settings** -> **Networking**:
    *   Railway usually auto-detects port `3000` from the Dockerfile `EXPOSE`.
    *   Generate a **Public Domain** (e.g., `ai-guardrails-production.up.railway.app`).
5.  **Webhook Setup**:
    *   Use the Public Domain + `/api/github/webhooks` for your GitHub App Webhook URL.
    *   Use the Public Domain + `/api/github/webhooks` for your GitHub App Webhook URL.
    *   **Final Verified URL**: `https://ai-guardrails-enterprise-production.up.railway.app/api/github/webhooks`


---


## 🔗 Final Step: Connect GitHub to Real Deployment

Once you have your **Deployed App URL** (e.g., `https://ai-guardrails-app.onrender.com`):

1.  Go to **GitHub Developer Settings -> GitHub Apps -> Your App**.
2.  Find **Webhook URL**.
3.  **Replace** the `smee.io` URL with your new deployed URL.
    *   **Append**: `/api/github/webhooks`
    *   Example: `https://ai-guardrails-app.onrender.com/api/github/webhooks`
4.  **Save Changes**.

**Done!** Your app is now live. You can close your local terminal, and GitHub will send events directly to your cloud deployment.
