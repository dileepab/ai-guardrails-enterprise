
## 🚀 Deployment Information (Reviewers Start Here)

**Production URL**: `https://ai-guardrails-enterprise-production.up.railway.app`

**Webhook URL**: `https://ai-guardrails-enterprise-production.up.railway.app/api/github/webhooks`

**Dashboard URL**: `https://ai-guardrails-enterprise-production.up.railway.app/dashboard`

**Repository**: [https://github.com/dileepab/ai-guardrails-enterprise](https://github.com/dileepab/ai-guardrails-enterprise)

---

# AI Powered Enterprise Guardrails for GitHub Copilot

## Overview
This solution provides an enterprise-grade guardrails system for GitHub Copilot and general development workflows. It integrates deeply with GitHub via a Probot App to enforce:
- **Secure Coding Practices**: Detects secrets, injection flaws, and dangerous patterns.
- **Enterprise Standards**: Enforces coding style and naming conventions.
- **License Compliance**: flags restricted licenses (e.g., GPL) in PRs.
- **AI-Assisted Review**: Utilizes Google Gemini (or OpenAI) to provide contextual, intelligent code reviews beyond static analysis.

## Features
- **Hybrid Analysis Engine**: Combines Static Analysis (Regex/AST) with LLM-based reasoning.
- **Audit Logging**: Comprehensive JSON logs for all scan activities (`backend/audit.log`).
- **Configurable Rules**: Policy-as-Code via `backend/rules/default_rules.yaml`.
- **Copilot Awareness**: Automatically detects AI-generated commits and applies stricter scrutiny.
- **Industry Rule Packs**: Pre-built compliance packs for **Banking (PCI-DSS)**, **Healthcare (HIPAA)**, **Telecom (GDPR)**, and **Government (FedRAMP)**.
- **License Scanning**: Scans dependency files (`package.json`, `requirements.txt`) for prohibited licenses (GPL/AGPL).
- **Compliance Dashboard**: Visual analytics at `/dashboard` with CSV Export, Time Filtering, and Severity Charts.
- **Developer Friendly**: Posts blocking reviews or info comments directly on Pull Requests.

## Repository Structure
- `backend/`: FastAPI-based analysis engine (Python).
- `github-app/`: TypeScript Probot application for GitHub integration.
- `verification/`: Scripts for end-to-end testing without webhooks.

## Setup & Deployment

### Prerequisites
- Python 3.9+
- Node.js 18+
- Google Gemini API Key (or OpenAI Key)

### 1. Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure Environment
# Create .env file with:
LLM_PROVIDER=gemini # Options: "gemini", "openai"
GEMINI_API_KEY=your_gemini_key_here
OPENAI_API_KEY=your_openai_key_here # Optional if using gemini
```

### 2. GitHub App Configuration (Critical)
To enable End-to-End protection, you must register and configure a GitHub App:

1.  **Register App**: Go to [GitHub Developer Settings > GitHub Apps > New GitHub App](https://github.com/settings/apps/new).
    *   **Webhook URL**: Use your Smee URL (e.g., `https://smee.io/your-url`) for local dev.
    *   **Webhook Secret**: Set a secret (e.g., `development`).

2.  **App Permissions** (In "Permissions & events"):
    *   `Pull Requests`: **Read and write** (To post comments)
    *   `Commit statuses`: **Read and write** (To output Red/Green checks)
    *   `Contents`: **Read-only** (To read code)
    *   `Metadata`: **Read-only**
    *   **Subscribe to events**: Check `Pull request`.

3.  **Local Configuration**:
    In `github-app/.env`:
    ```env
    WEBHOOK_PROXY_URL=https://smee.io/your-url
    APP_ID=12345
    PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----...-----END RSA PRIVATE KEY-----"
    WEBHOOK_SECRET=development  # MUST MATCH GitHub App setting
    GITHUB_CLIENT_ID=Iv1...     # From App Settings
    GITHUB_CLIENT_SECRET=962... # From App Settings
    LOG_LEVEL=info
    ```

### 3. Branch Protection (Enforce Blocking)
By default, failing checks do not prevent merging. To enforce:
1.  Go to Repository **Settings -> Branches -> Add branch protection rule**.
2.  Pattern: `main` (or target branch).
3.  Check **"Require status checks to pass before merging"**.
4.  Search for **"AI Guardrails"** (You must run the app once for this to appear).
5.  Select it and Click **Create**.

### 4. Running Locally
Terminal 1 (Backend):
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

Terminal 2 (GitHub App):
```bash
cd github-app
npm install
npm start
```

### 🛡️ Pre-Commit Hook (Local Protection)
To enforce guardrails *before* you even push code, install the local hook:

```bash
./setup-hooks.sh
```

Now, every time you run `git commit`, the system will scan your staged changes. If it finds **BLOCKING** violations (like secrets or Copilot-generated errors), the commit will be rejected immediately.

## Usage
1.  Install the GitHub App on your repository.
2.  Open a Pull Request.
3.  The system automatically scans changed files and posts review comments.


## ⚙️ Configuration Guide

### Enabling Industry Rule Packs
To enforce specific compliance standards, create an `.ai-guardrails.yaml` file in your repository root:

```yaml
# Options: default, banking, healthcare, telecom, government
rule_pack: "healthcare" 

# Enforcement Mode: advisory, warning, or blocking
enforcement_mode: "blocking"
```

### Copilot Detection
The system automatically flags commits as **AI-Generated** if the commit message contains:
- `Co-authored-by: Copilot`
- `Generated by Copilot`

These commits are logged specifically in the audit trail for "AI vs Human" compliance tracking.


## Architecture
[GitHub Mock Event] -> [GitHub App (TS)] -> [Backend API (Python)] -> [Hybrid Engine]
                                                                        |-> [Static Analysis Service]
                                                                        |-> [LLM Service (Gemini)]
                                                                        |-> [Rule Engine]
                                                                        |-> [Audit Logger]
