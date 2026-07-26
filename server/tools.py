"""
Building Control MCP Tools implementation.
Defines functions and Pydantic schemas for telemetry querying, HVAC setpoint updates,
and grid carbon intensity monitoring for LLM agent integration.
"""

import time
import math
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator


class TelemetryResponse(BaseModel):
    """Schema for building sensor telemetry response."""
    zone_id: str = Field(..., description="Target thermal zone identifier")
    indoor_temperature_c: float = Field(..., description="Zone mean air temperature in Celsius")
    indoor_air_quality_co2_ppm: float = Field(..., description="Indoor CO2 concentration in parts per million (ppm)")
    pmv_thermal_comfort: float = Field(..., description="Predicted Mean Vote (PMV) thermal comfort index (-3.0 to +3.0)")
    hvac_power_kw: float = Field(..., description="Total HVAC electrical power consumption in kW")
    humidity_percent: float = Field(..., description="Relative indoor humidity percentage")
    occupancy_count: int = Field(..., description="Current occupant count in the zone")
    heating_setpoint_c: float = Field(..., description="Active heating setpoint in Celsius")
    cooling_setpoint_c: float = Field(..., description="Active cooling setpoint in Celsius")
    timestamp: str = Field(..., description="Telemetry sample timestamp")


class UpdateSetpointInput(BaseModel):
    """Schema for HVAC setpoint update requests."""
    zone_id: str = Field(default="Zone_1", description="Target zone identifier (e.g., 'Zone_1')")
    cooling_setpoint: float = Field(..., description="Cooling setpoint in Celsius (18.0°C to 26.0°C)")
    heating_setpoint: float = Field(..., description="Heating setpoint in Celsius (18.0°C to 26.0°C)")

    @field_validator("cooling_setpoint", "heating_setpoint")
    @classmethod
    def validate_bounds(cls, v: float) -> float:
        if not (18.0 <= v <= 26.0):
            raise ValueError(f"Setpoint {v}°C is out of safe comfort bounds (18.0°C - 26.0°C).")
        return v


class UpdateSetpointResponse(BaseModel):
    """Schema for setpoint update status response."""
    status: str = Field(..., description="'success' or 'error'")
    zone_id: str = Field(..., description="Target zone identifier")
    updated_cooling_setpoint: float = Field(..., description="Confirmed cooling setpoint (°C)")
    updated_heating_setpoint: float = Field(..., description="Confirmed heating setpoint (°C)")
    message: str = Field(..., description="Status summary message")


class CarbonIntensityResponse(BaseModel):
    """Schema for real-time electric grid carbon intensity."""
    timestamp: str = Field(..., description="Current simulation or system timestamp")
    carbon_intensity_gco2_kwh: float = Field(..., description="Grid carbon intensity in gCO2/kWh")
    grid_status: str = Field(..., description="Grid state: 'Low Carbon', 'Moderate', or 'High Carbon Peak'")


# Shared in-memory building state for server tools
_BUILDING_STATE: Dict[str, Dict[str, Any]] = {
    "Zone_1": {
        "indoor_temperature_c": 22.4,
        "indoor_air_quality_co2_ppm": 450.0,
        "pmv_thermal_comfort": +0.12,
        "hvac_power_kw": 4.25,
        "humidity_percent": 48.0,
        "occupancy_count": 12,
        "heating_setpoint_c": 20.0,
        "cooling_setpoint_c": 24.0,
    },
    "Zone_2": {
        "indoor_temperature_c": 23.1,
        "indoor_air_quality_co2_ppm": 510.0,
        "pmv_thermal_comfort": +0.28,
        "hvac_power_kw": 3.80,
        "humidity_percent": 50.0,
        "occupancy_count": 8,
        "heating_setpoint_c": 20.0,
        "cooling_setpoint_c": 24.0,
    }
}


def get_building_telemetry(zone_id: str = "Zone_1") -> TelemetryResponse:
    """
    Query real-time sensor telemetry for a specified building zone.
    Returns zone temperature, indoor air quality (CO2 ppm), PMV comfort index, and HVAC power.
    """
    target_zone = zone_id if zone_id in _BUILDING_STATE else "Zone_1"
    data = _BUILDING_STATE[target_zone]

    return TelemetryResponse(
        zone_id=target_zone,
        indoor_temperature_c=data["indoor_temperature_c"],
        indoor_air_quality_co2_ppm=data["indoor_air_quality_co2_ppm"],
        pmv_thermal_comfort=data["pmv_thermal_comfort"],
        hvac_power_kw=data["hvac_power_kw"],
        humidity_percent=data["humidity_percent"],
        occupancy_count=data["occupancy_count"],
        heating_setpoint_c=data["heating_setpoint_c"],
        cooling_setpoint_c=data["cooling_setpoint_c"],
        timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
    )


def update_hvac_setpoint(zone_id: str, cooling_setpoint: float, heating_setpoint: float) -> UpdateSetpointResponse:
    """
    Validate and apply HVAC thermostat setpoint changes to active building simulation.
    Enforces safe comfort bounds (18.0°C - 26.0°C) and deadband constraints.
    """
    # 1. Bounds Validation (18.0°C to 26.0°C)
    if not (18.0 <= heating_setpoint <= 26.0):
        return UpdateSetpointResponse(
            status="error",
            zone_id=zone_id,
            updated_cooling_setpoint=cooling_setpoint,
            updated_heating_setpoint=heating_setpoint,
            message=f"Heating setpoint {heating_setpoint}°C outside safe bounds [18.0°C, 26.0°C]."
        )

    if not (18.0 <= cooling_setpoint <= 26.0):
        return UpdateSetpointResponse(
            status="error",
            zone_id=zone_id,
            updated_cooling_setpoint=cooling_setpoint,
            updated_heating_setpoint=heating_setpoint,
            message=f"Cooling setpoint {cooling_setpoint}°C outside safe bounds [18.0°C, 26.0°C]."
        )

    # 2. Deadband Validation
    if heating_setpoint >= cooling_setpoint:
        return UpdateSetpointResponse(
            status="error",
            zone_id=zone_id,
            updated_cooling_setpoint=cooling_setpoint,
            updated_heating_setpoint=heating_setpoint,
            message=f"Heating setpoint ({heating_setpoint}°C) must be strictly less than cooling setpoint ({cooling_setpoint}°C)."
        )

    # 3. Apply state update
    target_zone = zone_id if zone_id in _BUILDING_STATE else "Zone_1"
    _BUILDING_STATE[target_zone]["heating_setpoint_c"] = heating_setpoint
    _BUILDING_STATE[target_zone]["cooling_setpoint_c"] = cooling_setpoint

    # Simulate HVAC power response adjustment
    power_delta = (24.0 - cooling_setpoint) * 0.4
    _BUILDING_STATE[target_zone]["hvac_power_kw"] = round(max(0.5, 4.0 + power_delta), 2)

    return UpdateSetpointResponse(
        status="success",
        zone_id=target_zone,
        updated_cooling_setpoint=cooling_setpoint,
        updated_heating_setpoint=heating_setpoint,
        message=f"Successfully updated HVAC setpoints for {target_zone} to Heating: {heating_setpoint}°C, Cooling: {cooling_setpoint}°C."
    )


def get_grid_carbon_intensity() -> CarbonIntensityResponse:
    """
    Retrieve real-time electric grid carbon intensity (gCO2/kWh).
    Simulates diurnal carbon intensity curves based on time of day (high during peak hours, lower during solar hours).
    """
    current_hour = time.localtime().tm_hour
    # Diurnal carbon curve simulation: peak around 17:00 (5 PM), trough around 12:00 (noon solar)
    base_intensity = 250.0
    diurnal_variation = 100.0 * math.sin((current_hour - 8) / 24.0 * 2 * math.pi)
    carbon_intensity = round(max(100.0, base_intensity + diurnal_variation), 1)

    if carbon_intensity < 200.0:
        grid_status = "Low Carbon (High Renewable Generation)"
    elif carbon_intensity < 320.0:
        grid_status = "Moderate Carbon Intensity"
    else:
        grid_status = "High Carbon Peak (Demand Response Recommended)"

    return CarbonIntensityResponse(
        timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
        carbon_intensity_gco2_kwh=carbon_intensity,
        grid_status=grid_status,
    )
