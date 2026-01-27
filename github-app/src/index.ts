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
};
