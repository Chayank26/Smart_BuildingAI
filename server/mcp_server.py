"""
Model Context Protocol (MCP) Server for Smart Building AI.
Provides MCP tool integration using Python MCP SDK.
"""

import os
import sys
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from server.tools import get_building_telemetry, set_thermostat_setpoint

load_dotenv()

# Initialize FastMCP Server
mcp = FastMCP("Smart Building Control Server")


@mcp.tool()
def read_telemetry(zone_id: str = "Zone_1") -> str:
    """Get real-time sensor telemetry for a building zone including temperature, humidity, power, and setpoints."""
    data = get_building_telemetry(zone_id)
    return str(data)


@mcp.tool()
def update_setpoints(zone_id: str, heating_setpoint: float, cooling_setpoint: float) -> str:
    """Set thermostat heating and cooling setpoints for a building thermal zone."""
    result = set_thermostat_setpoint(zone_id, heating_setpoint, cooling_setpoint)
    return str(result)


if __name__ == "__main__":
    print("Starting Smart Building MCP Server...")
    mcp.run()
