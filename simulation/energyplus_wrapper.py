"""
EnergyPlus API Wrapper module.
Provides the modular EnergyPlusRunner class using pyenergyplus.api for co-simulation,
sensor telemetry callbacks, and dynamic HVAC actuator control.
"""

import os
import sys
import time
from typing import Dict, Any, Optional, List, Callable

# Check for EnergyPlus installation path in environment or standard macOS Application folder
EP_DIR = os.getenv("ENERGYPLUS_DIR", "/Applications/EnergyPlus")
if os.path.exists(EP_DIR) and EP_DIR not in sys.path:
    sys.path.insert(0, EP_DIR)


# Attempt import of official pyenergyplus API
try:
    # pyrefly: ignore [missing-import]
    from pyenergyplus.api import EnergyPlusAPI
    PYENERGYPLUS_AVAILABLE = True
except ImportError:
    PYENERGYPLUS_AVAILABLE = False
    EnergyPlusAPI = None


class EnergyPlusRunner:
    """
    Modular runner for EnergyPlus simulations using official pyenergyplus API.
    Manages simulation state, handles runtime callbacks, retrieves sensor metrics,
    and dynamically actuates HVAC setpoints.
    """

    def __init__(
        self,
        idf_path: Optional[str] = None,
        epw_path: Optional[str] = None,
        zone_name: str = "ZONE ONE",
    ):
        self.idf_path = idf_path or os.getenv("IDF_FILE_PATH", "data/building.idf")
        self.epw_path = epw_path or os.getenv("EPW_FILE_PATH", "data/weather.epw")
        self.zone_name = zone_name
        self.api_available = PYENERGYPLUS_AVAILABLE

        # Variable & Actuator Handles
        self.handles_initialized = False
        self.handle_temp: int = -1
        self.handle_pmv: int = -1
        self.handle_hvac_power: int = -1
        self.handle_heating_sp_actuator: int = -1
        self.handle_cooling_sp_actuator: int = -1

        # Current State & Setpoints
        self.current_heating_sp: float = 20.0
        self.current_cooling_sp: float = 24.0
        self.latest_metrics: Dict[str, Any] = {
            "zone_temp_c": 22.0,
            "pmv": 0.0,
            "hvac_power_kw": 0.0,
            "timestamp": "",
        }

        # EnergyPlus API & State initialization
        if self.api_available:
            try:
                self.api = EnergyPlusAPI()
                self.state = self.api.state_manager.new_state()
                self._register_callbacks()
                print(f"[EnergyPlusRunner] Initialized EnergyPlus API state successfully.")
            except Exception as e:
                print(f"[EnergyPlusRunner] Failed to initialize EnergyPlus state: {e}")
                self.api_available = False
        else:
            print("[EnergyPlusRunner] pyenergyplus API not available. Operating in simulation fallback mode.")

    def _register_callbacks(self) -> None:
        """Register runtime callbacks with EnergyPlus API."""
        if not self.api_available or not hasattr(self, "api"):
            return

        # Callback before predictor step to intercept metrics and actuate controls
        self.api.runtime.callback_begin_system_timestep_before_predictor(
            self.state, self._begin_system_timestep_callback
        )
        print("[EnergyPlusRunner] Registered 'callback_begin_system_timestep_before_predictor'.")

    def _initialize_handles(self, state: Any) -> None:
        """Fetch and validate EnergyPlus sensor variable and actuator handles."""
        if self.handles_initialized:
            return

        exchange = self.api.exchange

        print("[EnergyPlusRunner] Fetching variable and actuator handles...")

        # 1. Zone Mean Air Temperature Sensor Handle
        self.handle_temp = exchange.get_variable_handle(
            state, "Zone Mean Air Temperature", self.zone_name
        )
        self._check_handle("Zone Mean Air Temperature", self.zone_name, self.handle_temp)

        # 2. Occupant PMV Sensor Handle
        self.handle_pmv = exchange.get_variable_handle(
            state, "Zone Thermal Comfort Fanger Model PMV", self.zone_name
        )
        if self.handle_pmv == -1:
            # Alternate standard key name fallback
            self.handle_pmv = exchange.get_variable_handle(
                state, "Occupant PMV", self.zone_name
            )
        self._check_handle("Occupant PMV / Fanger PMV", self.zone_name, self.handle_pmv)

        # 3. Total HVAC Electric Demand Power Sensor Handle
        self.handle_hvac_power = exchange.get_variable_handle(
            state, "Facility Total HVAC Electric Demand Power", "Whole Building"
        )
        if self.handle_hvac_power == -1:
            self.handle_hvac_power = exchange.get_variable_handle(
                state, "Total HVAC Electric Demand Power", "Whole Building"
            )
        self._check_handle("HVAC Electric Power", "Whole Building", self.handle_hvac_power)

        # 4. Heating Setpoint Actuator Handle
        self.handle_heating_sp_actuator = exchange.get_actuator_handle(
            state, "Zone Temperature Control", "Heating Setpoint", self.zone_name
        )
        self._check_handle("Heating Setpoint Actuator", self.zone_name, self.handle_heating_sp_actuator)

        # 5. Cooling Setpoint Actuator Handle
        self.handle_cooling_sp_actuator = exchange.get_actuator_handle(
            state, "Zone Temperature Control", "Cooling Setpoint", self.zone_name
        )
        self._check_handle("Cooling Setpoint Actuator", self.zone_name, self.handle_cooling_sp_actuator)

        self.handles_initialized = True

    def _check_handle(self, name: str, key: str, handle: int) -> None:
        """Validate handle retrieval and log warnings if missing."""
        if handle == -1:
            print(f"[EnergyPlusRunner] WARNING: Could not find handle for '{name}' (Key: '{key}'). Handle ID: -1")
        else:
            print(f"[EnergyPlusRunner] Successfully retrieved handle for '{name}' (Key: '{key}'): ID {handle}")

    def _begin_system_timestep_callback(self, state: Any) -> None:
        """
        Runtime callback invoked by EnergyPlus at the beginning of each system timestep.
        Intercepts zone metrics and applies queued setpoint actuation values.
        """
        exchange = self.api.exchange

        # Warmup check: skip actuation during building warmup timesteps
        if exchange.warmup_flag(state):
            return

        # Ensure handles are fetched
        if not self.handles_initialized:
            self._initialize_handles(state)

        # 1. Read Zone Mean Air Temperature
        zone_temp = (
            exchange.get_variable_value(state, self.handle_temp)
            if self.handle_temp != -1
            else 22.0
        )

        # 2. Read or Calculate Estimated PMV (Thermal Comfort)
        if self.handle_pmv != -1:
            pmv = exchange.get_variable_value(state, self.handle_pmv)
        else:
            # Approximate PMV: 0.0 at 22°C, +1.0 at 26°C, -1.0 at 18°C
            pmv = (zone_temp - 22.0) * 0.25

        # 3. Read or Calculate Estimated HVAC Power
        if self.handle_hvac_power != -1:
            hvac_power = exchange.get_variable_value(state, self.handle_hvac_power)
        else:
            # Basic load estimation: higher draw when temp exceeds cooling setpoint
            cooling_delta = max(0.0, zone_temp - self.current_cooling_sp)
            hvac_power = 1.2 + (cooling_delta * 1.8) if cooling_delta > 0 else 0.2

        # Timestamp tracking
        month = exchange.month(state)
        day = exchange.day_of_month(state)
        hour = exchange.hour(state)
        minute = exchange.minutes(state)
        timestamp_str = f"M{month:02d}-D{day:02d} {hour:02d}:{minute:02d}"

        self.latest_metrics = {
            "timestamp": timestamp_str,
            "zone_temp_c": round(zone_temp, 2),
            "pmv": round(pmv, 2),
            "hvac_power_kw": round(hvac_power, 2),
            "heating_setpoint": self.current_heating_sp,
            "cooling_setpoint": self.current_cooling_sp,
        }

        # Apply Dynamic Actuation
        if self.handle_heating_sp_actuator != -1:
            exchange.set_actuator_value(
                state, self.handle_heating_sp_actuator, self.current_heating_sp
            )
        if self.handle_cooling_sp_actuator != -1:
            exchange.set_actuator_value(
                state, self.handle_cooling_sp_actuator, self.current_cooling_sp
            )

        # Log Progress Cleanly to stdout
        print(
            f"[EnergyPlus Step {timestamp_str}] Zone: {self.zone_name} | "
            f"Temp: {self.latest_metrics['zone_temp_c']}°C | "
            f"PMV: {self.latest_metrics['pmv']:+.2f} | "
            f"HVAC Power: {self.latest_metrics['hvac_power_kw']} kW | "
            f"Setpoints: [{self.current_heating_sp}°C - {self.current_cooling_sp}°C]"
        )

    def set_hvac_setpoints(self, heating_setpoint: float, cooling_setpoint: float) -> bool:
        """
        Dynamically update HVAC heating and cooling setpoints.
        Validates setpoint range and deadband.
        """
        if heating_setpoint >= cooling_setpoint:
            print(
                f"[EnergyPlusRunner] ERROR: Invalid setpoints. Heating ({heating_setpoint}°C) "
                f"must be less than Cooling ({cooling_setpoint}°C)."
            )
            return False

        self.current_heating_sp = heating_setpoint
        self.current_cooling_sp = cooling_setpoint
        print(
            f"[EnergyPlusRunner] Updated HVAC setpoints for {self.zone_name} -> "
            f"Heating: {heating_setpoint}°C | Cooling: {cooling_setpoint}°C"
        )
        return True

    def run_simulation(self, output_directory: str = "simulation/output") -> int:
        """
        Run complete EnergyPlus simulation using state and runtime API.
        """
        if not self.api_available:
            print("[EnergyPlusRunner] Cannot run full simulation: pyenergyplus API not available.")
            return -1

        if not os.path.exists(self.idf_path):
            print(f"[EnergyPlusRunner] ERROR: IDF file not found at '{self.idf_path}'.")
            return -1

        if not os.path.exists(self.epw_path):
            print(f"[EnergyPlusRunner] ERROR: EPW file not found at '{self.epw_path}'.")
            return -1

        os.makedirs(output_directory, exist_ok=True)
        sys_args = ["-d", output_directory, "-w", self.epw_path, self.idf_path]

        print(f"[EnergyPlusRunner] Launching EnergyPlus simulation: {' '.join(sys_args)}")
        exit_code = self.api.runtime.run_energyplus(self.state, sys_args)
        print(f"[EnergyPlusRunner] Simulation finished with exit code {exit_code}.")
        return exit_code

    def run_step(self, heating_setpoint: float, cooling_setpoint: float) -> Dict[str, Any]:
        """
        Co-simulation step interface for agent interaction.
        Updates setpoints and returns current metrics.
        """
        self.set_hvac_setpoints(heating_setpoint, cooling_setpoint)

        if not self.api_available:
            # Simulated fallback for testing without EnergyPlus binaries
            self.latest_metrics = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "zone_temp_c": round(21.5 + (cooling_setpoint - 24.0) * 0.4, 2),
                "pmv": round((cooling_setpoint - 24.0) * 0.1, 2),
                "hvac_power_kw": round(max(0.5, 4.8 - (cooling_setpoint - 20.0) * 0.5), 2),
                "heating_setpoint": heating_setpoint,
                "cooling_setpoint": cooling_setpoint,
            }

        return self.latest_metrics


# Alias for backward compatibility
EnergyPlusWrapper = EnergyPlusRunner

if __name__ == "__main__":
    print("\n" + "="*60)
    print("Launching Full EnergyPlus Simulation Run...")
    print("="*60)
    
    # 1. Initialize runner with your data paths
    runner = EnergyPlusRunner(
        idf_path="data/baseline.idf",
        epw_path="data/weather.epw",
        zone_name="ZONE ONE"  # Note: Adjust if your IDF uses a different zone name like 'SPACE1-1'
    )
    
    # 2. Run the actual simulation
    exit_code = runner.run_simulation(output_directory="simulation/output")
    
    if exit_code == 0:
        print("\n Simulation completed successfully!")
    else:
        print(f"\n Simulation failed with exit code: {exit_code}")

