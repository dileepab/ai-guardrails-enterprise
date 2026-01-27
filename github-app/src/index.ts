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
    // In Probot v12+, getRouter is passed in the second argument options object
    const router = getRouter("/dashboard");
    const auditRouter = getRouter("/api/v1/audit");

    // We need to use 'http-proxy-middleware' manually if Probot doesn't expose full express app easily,
    // BUT Probot's getRouter() allows standard express handlers.

    const { createProxyMiddleware } = require('http-proxy-middleware');
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8123/api/v1';
    // Remove /api/v1 suffix for the base target if needed, but our BACKEND_URL includes it.
    // Let's assume BACKEND_URL = http://localhost:8123/api/v1
    // We want /dashboard -> http://localhost:8123/dashboard

    const targetBase = backendUrl.replace('/api/v1', ''); // http://localhost:8123

    const proxyOptions = {
        target: targetBase,
        changeOrigin: true,
        pathRewrite: {
            '^/dashboard': '/dashboard',
            '^/api/v1/audit': '/api/v1/audit'
        },
        logger: console
    };

    router.use(createProxyMiddleware(proxyOptions));
    auditRouter.use(createProxyMiddleware(proxyOptions));
};
