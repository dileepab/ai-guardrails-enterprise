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

    // Proxy Dashboard & Audit API to Python Backend
    // We mount on the root ("/") to preserve paths.
    // createProxyMiddleware with filter list handles the routing.
    const router = getRouter("/");

    const { createProxyMiddleware } = require('http-proxy-middleware');
    const backendUrl = (process.env.BACKEND_URL || 'http://localhost:8000').replace(/\/$/, '');
    // Strips trailing slash if present

    // 1. Dashboard Proxy
    // Mounted on /dashboard. Express strips '/dashboard', so req.url becomes '/'.
    // We set target to include '/dashboard' so it reconstructs the correct upstream URL.
    const dashboardProxy = createProxyMiddleware({
        target: `${backendUrl}/dashboard`,
        changeOrigin: true,
        logger: console,
        pathRewrite: { '^/$': '' } // Remove potential double slash if any, but mainly purely rely on target
    });

    // 2. Audit API Proxy
    // Mounted on /api/v1/audit.
    const auditProxy = createProxyMiddleware({
        target: `${backendUrl}/api/v1/audit`,
        changeOrigin: true,
        logger: console,
        pathRewrite: { '^/$': '' }
    });

    router.use('/dashboard', dashboardProxy);
    router.use('/api/v1/audit', auditProxy);
};
