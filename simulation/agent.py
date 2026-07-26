"""
Autonomous Building Control Agent.
Performs smart setpoint adjustments based on weather forecast, occupancy, and energy demand.
"""

from typing import Dict, Any
from simulation.energyplus_wrapper import EnergyPlusWrapper


class AutonomousBuildingAgent:
    """Agent that optimizes HVAC setpoints to balance comfort and energy efficiency."""

    def __init__(self, wrapper: EnergyPlusWrapper):
        self.wrapper = wrapper
        self.default_heating = 20.0
        self.default_cooling = 24.0

    def compute_optimal_setpoints(self, telemetry: Dict[str, Any]) -> Dict[str, float]:
        """Determine optimal setpoints using rule-based/predictive policy."""
        outdoor_temp = telemetry.get("outdoor_temp_c", 25.0)
        
        # Demand-response adjustment: widen deadband during high outdoor temperatures
        if outdoor_temp > 30.0:
            cooling_target = 25.5
            heating_target = 19.5
        elif outdoor_temp < 10.0:
            cooling_target = 23.5
            heating_target = 21.0
        else:
            cooling_target = self.default_cooling
            heating_target = self.default_heating

        return {
            "heating_setpoint": heating_target,
            "cooling_setpoint": cooling_target
        }

    def execute_control_loop(self) -> Dict[str, Any]:
        """Execute a single control step: sample state -> optimize -> actuate."""
        # 1. Get current building state
        current_state = self.wrapper.run_step(self.default_heating, self.default_cooling)
        
        # 2. Compute optimized setpoints
        optimal_setpoints = self.compute_optimal_setpoints(current_state)
        
        # 3. Actuate via wrapper
        updated_state = self.wrapper.run_step(
            heating_setpoint=optimal_setpoints["heating_setpoint"],
            cooling_setpoint=optimal_setpoints["cooling_setpoint"]
        )
        
        return {
            "status": "active",
            "decision": optimal_setpoints,
            "state": updated_state
        }


if __name__ == "__main__":
    wrapper = EnergyPlusWrapper()
    agent = AutonomousBuildingAgent(wrapper)
    result = agent.execute_control_loop()
    print("Agent Step Output:", result)
