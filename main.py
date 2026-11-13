import os
from datetime import datetime, timezone

import httpx
from fastapi import FastAPI, HTTPException

app = FastAPI(
    title="ThermoWorks RFX Bridge",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

THERMOWORKS_URL = "https://cloud.thermoworks.com/api/v1/devices"


def parse_time(value):
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def freshness(timestamp, snapshot):
    recorded = parse_time(timestamp)
    if recorded is None:
        return "no_data", None

    age_minutes = max(
        0, (snapshot - recorded).total_seconds() / 60
    )

    if age_minutes <= 3:
        state = "current"
    elif age_minutes <= 10:
        state = "delayed"
    else:
        state = "stale"

    return state, round(age_minutes, 1)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/temperatures")
async def temperatures():
    api_key = os.environ.get("THERMOWORKS_API_KEY")

    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="ThermoWorks credential not configured",
        )

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(
                THERMOWORKS_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                },
            )
            response.raise_for_status()
            data = response.json()

    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"ThermoWorks returned HTTP {exc.response.status_code}",
        )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"ThermoWorks connection error: {type(exc).__name__}",
        )

    snapshot = datetime.now(timezone.utc)
    if snapshot is None:
        raise HTTPException(
            status_code=502,
            detail="Invalid ThermoWorks snapshot",
        )

    devices = []

    for device in data.get("devices", []):
        channels = []

        for channel in device.get("channels", []):
            state, age = freshness(
                channel.get("lastTelemetrySaved"),
                snapshot,
            )

            value = channel.get("value")
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                value = round(value, 1)

            channels.append({
                "number": channel.get("number"),
                "label": channel.get("label"),
                "temperature": value,
                "units": channel.get("units"),
                "status": channel.get("status"),
                "freshness": state,
                "age_minutes": age,
                "last_reading": channel.get("lastTelemetrySaved"),
            })

        devices.append({
            "name": device.get("label"),
            "model": device.get("model"),
            "channels": channels,
        })

    return {
        "generated_at": data.get("generatedAt"),
        "devices": devices,
    }
