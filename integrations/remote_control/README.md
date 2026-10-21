# IM 19 Codespaces Remote Control (MCP)

This is a restricted MCP server scaffold for a Codespaces workspace. It is **not yet connected to ChatGPT**. It exposes a small fixed toolset and has no deployment, push, merge, arbitrary-shell, secret-read, or workflow-edit tool.

## Security model

- Run the MCP server using stdio inside the Codespace.
- For ChatGPT, use OpenAI **Secure MCP Tunnel** if your ChatGPT workspace and Platform organization are eligible and authorized. The tunnel client and MCP server must run where the workspace can reach them. Do not expose a public Codespaces port for this server.
- Tools currently exposed: \`workspace_status\`, \`read_project_file\`, \`run_unit_tests\`, \`apply_unified_patch\`.
- File reads are allowlisted and size-limited. Patch paths are limited to \`integrations/rag/\`, \`tests/\`, \`scripts/\`, and \`docs/\`.
- Patches are rejected on \`main\`, \`master\`, \`production\`, or \`prod\`; writes require an \`agent/*\` or \`work/*\` branch.
- No arbitrary command execution, credentials access, git push, merge, or deployment is exposed.
- Patch application is not a commit. Inspect \`git diff\`, run tests, and use a human-reviewed pull request to land changes.

## Install in Codespaces

From the repository root:

\`\`\`bash
python -m venv .venv-remote
source .venv-remote/bin/activate
python -m pip install --upgrade pip
python -m pip install -r integrations/remote_control/requirements.txt
\`\`\`

Use a dedicated branch before allowing patch tools:

\`\`\`bash
git switch -c agent/chatgpt-work
git status --short --branch
\`\`\`

If the branch already exists, inspect it and switch to it rather than deleting it.

## Run locally / inspect tools

\`\`\`bash
IM19_WORKSPACE="$PWD" python -m integrations.remote_control.server
\`\`\`

The process speaks MCP over stdio. A normal shell will appear to wait because stdio is the protocol transport; use an MCP client to inspect/call the tools.

## Secure MCP Tunnel and ChatGPT eligibility

ChatGPT cannot connect directly to a local stdio process. Secure MCP Tunnel provides an outbound-only path, but setup requires a tunnel created in the correct OpenAI Platform organization, a runtime API key with tunnel-use permissions, and a ChatGPT workspace that supports custom MCP apps. Current OpenAI documentation says full custom MCP actions in ChatGPT are available to Business and Enterprise/Edu; Pro is limited to read/fetch; Free accounts should not assume custom MCP access. Confirm current availability in the ChatGPT web UI.

Official documentation:
- https://developers.openai.com/api/docs/guides/secure-mcp-tunnels
- https://help.openai.com/en/articles/12584461-connecting-custom-mcp-servers-in-chatgpt

### Secure Tunnel setup checklist

1. In the OpenAI Platform, create/manage a Secure MCP Tunnel and note the tunnel ID. Do not put runtime API keys in Git.
2. Install the supported \`openai/tunnel-client\` release according to its official onboarding docs. Review \`tunnel-client help quickstart\` and \`tunnel-client doctor --explain\`.
3. Configure its local MCP target to launch this stdio server using the current Codespaces Python environment.
4. Store the runtime API key in the Codespace secret/environment, not in shell history, repository files, or chat. Run the tunnel client and verify it reports ready/active polling.
5. In ChatGPT web, add a custom MCP app, select **Tunnel**, select the matching tunnel ID, configure the required authentication, and review the listed tools.
6. Test \`workspace_status\` first, then \`read_project_file\` on a non-secret file, then \`run_unit_tests\`. Test patch application only on a disposable \`agent/*\` branch.
7. Verify that a patch to \`main\`, a path such as \`.env\`, an arbitrary command, and a deployment request are all unavailable/rejected.

Do not claim the integration is active until a real tool call from ChatGPT succeeds.

## QR code clarification

A QR code is not an authentication method for ChatGPT's MCP connection. The MCP connection is configured in ChatGPT and OpenAI Platform. A QR pairing dashboard can be added separately for a human mobile approval console, but it must use short-lived one-time codes, authenticated sessions, and server-side authorization. This scaffold does not generate QR codes or expose an unauthenticated pairing endpoint.
