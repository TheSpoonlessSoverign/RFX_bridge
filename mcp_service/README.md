# ThermoWorks RFX MCP adapter

Read-only MCP endpoint for ChatGPT. Deploy this folder as a **separate** Cloud Run service using Python buildpacks, build context `/mcp_service`, and entrypoint `python main.py`.

Runtime service account: `thermoworks-mcp@thermoworks-bridge.iam.gserviceaccount.com`.

The service calls the existing authenticated `thermoworks-rfx` service using a Google-signed ID token. Do not place Google credentials or ThermoWorks API keys in the repository.

MCP endpoint: `/mcp`. The service has one read-only tool: `get_rfx_temperatures`.

**Access warning:** If deployed with unauthenticated invocation, anyone with its URL can query the MCP tool. Do not expose additional tools or sensitive data without adding authentication.
