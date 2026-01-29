import { Probot } from "probot";
import { handlePullRequest } from "./handlers/pr_handler";

export = (app: Probot, { getRouter }: any) => {
    app.log.info("App loaded! Waiting for webhooks...");

    app.on("pull_request.opened", async (context) => {
        await handlePullRequest(context);
    });

    app.on("pull_request.synchronize", async (context) => {
        await handlePullRequest(context);
    });

    app.on("pull_request.reopened", async (context) => {
        await handlePullRequest(context);
    });

    // Endpoint for Python Backend to trigger Admin Override (Internal Localhost Only)
    const router = getRouter("/");
    router.use(require("express").json());
    router.post("/api/override", async (req: any, res: any) => {
        try {
            const { repo_full_name, commit_sha, reason } = req.body;
            app.log.info(`Received Admin Override for ${repo_full_name} @ ${commit_sha}`);

            const [owner, repo] = repo_full_name.split("/");

            // 1. Get Installation ID for this repo
            // Authenticate as App (JWT) to find installation
            const jwtOctokit = await app.auth();
            const installation = await jwtOctokit.apps.getRepoInstallation({ owner, repo });

            // 2. Authenticate as Installation
            const octokit = await app.auth(installation.data.id);

            // 3. Post "Success" Status
            await octokit.repos.createCommitStatus({
                owner,
                repo,
                sha: commit_sha,
                state: "success",
                description: `Admin Override: ${reason || "Manual Approval"}`,
                context: "AI Guardrails", // Must match the context used by the bot (Case Sensitive!)
                target_url: `${process.env.PUBLIC_URL || (process.env.RAILWAY_PUBLIC_DOMAIN ? `https://${process.env.RAILWAY_PUBLIC_DOMAIN}` : "http://localhost:8000")}/dashboard`
            });

            res.json({ status: "ok", message: "Override applied" });
        } catch (error: any) {
            app.log.error(error);
            res.status(500).json({ error: error.message });
        }
    });

    // Proxy Dashboard & Audit API to Python Backend (Legacy/Dev - In Prod Python is Gateway)
    // We keep this just in case verified logic relies on it, but it's largely unused in current Prod setup.
    const routerProxy = getRouter("/");

    const { createProxyMiddleware } = require('http-proxy-middleware');
    // On Railway BACKEND_URL includes /api/v1, but we need the base root for the dashboard.
    // So we strip '/api/v1' suffix effectively.
    let backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';
    backendUrl = backendUrl.replace(/\/api\/v1\/?$/, '').replace(/\/$/, '');

    // 1. Dashboard Proxy
    const dashboardProxy = createProxyMiddleware({
        target: `${backendUrl}/dashboard`,
        changeOrigin: true,
        logger: console,
        pathRewrite: { '^/$': '' }
    });

    // 2. Audit API Proxy
    const auditProxy = createProxyMiddleware({
        target: `${backendUrl}/api/v1/audit`,
        changeOrigin: true,
        logger: console,
        pathRewrite: { '^/$': '' }
    });

    routerProxy.use('/dashboard', dashboardProxy);
    routerProxy.use('/api/v1/audit', auditProxy);
};
