# Smart Building AI - Autonomous Control System

An end-to-end Python framework for autonomous smart building management, integrating EnergyPlus simulation co-simulation, Model Context Protocol (MCP) server control tools, intelligent setpoint optimization agents, and an interactive Streamlit dashboard.

---

## 📁 Project Layout

```
Smart_BuildingAI/
├── data/                       # Building (.idf) and weather (.epw) input files
│   └── README.md               # Instructions for placing simulation data
├── server/                     # Model Context Protocol (MCP) tool integration
│   ├── __init__.py
│   ├── mcp_server.py           # FastMCP server exposing building tools
│   └── tools.py                # Pydantic schemas and tool handlers
├── simulation/                 # Co-simulation and agent decision logic
│   ├── __init__.py
│   ├── energyplus_wrapper.py   # EnergyPlus API wrapper & state bridge
│   └── agent.py                # Autonomous agent control policies
├── dashboard/                  # Interactive Streamlit monitoring dashboard
│   ├── __init__.py
│   └── app.py                  # Real-time telemetry & Plotly charts
├── .env                        # Active environment configuration
├── .env.example                # Template for environment variables
├── .gitignore                  # Git ignore rules for virtualenv & E+ outputs
├── requirements.txt            # Python dependencies
└── README.md                   # Project documentation
```

---

## 🚀 Quick Start Guide

### 1. Prerequisites & Virtual Environment

Create and activate a Python virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### 2. Environment Configuration

Copy `.env.example` to `.env` and fill in your API keys and EnergyPlus path settings:

```bash
cp .env.example .env
```

### 3. Run the MCP Server

Start the Model Context Protocol server to expose building control tools to LLMs and agents:

```bash
python -m server.mcp_server
```

### 4. Run the EnergyPlus Simulation Agent

Run the autonomous agent step execution:

```bash
python -m simulation.agent
```

### 5. Launch the Streamlit Dashboard

Run the Streamlit monitoring and control interface:

```bash
streamlit run dashboard/app.py
```

Open `http://localhost:8501` in your browser.
