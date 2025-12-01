"""
Graph Structure Verification Script
"""
from ai_agent.config.settings import Config
from ai_agent.workflow.graph import create_workflow_graph

config = Config()
graph = create_workflow_graph(config)

# Get all nodes
nodes = list(graph.get_graph().nodes.keys())
print('Total Nodes:', len(nodes))
print('Nodes:', sorted(nodes))

# Get all edges
edges = graph.get_graph().edges
print('\nTotal Edges:', len(edges))
print('\nForward Edges (solid):')
for edge in edges:
    if edge[0] != '__start__' and edge[1] != '__end__':
        print(f'  {edge[0]} --> {edge[1]}')

print('\nChecking for vulnerability_analysis node...')
if 'vulnerability_analysis' in nodes:
    print('  [ERROR] vulnerability_analysis node still exists!')
else:
    print('  [OK] vulnerability_analysis node removed')

print('\nChecking for building_characteristics node...')
if 'building_characteristics' in nodes:
    print('  [OK] building_characteristics node exists')
else:
    print('  [ERROR] building_characteristics node missing!')

print('\nValidation conditional edges:')
validation_edges = [e for e in edges if e[0] == 'validation']
for edge in validation_edges:
    print(f'  validation --> {edge[1]}')
