"""
Building Control MCP Tools implementation.
Defines functions for telemetry querying, setpoint updates, and HVAC controls.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class SetpointRequest(BaseModel):
    zone_id: str = Field(..., description="Target thermal zone ID (e.g. 'Zone_1')")
    heating_setpoint: float = Field(..., description="Heating setpoint in Celsius (e.g. 20.0)")
    cooling_setpoint: float = Field(..., description="Cooling setpoint in Celsius (e.g. 24.0)")


class TelemetryResponse(BaseModel):
    zone_id: str
    indoor_temperature: float
    outdoor_temperature: float
    humidity: float
    hvac_power_kw: float
    occupancy_count: int
    heating_setpoint: float
    cooling_setpoint: float


# Simulated in-memory state for building control tools
_BUILDING_STATE: Dict[str, Dict[str, Any]] = {
    "Zone_1": {
        "indoor_temperature": 22.5,
        "outdoor_temperature": 30.1,
        "humidity": 48.0,
        "hvac_power_kw": 4.2,
        "occupancy_count": 12,
        "heating_setpoint": 20.0,
        "cooling_setpoint": 24.0,
    },
    "Zone_2": {
        "indoor_temperature": 23.1,
        "outdoor_temperature": 30.1,
        "humidity": 50.0,
        "hvac_power_kw": 3.8,
        "occupancy_count": 8,
        "heating_setpoint": 20.0,
        "cooling_setpoint": 24.0,
    }
}


def get_building_telemetry(zone_id: Optional[str] = None) -> Dict[str, Any]:
    """Retrieve real-time building sensor telemetry."""
    if zone_id and zone_id in _BUILDING_STATE:
        return {"zone_id": zone_id, **_BUILDING_STATE[zone_id]}
    return _BUILDING_STATE


def set_thermostat_setpoint(zone_id: str, heating_setpoint: float, cooling_setpoint: float) -> Dict[str, Any]:
    """Update heating and cooling thermostat setpoints for a specified zone."""
    if zone_id not in _BUILDING_STATE:
        return {"status": "error", "message": f"Zone '{zone_id}' not found."}
    
    if heating_setpoint >= cooling_setpoint:
        return {
            "status": "error",
            "message": "Heating setpoint must be strictly lower than cooling setpoint."
        }

    _BUILDING_STATE[zone_id]["heating_setpoint"] = heating_setpoint
    _BUILDING_STATE[zone_id]["cooling_setpoint"] = cooling_setpoint
    
    return {
        "status": "success",
        "zone_id": zone_id,
        "updated_heating_setpoint": heating_setpoint,
        "updated_cooling_setpoint": cooling_setpoint
    }
