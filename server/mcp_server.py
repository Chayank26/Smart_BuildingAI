"""
Model Context Protocol (MCP) Server for Autonomous Smart Building Control.
Exposes MCP tool endpoints for real-time telemetry querying, HVAC setpoint updates,
and grid carbon intensity monitoring to LLM agents.
"""

import os
import sys
from dotenv import load_dotenv
# pyrefly: ignore [missing-import]
from mcp.server.fastmcp import FastMCP

from tools import (
    get_building_telemetry,
    update_hvac_setpoint,
    get_grid_carbon_intensity,
    TelemetryResponse,
    UpdateSetpointResponse,
    CarbonIntensityResponse,
)

load_dotenv()

# Initialize FastMCP Server
mcp = FastMCP(
    "Smart Building Autonomous Control Server",
    instructions=(
        "You are an AI Smart Building Energy Manager. Use these MCP tools to monitor zone "
        "telemetry, check grid carbon intensity, and optimize HVAC setpoints within safe "
        "comfort bounds (18°C - 26°C)."
    )
)


@mcp.tool()
def read_telemetry(zone_id: str = "Zone_1") -> dict:
    """
    Get current zone temperature, indoor air quality (CO2 ppm), PMV thermal comfort index, and HVAC power consumption.

    Args:
        zone_id: Target thermal zone identifier (e.g. 'Zone_1', 'Zone_2')

    Returns:
        Dictionary containing zone metrics, occupancy count, humidity, and active setpoints.
    """
    telemetry: TelemetryResponse = get_building_telemetry(zone_id)
    return telemetry.model_dump()


@mcp.tool()
def update_setpoint(zone_id: str, cooling_setpoint: float, heating_setpoint: float) -> dict:
    """
    Update HVAC heating and cooling setpoints for a specified zone.
    Enforces safe comfort bounds (18.0°C - 26.0°C) and deadband validation.

    Args:
        zone_id: Target thermal zone identifier (e.g. 'Zone_1')
        cooling_setpoint: Target cooling setpoint in Celsius (18.0°C to 26.0°C)
        heating_setpoint: Target heating setpoint in Celsius (18.0°C to 26.0°C)

    Returns:
        Status response object indicating 'success' or 'error' and confirmed setpoint values.
    """
    response: UpdateSetpointResponse = update_hvac_setpoint(
        zone_id=zone_id,
        cooling_setpoint=cooling_setpoint,
        heating_setpoint=heating_setpoint
    )
    return response.model_dump()


@mcp.tool()
def read_grid_carbon_intensity() -> dict:
    """
    Get real-time simulated electric grid carbon intensity (gCO2/kWh).
    Use this to execute demand response or load-shifting strategies when grid intensity is high.

    Returns:
        Dictionary containing carbon intensity value (gCO2/kWh), timestamp, and grid status.
    """
    carbon_info: CarbonIntensityResponse = get_grid_carbon_intensity()
    return carbon_info.model_dump()


if __name__ == "__main__":
    print("Starting Smart Building Autonomous Control MCP Server...")
    mcp.run()
