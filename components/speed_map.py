import plotly.graph_objects as go
import pandas as pd

def create_speed_map(form_data: pd.DataFrame) -> go.Figure:
    # Create figure
    fig = go.Figure()
    
    # Handle empty data case
    if form_data.empty:
        fig.add_annotation(
            text="No data available for speed map",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False
        )
        return fig
    
    # Ensure required columns exist
    required_columns = ['Horse', 'Barrier', 'Rating', 'Jockey']
    if not all(col in form_data.columns for col in required_columns):
        fig.add_annotation(
            text="Missing required data for speed map",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False
        )
        return fig
    
    # Convert barriers to numeric, handling any non-numeric values
    data = form_data.copy()
    data['Barrier'] = pd.to_numeric(data['Barrier'], errors='coerce')
    data = data.dropna(subset=['Barrier'])
    
    if data.empty:
        fig.add_annotation(
            text="No valid barrier data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False
        )
        return fig
    
    # Sort by barrier
    data = data.sort_values('Barrier')
    
    # Ensure Rating is numeric
    data['Rating'] = pd.to_numeric(data['Rating'], errors='coerce').fillna(0)
    
    # Calculate marker colors based on confidence levels
    colors = []
    for _, row in data.iterrows():
        if 'confidence' in row:
            if row['confidence'] == 'High':
                colors.append('#90EE90')
            elif row['confidence'] == 'Medium':
                colors.append('#FFFFE0')
            else:
                colors.append('#FFB6C1')
        else:
            colors.append('#FFB6C1')
    
    # Add horses to their barriers
    try:
        fig.add_trace(go.Scatter(
            x=data['Barrier'],
            y=[1] * len(data),
            mode='markers+text',
            text=data['Horse'],
            textposition='top center',
            marker=dict(
                size=30,
                symbol='square',
                color=colors,
                line=dict(color='black', width=1)
            ),
            name='Runners',
            hovertemplate="<br>".join([
                "Horse: %{text}",
                "Barrier: %{x}",
                "Rating: %{customdata[0]}",
                "Jockey: %{customdata[1]}"
            ]),
            customdata=list(zip(
                data['Rating'].round(1),
                data['Jockey'].fillna('Unknown')
            ))
        ))
    except Exception as e:
        print(f"Error creating speed map trace: {str(e)}")
        return fig
    
    # Update layout
    try:
        max_barrier = int(data['Barrier'].max())
        fig.update_layout(
            xaxis_title="Barrier",
            yaxis_title="",
            yaxis_showticklabels=False,
            plot_bgcolor='white',
            showlegend=False,
            margin=dict(t=50, b=50, l=50, r=50)
        )
        
        fig.update_xaxes(
            gridcolor='lightgrey',
            gridwidth=1,
            range=[0, max_barrier + 1]
        )
    except Exception as e:
        print(f"Error updating speed map layout: {str(e)}")
    
    return fig
