"""Read-only MCP adapter for the private ThermoWorks RFX Cloud Run service."""
import os
from datetime import datetime, timezone

import httpx
import google.auth.transport.requests
from google.oauth2 import id_token
from mcp.server.fastmcp import FastMCP

BRIDGE_URL = os.environ.get(
    "RFX_BRIDGE_URL",
    "https://thermoworks-rfx-933426864321.us-east4.run.app",
).rstrip("/")
PORT = int(os.environ.get("PORT", "8080"))

mcp = FastMCP(
    "ThermoWorks RFX",
    host="0.0.0.0",
    port=PORT,
    stateless_http=True,
    json_response=True,
)


@mcp.tool()
async def get_rfx_temperatures() -> dict:
    """Get the latest ThermoWorks RFX probe and ambient temperatures, including freshness.

    Stale values are historical readings and must not be presented as live.
    This tool only reads data and cannot change any ThermoWorks settings.
    """
    try:
        request = google.auth.transport.requests.Request()
        token = id_token.fetch_id_token(request, BRIDGE_URL)
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(
                f"{BRIDGE_URL}/temperatures",
                headers={"Authorization": f"Bearer {token}"},
            )
            response.raise_for_status()
            return response.json()
    except Exception as exc:
        # Do not leak tokens or request details in MCP errors.
        return {
            "error": "Unable to retrieve RFX temperatures",
            "error_type": type(exc).__name__,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
