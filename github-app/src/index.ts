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
    // We mount on the root ("/") so that the paths (/dashboard, /api/v1/audit) are NOT stripped by Express.
    // createProxyMiddleware will only match the paths in the filter list.
    const router = (app as any).getRouter("/");

    const { createProxyMiddleware } = require('http-proxy-middleware');
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';
    // Ensure backendUrl doesn't have a path suffix if we want 1:1 mapping

    const proxyOptions = {
        target: backendUrl,
        changeOrigin: true,
        pathRewrite: {
            // Force preservation of paths. 
            // The key '^/dashboard' -> value '/dashboard' tells it to rewrite /dashboard to /dashboard (no-op)
            // But sometimes the library strips it BEFORE this config if mounted on a subpath.
            // Since we mounted on "/", it shouldn't strip. 
            // However, this explicit map safeguards it.
            '^/dashboard': '/dashboard',
            '^/api/v1/audit': '/api/v1/audit'
        },
        logger: console
    };

    router.use(createProxyMiddleware(['/dashboard', '/api/v1/audit'], proxyOptions));
};
