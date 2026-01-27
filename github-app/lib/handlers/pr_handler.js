"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.handlePullRequest = void 0;
const axios_1 = __importDefault(require("axios"));
const handlePullRequest = async (context) => {
    const pr = context.payload.pull_request;
    const repo = context.repo();
    context.log.info(`Processing PR #${pr.number}`);
    // 1. Fetch changed files
    const filesResponse = await context.octokit.pulls.listFiles({
        owner: repo.owner,
        repo: repo.repo,
        pull_number: pr.number,
    });
    const filesToScan = filesResponse.data.map((f) => ({
        filename: f.filename,
        content: f.patch || "", // In a real app, we might fetch full content if patch is insufficient
        patch: f.patch,
    }));
    if (filesToScan.length === 0) {
        context.log.info("No files to scan.");
        return;
    }
    // Fetch config override if exists
    let configOverride;
    try {
        const configResponse = await context.octokit.repos.getContent({
            owner: repo.owner,
            repo: repo.repo,
            path: ".ai-guardrails.yaml",
            ref: pr.head.sha
        });
        if ('content' in configResponse.data && !Array.isArray(configResponse.data)) {
            configOverride = Buffer.from(configResponse.data.content, 'base64').toString();
        }
    }
    catch (e) {
        // No config found, ignore
    }
    // 1.5 Set Pending Status
    await context.octokit.repos.createCommitStatus({
        owner: repo.owner,
        repo: repo.repo,
        sha: pr.head.sha,
        state: "pending",
        context: "AI Guardrails",
        description: "Scanning for violations..."
    });
    // 2. Call Backend API
    try {
        const backendUrl = process.env.BACKEND_URL || "http://127.0.0.1:8000/api/v1";
        const response = await axios_1.default.post(`${backendUrl}/scan`, {
            repo_full_name: `${repo.owner}/${repo.repo}`,
            pr_number: pr.number,
            commit_sha: pr.head.sha,
            files: filesToScan,
            config_override: configOverride,
            is_copilot_generated: false // TODO: Detection Logic
        });
        const scanResult = response.data;
        // 3. Post Feedback & Status
        await context.octokit.repos.createCommitStatus({
            owner: repo.owner,
            repo: repo.repo,
            sha: pr.head.sha,
            state: scanResult.succeeded ? "success" : "failure",
            context: "AI Guardrails",
            description: scanResult.summary.substring(0, 140) // GitHub limit
        });
        if (scanResult.violations.length > 0) {
            // Post review comments
            const comments = scanResult.violations.map(v => ({
                path: v.file_path,
                line: v.line_number,
                body: `**[${v.severity}] ${v.rule_id}**: ${v.message}\n\n${v.suggestion ? `Suggestion: \`${v.suggestion}\`` : ""}`
            }));
            // Group into a review
            // Note: GitHub limit is approx 80 comments per review.
            // For prototype we'll take top 10 to avoid limits.
            const reviewComments = comments.slice(0, 10);
            try {
                await context.octokit.pulls.createReview({
                    owner: repo.owner,
                    repo: repo.repo,
                    pull_number: pr.number,
                    event: scanResult.succeeded ? "COMMENT" : "REQUEST_CHANGES",
                    body: `## Guardrails Scan Results\n\n**Mode**: ${scanResult.enforcement_mode}\n\n${scanResult.summary}\n\n${scanResult.succeeded ? "✅ Checks Passed" : "❌ Blocking Issues Found"}`,
                    comments: reviewComments
                });
            }
            catch (reviewError) {
                context.log.warn(`Failed to post review comments (likely line mismatch): ${reviewError.message}`);
                // Fallback: Post as a general comment without line references
                await context.octokit.issues.createComment({
                    owner: repo.owner,
                    repo: repo.repo,
                    issue_number: pr.number,
                    body: `## Guardrails Scan Results (General)\n\n**Mode**: ${scanResult.enforcement_mode}\n\n${scanResult.summary}\n\n${scanResult.succeeded ? "✅ Checks Passed" : "❌ Blocking Issues Found"}\n\n*(Note: Could not post inline comments due to line resolution errors. Please check the logs for details.)*`
                });
            }
        }
        else {
            // Post success comment
            await context.octokit.issues.createComment({
                owner: repo.owner,
                repo: repo.repo,
                issue_number: pr.number,
                body: "## Guardrails Scan passed! ✅\nNo issues found.",
            });
        }
    }
    catch (error) {
        context.log.error(error, "Failed to scan code");
        // Set Failure Status on Error
        await context.octokit.repos.createCommitStatus({
            owner: repo.owner,
            repo: repo.repo,
            sha: pr.head.sha,
            state: "error",
            context: "AI Guardrails",
            description: "Scan failed due to internal error."
        });
        await context.octokit.issues.createComment({
            owner: repo.owner,
            repo: repo.repo,
            issue_number: pr.number,
            body: "⚠️ Guardrails Scan failed due to an internal error.",
        });
    }
};
exports.handlePullRequest = handlePullRequest;
