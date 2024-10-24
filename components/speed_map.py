import streamlit as st
import plotly.graph_objects as go
import pandas as pd

def create_speed_map_key():
    """Create speed map key section with detailed explanations"""
    st.markdown('''
        <div class="speed-map-key">
            <h3>Speed Map Key</h3>
            <div class="speed-map-grid">
                <div class="speed-map-tile blue">
                    <h4>Favoured Position</h4>
                    <p>The darkest Blue shade indicates the most favoured Map Position for runners</p>
                </div>
                <div class="speed-map-tile pink">
                    <h4>Unfavoured Position</h4>
                    <p>The darkest Pink shade indicates the least favoured Map Position</p>
                </div>
            </div>
            
            <div class="speed-map-section">
                <h4>SPEED</h4>
                <p>Runner's Early Speed Rank (1 fastest, descending). Green = Rank 1-4, White = Rank 5-8, Red = Rank 9+</p>
            </div>
            
            <div class="speed-map-section">
                <h4>MAP A2E</h4>
                <p>Map Position performance. Above 1.00 indicates over-performance (Blue), below 1.00 indicates under-performance (Pink)</p>
            </div>
            
            <div class="speed-map-section">
                <h4>SETTLE</h4>
                <p>Runner's Average Historical Settle Position Ranking. This is based on the runner's historical settle position as a percentage of field size, ranked against the other runners in today's race.</p>
            </div>
            
            <div class="speed-map-section">
                <h4>JOCKEY</h4>
                <p>The Jockey A2E performance is calculated using the Jockey's last 100 (L100) rides. An up arrow indicates their L100 A2E performance is better than their career A2E.</p>
            </div>
            
            <div class="speed-map-section">
                <h4>PRICE</h4>
                <p>PF AI Price. Each runner's Price is AI generated before the upcoming race market opens, using fundamental factors only, no market factors are included.</p>
            </div>
        </div>
    ''', unsafe_allow_html=True)

def create_speed_map(form_data: pd.DataFrame) -> go.Figure:
    """Create enhanced speed map visualization with color coding"""
    if form_data.empty:
        return go.Figure()

    # Show Key toggle
    show_key = st.checkbox("Show Speed Map Key", value=False)
    if show_key:
        create_speed_map_key()

    # Calculate speed ranks and settle positions
    form_data['SpeedRank'] = form_data['Rating'].rank(ascending=False)
    form_data['SettleRank'] = form_data['Barrier'].rank()

    # Create figure
    fig = go.Figure()

    # Add horse markers with color coding
    for _, row in form_data.iterrows():
        # Determine colors based on ranks
        speed_color = '#90EE90' if row['SpeedRank'] <= 4 else '#FFFFFF' if row['SpeedRank'] <= 8 else '#FFB6C1'
        map_color = f'rgba(204, 230, 255, {min(float(row["Rating"])/100, 1)})' if row['Rating'] >= 70 else \
                   f'rgba(255, 204, 230, {min(1 - float(row["Rating"])/100, 1)})'

        # Create hover text with A2E and L100 info
        hover_text = f"""
            <b>{row['Number']}. {row['Horse']}</b><br>
            Speed Rank: {int(row['SpeedRank'])}<br>
            Settle Position: {int(row['SettleRank'])}<br>
            Map A2E: {row.get('map_a2e', 'N/A')}<br>
            Jockey L100: {row.get('jockey_l100', 'N/A')}<br>
            PF AI Price: ${row.get('pf_price', 'N/A')}
        """

        # Add marker
        fig.add_trace(go.Scatter(
            x=[row['Barrier']],
            y=[1],
            mode='markers+text',
            text=[row['Number']],
            textposition='middle center',
            marker=dict(
                size=50,
                color=map_color,
                line=dict(color=speed_color, width=2),
                symbol='square'
            ),
            name=row['Horse'],
            hovertemplate=hover_text,
            showlegend=False
        ))

    # Update layout
    fig.update_layout(
        title="Speed Map Analysis",
        xaxis_title="Barrier",
        yaxis_title="",
        yaxis_showticklabels=False,
        plot_bgcolor='white',
        height=600,
        margin=dict(t=50, b=50, l=50, r=50)
    )

    # Configure axes
    fig.update_xaxes(
        gridcolor='lightgrey',
        gridwidth=1,
        range=[-1, max(form_data['Barrier']) + 1]
    )

    fig.update_yaxes(
        range=[0, 2],
        showgrid=False
    )

    return fig
