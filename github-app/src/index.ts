import { Probot } from "probot";
import { handlePullRequest } from "./handlers/pr_handler";

export = (app: Probot) => {
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
    // Probot uses Express under the hood (app.route() gives us the router)
    const router = app.route("/dashboard");
    const auditRouter = app.route("/api/v1/audit");

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
