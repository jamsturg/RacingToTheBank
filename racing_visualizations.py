import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import List, Dict
import numpy as np
import networkx as nx

class RacingVisualizations:
    @staticmethod
    def create_speed_map(runners: List[Dict]) -> go.Figure:
        """Create interactive speed map visualization"""
        positions = ['Inside', 'Mid', 'Outside']
        sections = ['Early', 'Middle', 'Late']
        
        # Create position matrix
        position_matrix = np.random.randint(1, len(runners) + 1, (len(positions), len(sections)))
        
        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=position_matrix,
            x=sections,
            y=positions,
            colorscale='Viridis',
            showscale=False
        ))
        
        # Add runner annotations
        for i, runner in enumerate(runners, 1):
            positions = np.where(position_matrix == i)
            if len(positions[0]) > 0:
                fig.add_annotation(
                    x=sections[positions[1][0]],
                    y=positions[0][0],
                    text=f"{i}. {runner['runnerName']}",
                    showarrow=False
                )
        
        fig.update_layout(
            title="Predicted Running Positions",
            xaxis_title="Race Section",
            yaxis_title="Track Position",
            height=400
        )
        
        return fig

    @staticmethod
    def create_track_bias(track_data: Dict) -> go.Figure:
        """Create track bias visualization"""
        sections = ['0-400m', '400-800m', '800-1200m', '1200m+']
        positions = ['Inside', 'Middle', 'Outside']
        
        bias_matrix = np.random.uniform(0, 1, (len(positions), len(sections)))
        
        fig = go.Figure(data=go.Heatmap(
            z=bias_matrix,
            x=sections,
            y=positions,
            colorscale='RdYlGn',
            showscale=True
        ))
        
        fig.update_layout(
            title="Track Bias Analysis",
            xaxis_title="Race Section",
            yaxis_title="Track Position",
            height=400
        )
        
        return fig

    @staticmethod
    def create_odds_movement(odds_history: List[Dict]) -> go.Figure:
        """Create odds movement chart"""
        df = pd.DataFrame(odds_history)
        
        fig = go.Figure()
        
        for runner in df['runner'].unique():
            runner_data = df[df['runner'] == runner]
            fig.add_trace(go.Scatter(
                x=runner_data['timestamp'],
                y=runner_data['odds'],
                name=runner,
                mode='lines+markers'
            ))
        
        fig.update_layout(
            title="Odds Movement",
            xaxis_title="Time",
            yaxis_title="Fixed Odds ($)",
            height=400,
            legend_title="Runners"
        )
        
        return fig

    @staticmethod
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
        
        # Create edge trace
        edge_x = []
        edge_y = []
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
            
        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=0.5, color='#888'),
            hoverinfo='none',
            mode='lines'
        )

        # Create node trace
        node_x = []
        node_y = []
        node_text = []
        for node in G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            node_text.append(node)
            
        node_trace = go.Scatter(
            x=node_x, y=node_y,
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
            text=node_text,
            textposition="top center"
        )

        # Create figure
        fig = go.Figure(data=[edge_trace, node_trace],
                     layout=go.Layout(
                         showlegend=False,
                         hovermode='closest',
                         margin=dict(b=20,l=5,r=5,t=40),
                         title="Race Connections Network"
                     ))
                     
        return fig

    @staticmethod
    def create_form_radar(runner_stats: Dict) -> go.Figure:
        """Create runner form radar chart"""
        categories = ['Speed', 'Form', 'Class', 'Distance', 'Track']
        
        fig = go.Figure(data=go.Scatterpolar(
            r=[
                runner_stats.get('speed_rating', 0),
                runner_stats.get('form_rating', 0),
                runner_stats.get('class_rating', 0),
                runner_stats.get('distance_rating', 0),
                runner_stats.get('track_rating', 0)
            ],
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
            showlegend=False,
            height=400
        )
        
        return fig
