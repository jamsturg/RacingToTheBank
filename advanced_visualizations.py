import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from typing import List, Dict
import networkx as nx

class RacingVisualizations:
    def create_horse_network(self, race_data: Dict):
        """Create interactive network visualization of horse relationships"""
        G = nx.Graph()
        
        # Add nodes for each horse
        for runner in race_data['runners']:
            G.add_node(runner['runnerName'], 
                      type='horse',
                      odds=runner.get('fixedOdds', {}).get('returnWin', 0))
            
            # Add connections to jockey and trainer
            G.add_node(runner.get('jockey', 'Unknown'), type='jockey')
            G.add_node(runner.get('trainer', 'Unknown'), type='trainer')
            
            G.add_edge(runner['runnerName'], runner.get('jockey', 'Unknown'))
            G.add_edge(runner['runnerName'], runner.get('trainer', 'Unknown'))
        
        # Create positions for visualization
        pos = nx.spring_layout(G)
        
        # Create Plotly traces
        edge_trace = go.Scatter(
            x=[], y=[],
            line=dict(width=0.5, color='#888'),
            hoverinfo='none',
            mode='lines')

        node_trace = go.Scatter(
            x=[], y=[],
            mode='markers+text',
            hoverinfo='text',
            marker=dict(
                showscale=True,
                colorscale='YlOrRd',
                size=20,
                colorbar=dict(
                    thickness=15,
                    title='Odds',
                    xanchor='left',
                    titleside='right'
                )
            ),
            text=[],
            textposition="top center"
        )

        # Add edges to trace
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_trace['x'] += (x0, x1, None)
            edge_trace['y'] += (y0, y1, None)

        # Add nodes to trace
        for node in G.nodes():
            x, y = pos[node]
            node_trace['x'] += (x,)
            node_trace['y'] += (y,)
            node_trace['text'] += (node,)

        # Create figure
        fig = go.Figure(data=[edge_trace, node_trace],
                     layout=go.Layout(
                         showlegend=False,
                         hovermode='closest',
                         margin=dict(b=20,l=5,r=5,t=40),
                         title="Race Connections Network"
                     ))
                     
        return fig

    def create_form_spiral(self, runner_data: Dict):
        """Create spiral visualization of runner form"""
        if 'formComments' not in runner_data:
            return None
            
        form = runner_data['formComments']
        
        # Calculate spiral coordinates
        theta = np.linspace(0, 6*np.pi, len(form))
        r = np.linspace(1, 10, len(form))
        x = r * np.cos(theta)
        y = r * np.sin(theta)
        
        # Create figure
        fig = go.Figure()
        
        # Add spiral path
        fig.add_trace(go.Scatter(
            x=x, y=y,
            mode='lines+markers',
            marker=dict(
                size=10,
                color=[f['position'] for f in form],
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title='Position')
            ),
            text=[f"{f['date']}: {f['position']}/{f['totalRunners']}" for f in form],
            hoverinfo='text'
        ))
        
        fig.update_layout(
            title=f"Form History: {runner_data['runnerName']}",
            showlegend=False,
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
        )
        
        return fig

    def create_race_tree(self, race_data: Dict):
        """Create hierarchical tree visualization of race structure"""
        fig = go.Figure()
        
        def add_level(parent, items, level, x_offset=0):
            spacing = 1 / (len(items) + 1)
            for i, item in enumerate(items, 1):
                y = level
                x = x_offset + i * spacing
                
                # Add node
                fig.add_trace(go.Scatter(
                    x=[x], y=[y],
                    mode='markers+text',
                    text=[item['name']],
                    textposition='top center',
                    marker=dict(size=20),
                    showlegend=False
                ))
                
                # Add connection to parent
                if parent is not None:
                    fig.add_trace(go.Scatter(
                        x=[parent[0], x],
                        y=[parent[1], y],
                        mode='lines',
                        line=dict(color='gray'),
                        showlegend=False
                    ))
                
                # Add children
                if 'children' in item:
                    add_level((x, y), item['children'], level-1, x_offset)
        
        # Create tree structure
        tree = {
            'name': race_data['meeting']['venueName'],
            'children': [
                {
                    'name': f"Race {race_data['raceNumber']}",
                    'children': [
                        {'name': r['runnerName']}
                        for r in race_data['runners']
                    ]
                }
            ]
        }
        
        add_level(None, [tree], 3)
        
        fig.update_layout(
            title="Race Structure",
            showlegend=False,
            height=600,
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
        )
        
        return fig

    def create_performance_radar(self, performance_data: Dict):
        """Create radar chart of performance metrics"""
        categories = list(performance_data.keys())
        values = list(performance_data.values())
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=categories,
            fill='toself'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )
            ),
            showlegend=False
        )
        
        return fig

    def create_odds_flow(self, odds_history: List[Dict]):
        """Create Sankey diagram of odds movement"""
        fig = go.Figure(data=[go.Sankey(
            node = dict(
                pad = 15,
                thickness = 20,
                line = dict(color = "black", width = 0.5),
                label = ["Opening", "Mid", "Current"],
                color = "blue"
            ),
            link = dict(
                source = [0, 0, 1, 1],
                target = [1, 2, 1, 2],
                value = [1, 2, 1, 3]
            )
        )])
        
        fig.update_layout(
            title_text="Odds Flow",
            font_size=10
        )
        
        return fig
