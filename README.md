---

## 🎉 Project Overview & Completion

The **Autonomous AI Agent for Smart Building Energy Management** is now fully operational end-to-end!

### 🧱 Core Architecture & Pipeline
1. **Physics & Building Simulation Engine (`simulation/energyplus_wrapper.py`)**  
   Integrates directly with the **EnergyPlus C-API** to step through thermal dynamics in real time, serving live zone temperatures, PMV comfort indices, and HVAC power consumption.

2. **Model Context Protocol Server (`server/mcp_server.py`)**  
   Implements a FastMCP tool server providing standard API endpoints (`get_building_telemetry`, `update_hvac_setpoint`, `get_grid_carbon_intensity`) for LLM interaction.

3. **Autonomous Agentic Supervisory Loop (`simulation/agent_controller.py`)**  
   A closed-loop agent that continuously monitors telemetry, detects comfort breaches or high-carbon grid signals, and autonomously invokes MCP tool calls to adjust setpoints while minimizing latency via smart step skipping.

4. **Real-time Analytics Dashboard (`dashboard/app.py`)**  
   A Streamlit dashboard rendering live run history, setpoint adjustments, power demand profiles, and total carbon saved.

---

### 💻 Quick Start Command

To run the complete system from the project root:

```bash
# 1. Run the Closed-Loop Agent Simulation
PYTHONPATH=/Applications/EnergyPlus:. python simulation/agent_controller.py

# 2. Launch the Streamlit Analytics Dashboard
PYTHONPATH=/Applications/EnergyPlus:. streamlit run dashboard/app.py