"use strict";
const pr_handler_1 = require("./handlers/pr_handler");
module.exports = (app) => {
    app.log.info("App loaded! Waiting for webhooks...");
    app.on("pull_request.opened", async (context) => {
        await (0, pr_handler_1.handlePullRequest)(context);
    });
    app.on("pull_request.synchronize", async (context) => {
        await (0, pr_handler_1.handlePullRequest)(context);
    });
};
