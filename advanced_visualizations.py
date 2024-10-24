```python
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from typing import List, Dict
import streamlit as st
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

class AnimatedVisualizations:
    def create_race_animation(self, race_data: Dict):
        """Create animated race visualization"""
        frames = []
        
        # Create base figure
        fig = go.Figure(
            data=[go.Scatter(x=[0], y=[0])],
            layout=go.Layout(
                xaxis=dict(range=[0, 100]),
                yaxis=dict(range=[0, 10]),
                title="Race Progress"
            ),
            frames=frames
        )
        
        # Add animation controls
        fig.update_layout(
            updatemenus=[{
                'buttons': [
                    {
                        'args': [None, {'frame': {'duration': 500, 'redraw': True}}],
                        'label': 'Play',
                        'method': 'animate'
                    }
                ],
                'direction': 'left',
                'pad': {'r': 10, 't': 87},
                'showactive': False,
                'type': 'buttons',
                'x': 0.1,
                'xanchor': 'right',
                'y': 0,
                'yanchor': 'top'
            }]
        )
        
        return fig

class BettingStrategies:
    def __init__(self):
        self.strategies = {
            'value_betting': self.value_betting_strategy,
            'dutching': self.dutching_strategy,
            'hedging': self.hedging_strategy,
            'kelly_criterion': self.kelly_criterion_strategy
        }

    def value_betting_strategy(self, race_data: Dict, bank: float) -> List[Dict]:
        """Implement value betting strategy"""
        bets = []
        for runner in race_data['runners']:
            true_prob = self._calculate_true_probability(runner)
            market_odds = runner.get('fixedOdds', {}).get('returnWin', 0)
            
            if market_odds > 0:
                market_prob = 1 / market_odds
                if true_prob > market_prob:
                    value = (true_prob * market_odds) - 1
                    stake = self._calculate_kelly_stake(
                        true_prob, market_odds, bank
                    )
                    
                    bets.append({
                        'runner': runner['runnerName'],
                        'stake': stake,
                        'odds': market_odds,
                        'expected_value': value
                    })
        
        return sorted(bets, key=lambda x: x['expected_value'], reverse=True)

    def dutching_strategy(
        self,
        race_data: Dict,
        target_return: float
    ) -> List[Dict]:
        """Implement dutching strategy"""
        selected_runners = []
        total_probability = 0
        
        # Select runners with positive expected value
        for runner in race_data['runners']:
            true_prob = self._calculate_true_probability(runner)
            market_odds = runner.get('fixedOdds', {}).get('returnWin', 0)
            
            if market_odds > 0:
                market_prob = 1 / market_odds
                if true_prob > market_prob:
                    selected_runners.append({
                        'runner': runner['runnerName'],
                        'probability': true_prob,
                        'odds': market_odds
                    })
                    total_probability += true_prob
        
        # Calculate stakes for target return
        bets = []
        if selected_runners and total_probability < 1:
            total_stake = target_return / (1 - total_probability)
            
            for runner in selected_runners:
                stake = total_stake * runner['probability']
                bets.append({
                    'runner': runner['runner'],
                    'stake': stake,
                    'odds': runner['odds'],
                    'return': stake * runner['odds']
                })
        
        return bets

    def hedging_strategy(
        self,
        current_bets: List[Dict],
        current_odds: Dict
    ) -> List[Dict]:
        """Implement hedging strategy"""
        hedge_bets = []
        
        for bet in current_bets:
            potential_profit = bet['stake'] * bet['odds']
            other_runners = [
                r for r in current_odds['runners']
                if r['runnerNumber'] != bet['runner_number']
            ]
            
            # Calculate hedging stakes
            total_hedge_stake = 0
            for runner in other_runners:
                if 'fixedOdds' in runner:
                    hedge_stake = (potential_profit - bet['stake']) / runner['fixedOdds']['returnWin']
                    total_hedge_stake += hedge_stake
                    
                    hedge_bets.append({
                        'runner': runner['runnerNumber'],
                        'stake': hedge_stake,
                        'odds': runner['fixedOdds']['returnWin']
                    })
        
        return hedge_bets

    def kelly_criterion_strategy(
        self,
        probability: float,
        odds: float,
        bank: float
    ) -> float:
        """Implement Kelly Criterion betting strategy"""
        q = 1 - probability
        p = probability
        b = odds - 1
        
        if p * b > q:
            stake = (p * b - q) / b * bank
            return min(stake, bank * 0.1)  # Limit to 10% of bank
        
        return 0

    def _calculate_true_probability(self, runner: Dict) -> float:
        """Calculate true winning probability"""
        # This would use the machine learning model in production
        return np.random.random()  # Placeholder

    def _calculate_kelly_stake(
        self,
        probability: float,
        odds: float,
        bank: float
    ) -> float:
        """Calculate optimal stake using Kelly Criterion"""
        return self.kelly_criterion_strategy(probability, odds, bank)

class AdvancedStatistics:
    def calculate_performance_metrics(
        self,
        runner_data: Dict
    ) -> Dict:
        """Calculate comprehensive performance metrics"""
        if 'formComments' not in runner_data:
            return {}
            
        form = runner_data['formComments']
        
        return {
            'win_rate': self._calculate_win_rate(form),
            'place_rate': self._calculate_place_rate(form),
            'roi': self._calculate_roi(form),
            'consistency': self._calculate_consistency(form),
            'class_progression': self._calculate_class_progression(form),
            'distance_performance': self._calculate_distance_performance(form),
            'track_stats': self._calculate_track_stats(form)
        }

    def _calculate_win_rate(self, form: List[Dict]) -> float:
        """Calculate win rate percentage"""
        wins = sum(1 for race in form if race['position'] == 1)
        return (wins / len(form)) * 100 if form else 0

    def _calculate_place_rate(self, form: List[Dict]) -> float:
        """Calculate place rate percentage"""
        places = sum(1 for race in form if race['position'] <= 3)
        return (places / len(form)) * 100 if form else 0

    def _calculate_roi(self, form: List[Dict]) -> float:
        """Calculate Return on Investment"""
        if not form:
            return 0
            
        investment = len(form) * 10  # Assuming $10 win bets
        returns = sum(
            100 / race['totalRunners'] if race['position'] == 1 else 0
            for race in form
        )
        
        return ((returns - investment) / investment) * 100

    def _calculate_consistency(self, form: List[Dict]) -> float:
        """Calculate consistency rating"""
        if not form:
            return 0
            
        positions = [race['position'] for race in form]
        return 100 - (np.std(positions) * 10)