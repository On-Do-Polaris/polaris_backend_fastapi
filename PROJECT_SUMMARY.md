# SKAX Physical Risk Analyzer - Project Summary

## Overview

SKAX 물리적 리스크 분석 에이전트 - LangGraph 기반 기후 변화 리스크 분석 시스템

## Final Project Structure

```
backend_team/
├── main.py                          # Main orchestrator (LangGraph-based)
├── visualize_workflow.py            # Workflow visualization tool
│
├── agents/                          # Agent modules
│   ├── __init__.py
│   ├── data_collection_agent.py     # Step 1: Data collection
│   ├── ssp_probability_calculator.py # Step 2: SSP scenario probabilities
│   ├── base_climate_risk_agent.py   # Base class for climate risks
│   ├── climate_risk_agents/         # Step 3: 8 climate risk agents
│   │   ├── __init__.py
│   │   ├── high_temperature_risk_agent.py
│   │   ├── cold_wave_risk_agent.py
│   │   ├── sea_level_rise_risk_agent.py (FROZEN)
│   │   ├── drought_risk_agent.py
│   │   ├── wildfire_risk_agent.py
│   │   ├── typhoon_risk_agent.py
│   │   ├── water_scarcity_risk_agent.py (FROZEN)
│   │   └── flood_risk_agent.py
│   ├── risk_integration_agent.py    # Step 4: Risk integration
│   └── report_generation_agent.py   # Step 5: Report generation
│
├── workflow/                        # LangGraph workflow
│   ├── __init__.py
│   ├── state.py                     # State definitions (AnalysisState)
│   ├── nodes.py                     # Node functions
│   └── graph.py                     # Graph construction & visualization
│
├── config/                          # Configuration
│   ├── __init__.py
│   └── settings.py                  # Settings and config classes
│
├── workflow_diagram.mmd             # Mermaid workflow diagram
├── requirements.txt                 # Python dependencies
├── .env.example                     # Environment variables template
├── README.md                        # Main documentation
├── LANGGRAPH_GUIDE.md              # LangGraph implementation guide
└── PROJECT_SUMMARY.md              # This file
```

## Key Files

### Core Files

- **[main.py](main.py)**: Main entry point with `SKAXPhysicalRiskAnalyzer` class
- **[visualize_workflow.py](visualize_workflow.py)**: Workflow visualization script
- **[requirements.txt](requirements.txt)**: Python package dependencies

### Workflow (LangGraph)

- **[workflow/state.py](workflow/state.py)**: TypedDict state definitions
- **[workflow/nodes.py](workflow/nodes.py)**: 13 node functions (1 data collection + 1 SSP + 8 risks + 1 integration + 1 report + 1 end)
- **[workflow/graph.py](workflow/graph.py)**: Graph construction and visualization utilities

### Agents

- **Data Collection**: [agents/data_collection_agent.py](agents/data_collection_agent.py)
- **SSP Calculator**: [agents/ssp_probability_calculator.py](agents/ssp_probability_calculator.py)
- **Climate Risks** (8 agents in [agents/climate_risk_agents/](agents/climate_risk_agents/)):
  1. High Temperature
  2. Cold Wave (+ Snow)
  3. Sea Level Rise (FROZEN)
  4. Drought
  5. Wildfire
  6. Typhoon
  7. Water Scarcity (FROZEN)
  8. Flood
- **Integration**: [agents/risk_integration_agent.py](agents/risk_integration_agent.py)
- **Reporting**: [agents/report_generation_agent.py](agents/report_generation_agent.py)

### Configuration

- **[config/settings.py](config/settings.py)**: Configuration classes (Config, DevelopmentConfig, ProductionConfig, TestConfig)
- **[.env.example](.env.example)**: Environment variables template

### Documentation

- **[README.md](README.md)**: Project overview and usage guide
- **[LANGGRAPH_GUIDE.md](LANGGRAPH_GUIDE.md)**: Detailed LangGraph implementation guide
- **[workflow_diagram.mmd](workflow_diagram.mmd)**: Mermaid workflow visualization

## Workflow Structure

```
START
  ↓
[1. Data Collection]
  ↓
[2. SSP Probability] (ssp1-2.6, ssp2-4.5, ssp3-7.0, ssp5-8.5)
  ↓
[3. 8 Climate Risks] ← PARALLEL EXECUTION
  ├─ High Temperature
  ├─ Cold Wave (+ Snow)
  ├─ Sea Level Rise (FROZEN)
  ├─ Drought
  ├─ Wildfire
  ├─ Typhoon
  ├─ Water Scarcity (FROZEN)
  └─ Flood
  ↓
[4. Risk Integration] (H × E × V)
  ↓
[5. Report Generation]
  ↓
END
```

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Run Analysis

```python
from main import SKAXPhysicalRiskAnalyzer
from config import Config

# Initialize
config = Config()
analyzer = SKAXPhysicalRiskAnalyzer(config)

# Analyze
results = analyzer.analyze(
    target_location={'latitude': 37.5665, 'longitude': 126.9780, 'name': 'Seoul'},
    analysis_params={'time_horizon': '2050', 'analysis_period': '2025-2050'}
)
```

### Visualize Workflow

```bash
python visualize_workflow.py
```

View the generated `workflow_diagram.mmd` at https://mermaid.live

## Technology Stack

- **Python 3.8+**
- **LangGraph**: Workflow orchestration and parallel execution
- **LangChain**: Supporting libraries
- **NumPy/Pandas**: Data processing
- **Mermaid**: Workflow visualization

## Key Features

1. **LangGraph Workflow**
   - Parallel execution of 8 climate risk analyses
   - Type-safe state management
   - Auto-generated workflow diagrams

2. **Modular Architecture**
   - Each risk is an independent agent
   - Easy to extend with new risks
   - Clear separation of concerns

3. **Risk Calculation**
   - Formula: Risk Score = Hazard × Exposure × Vulnerability
   - SSP scenario weighting
   - Compound risk analysis

4. **Visualization**
   - Mermaid diagrams with color coding
   - Text-based workflow structure
   - Easy to understand and present

## Implementation Status

- ✅ Project structure
- ✅ LangGraph workflow integration
- ✅ All agent skeletons
- ✅ State management
- ✅ Workflow visualization
- ⚠️ Data collection logic (TODO)
- ⚠️ Risk calculation algorithms (TODO)
- ⚠️ Report generation implementation (TODO)
- ❄️ Sea Level Rise (FROZEN)
- ❄️ Water Scarcity (FROZEN)

## Next Steps

1. Implement data collection APIs
2. Fill in risk calculation algorithms
3. Implement report generation
4. Add unit tests
5. Performance optimization
6. Add error handling and retry logic

## Environment Variables

Create a `.env` file based on `.env.example`:

```env
ENVIRONMENT=development
CLIMATE_API_URL=https://api.climate.example.com
CLIMATE_API_KEY=your_api_key
GEOGRAPHIC_API_URL=https://api.geo.example.com
GEOGRAPHIC_API_KEY=your_api_key
DEBUG=True
```

## Documentation

- **Main README**: [README.md](README.md)
- **LangGraph Guide**: [LANGGRAPH_GUIDE.md](LANGGRAPH_GUIDE.md)
- **Workflow Diagram**: [workflow_diagram.mmd](workflow_diagram.mmd)

## License

(To be added)

## Contributors

(To be added)

---

**Last Updated**: 2025-11-05
**Version**: 1.0.0
