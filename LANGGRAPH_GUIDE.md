# SKAX Physical Risk Analyzer - LangGraph Guide

## Overview

This project has been converted to use **LangGraph** for workflow orchestration. LangGraph provides powerful features for parallel execution, state management, and workflow visualization.

## Architecture

### LangGraph Workflow Structure

```
START
  |
  v
[1. Data Collection] (collect_data)
  |
  v
[2. SSP Probability] (calculate_ssp)
  |
  +---> [Parallel Execution: 8 Climate Risks]
  |       |
  |       +---> 3.1 High Temperature (analyze_high_temperature)
  |       +---> 3.2 Cold Wave (analyze_cold_wave)
  |       +---> 3.3 Sea Level Rise (analyze_sea_level_rise) [FROZEN]
  |       +---> 3.4 Drought (analyze_drought)
  |       +---> 3.5 Wildfire (analyze_wildfire)
  |       +---> 3.6 Typhoon (analyze_typhoon)
  |       +---> 3.7 Water Scarcity (analyze_water_scarcity) [FROZEN]
  |       +---> 3.8 Flood (analyze_flood)
  |       |
  +-------|  (All risks complete)
  |
  v
[4. Risk Integration] (integrate_risks)
  |
  v
[5. Report Generation] (generate_report)
  |
  v
END
```

## Key Features

### 1. Parallel Execution
- **Step 3** (8 climate risks) executes in parallel using LangGraph
- Each risk agent runs independently
- Results are accumulated in the shared state
- Automatic synchronization before integration step

### 2. State Management
- **AnalysisState**: Tracks entire workflow state
- Type-safe state updates using TypedDict
- Annotated fields for accumulation (climate_risk_scores, logs, errors)

### 3. Workflow Visualization
- Automatic graph generation using Mermaid
- Visualization file: `workflow_diagram.mmd` with color-coded nodes and labels

## File Structure

```
backend_team/
├── main.py                        # LangGraph-based main orchestrator
├── visualize_workflow.py          # Workflow visualization script
├── workflow/
│   ├── __init__.py
│   ├── state.py                   # State definitions (AnalysisState)
│   ├── nodes.py                   # Node functions for each step
│   └── graph.py                   # Graph construction & visualization
└── workflow_diagram.mmd           # Mermaid workflow diagram
```

## Usage

### Running the Analysis

```python
from main import SKAXPhysicalRiskAnalyzer
from config import Config

# Initialize
config = Config()
analyzer = SKAXPhysicalRiskAnalyzer(config)

# Set target location
target_location = {
    'latitude': 37.5665,
    'longitude': 126.9780,
    'name': 'Seoul, South Korea'
}

# Set analysis parameters
analysis_params = {
    'time_horizon': '2050',
    'analysis_period': '2025-2050'
}

# Run analysis (parallel execution via LangGraph)
results = analyzer.analyze(target_location, analysis_params)

# Visualize workflow
analyzer.visualize("workflow_graph.png")
```

### Visualizing the Workflow

#### Command Line:
```bash
python visualize_workflow.py
```

This generates:
- `workflow_graph.mmd` - Mermaid diagram
- Console output with text-based workflow structure

#### Viewing the Visualization:
1. Open https://mermaid.live
2. Paste the contents of `workflow_diagram.mmd`
3. View the interactive, color-coded workflow diagram

## LangGraph Components

### 1. State (`workflow/state.py`)

```python
class AnalysisState(TypedDict, total=False):
    # Input
    target_location: Dict[str, Any]
    analysis_params: Dict[str, Any]

    # Step outputs
    collected_data: Optional[Dict[str, Any]]
    ssp_probabilities: Optional[Dict[str, float]]
    climate_risk_scores: Annotated[Dict[str, Any], operator.add]
    integrated_risk: Optional[Dict[str, Any]]
    report: Optional[Dict[str, Any]]

    # Control
    current_step: str
    workflow_status: str
```

**Key Points:**
- `Annotated[Dict, operator.add]`: Accumulates results from parallel nodes
- Type-safe state updates
- Tracks workflow progress

### 2. Nodes (`workflow/nodes.py`)

Each step is a node function:
```python
def collect_data_node(state: AnalysisState, config: Any) -> Dict:
    """Node for data collection"""
    agent = DataCollectionAgent(config)
    collected_data = agent.collect(state['target_location'], state['analysis_params'])

    return {
        'collected_data': collected_data,
        'data_collection_status': 'success',
        'logs': ['Data collection completed']
    }
```

**Node Types:**
- `collect_data_node`: Collects climate data
- `calculate_ssp_probabilities_node`: Calculates SSP scenario probabilities
- `analyze_*_node`: 8 parallel risk analysis nodes
- `integrate_risks_node`: Integrates all risks
- `generate_report_node`: Generates final report

### 3. Graph (`workflow/graph.py`)

```python
def create_workflow_graph(config):
    workflow = StateGraph(AnalysisState)

    # Add nodes
    workflow.add_node("collect_data", lambda state: nodes.collect_data_node(state, config))
    workflow.add_node("calculate_ssp", lambda state: nodes.calculate_ssp_probabilities_node(state, config))
    # ... 8 risk nodes
    workflow.add_node("integrate_risks", lambda state: nodes.integrate_risks_node(state, config))
    workflow.add_node("generate_report", lambda state: nodes.generate_report_node(state, config))

    # Add edges (workflow flow)
    workflow.set_entry_point("collect_data")
    workflow.add_edge("collect_data", "calculate_ssp")

    # Parallel edges: SSP -> 8 risks
    workflow.add_edge("calculate_ssp", "analyze_high_temperature")
    # ... 7 more parallel edges

    # Convergence: 8 risks -> integration
    workflow.add_edge("analyze_high_temperature", "integrate_risks")
    # ... 7 more convergence edges

    workflow.add_edge("integrate_risks", "generate_report")
    workflow.add_edge("generate_report", END)

    return workflow.compile()
```

## Benefits of LangGraph

### 1. Parallel Execution
- **Before**: Sequential execution of 8 risk analyses
- **After**: Parallel execution, significantly faster
- Automatic synchronization and state merging

### 2. State Management
- Type-safe state updates
- Automatic state accumulation for parallel nodes
- Clear data flow between steps

### 3. Visualization
- Auto-generated workflow diagrams
- Easy to understand and debug
- Great for documentation and presentations

### 4. Extensibility
- Easy to add new risk types (just add a node and edges)
- Conditional flows (can add decision nodes)
- Error handling and retry logic

### 5. Debugging
- Each node is independently testable
- State snapshots at each step
- Clear execution trace

## Comparison: Basic vs LangGraph

| Feature | Description |
|---------|-------------|
| Execution | Parallel (Step 3: 8 climate risks) |
| State Management | Type-safe AnalysisState with TypedDict |
| Visualization | Auto-generated Mermaid diagrams |
| Extensibility | Add nodes/edges without restructuring |
| Debugging | Easy node-level testing |
| Performance | Fast parallel execution |

## Advanced Usage

### Custom Node Configuration

```python
# Add custom logic to a node
def analyze_drought_node(state: AnalysisState, config: Any) -> Dict:
    agent = DroughtRiskAgent(config)

    # Custom preprocessing
    if state['collected_data'].get('precipitation_data'):
        risk_result = agent.calculate_risk(
            state['collected_data'],
            state['ssp_probabilities']
        )
    else:
        risk_result = {'risk_score': 0.0, 'status': 'no_data'}

    return {
        'climate_risk_scores': {'drought': risk_result},
        'completed_risk_analyses': ['drought']
    }
```

### Conditional Flows

```python
# Add conditional routing
def should_skip_frozen_risks(state: AnalysisState) -> bool:
    return state.get('skip_frozen', False)

workflow.add_conditional_edges(
    "calculate_ssp",
    should_skip_frozen_risks,
    {
        True: "analyze_high_temperature",  # Skip frozen risks
        False: "analyze_sea_level_rise"    # Include all risks
    }
)
```

## Troubleshooting

### Issue: LangGraph not installed
```bash
pip install langgraph langchain langchain-core
```

### Issue: Visualization fails
- Fallback: Mermaid diagram is generated as `.mmd` file
- View online: https://mermaid.live

### Issue: Parallel execution not working
- Check that all risk nodes are connected to `integrate_risks`
- Verify state annotations use `operator.add` for accumulation

## Next Steps

1. **Implement Risk Calculations**: Fill in TODO sections in each risk agent
2. **Add Data Sources**: Connect to actual climate data APIs
3. **Enhance Visualization**: Add progress indicators, metrics
4. **Add Conditional Logic**: Skip frozen risks, handle errors gracefully
5. **Performance Optimization**: Cache results, batch processing

## Resources

- LangGraph Documentation: https://langchain-ai.github.io/langgraph/
- Mermaid Live Editor: https://mermaid.live
- TCFD Guidelines: https://www.fsb-tcfd.org/

## License

(Add license information)
