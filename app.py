"""
Dashboard RFM interactif avec Plotly Dash
- 3 KPIs
- 3 graphiques
- 1 filtre dropdown pour segmenter par client
"""

import pandas as pd
from dash import Dash, dcc, html, Input, Output
import plotly.graph_objects as go

df = pd.read_csv("rfm_results.csv")

COLORS = {
    "Champions": "#2E7D32",
    "Loyal Customers": "#558B2F",
    "Potential Loyalists": "#9CCC65",
    "At Risk": "#FB8C00",
    "Cant Lose Them": "#E53935",
    "Hibernating": "#757575",
    "Others": "#BDBDBD",
}

app = Dash(__name__)
app.title = "RFM Dashboard"

# Layout principal
app.layout = html.Div([
    # Header
    html.Div([
        html.H1("📊 RFM Segmentation Dashboard", style={"margin": "0", "color": "#2c3e50"}),
        html.P("E-commerce Customer Analytics | Online Retail II", style={"color": "#7f8c8d", "margin": "5px 0 0 0"})
    ], style={"padding": "30px", "backgroundColor": "#ecf0f1", "borderBottom": "3px solid #3498db"}),
    
    # Contenu principal
    html.Div([
        # Filtre interactif
        html.Div([
            html.Label("🔍 Filtrer par segment :", style={"fontWeight": "bold", "color": "#2c3e50"}),
            dcc.Dropdown(
                id="segment-filter",
                options=[
                    {"label": "Tous les segments", "value": "all"},
                    {"label": "Champions", "value": "Champions"},
                    {"label": "Loyal Customers", "value": "Loyal Customers"},
                    {"label": "Potential Loyalists", "value": "Potential Loyalists"},
                    {"label": "At Risk", "value": "At Risk"},
                    {"label": "Cant Lose Them", "value": "Cant Lose Them"},
                    {"label": "Hibernating", "value": "Hibernating"},
                    {"label": "Others", "value": "Others"},
                ],
                value="all",
                style={"width": "100%", "padding": "10px"}
            )
        ], style={"padding": "20px", "backgroundColor": "#fff", "borderRadius": "8px", "boxShadow": "0 2px 4px rgba(0,0,0,0.1)", "marginBottom": "30px"}),
        
        # KPIs
        html.Div([
            html.Div([html.H3("Total Customers", style={"color": "#7f8c8d", "fontSize": "14px"}), html.H2(id="kpi-customers", style={"color": "#2E7D32", "margin": "10px 0"})], style={"padding": "20px", "backgroundColor": "#fff", "borderRadius": "8px", "boxShadow": "0 2px 4px rgba(0,0,0,0.1)"}),
            html.Div([html.H3("Avg Recency", style={"color": "#7f8c8d", "fontSize": "14px"}), html.H2(id="kpi-recency", style={"color": "#3498db", "margin": "10px 0"})], style={"padding": "20px", "backgroundColor": "#fff", "borderRadius": "8px", "boxShadow": "0 2px 4px rgba(0,0,0,0.1)"}),
            html.Div([html.H3("Avg Revenue", style={"color": "#7f8c8d", "fontSize": "14px"}), html.H2(id="kpi-revenue", style={"color": "#e74c3c", "margin": "10px 0"})], style={"padding": "20px", "backgroundColor": "#fff", "borderRadius": "8px", "boxShadow": "0 2px 4px rgba(0,0,0,0.1)"}),
        ], style={"display": "grid", "gridTemplateColumns": "1fr 1fr 1fr", "gap": "20px", "marginBottom": "30px"}),
        
        # Graphiques
        html.Div([
            html.Div([html.H3("Customer Segments Distribution", style={"color": "#2c3e50"}), dcc.Graph(id="pie")], style={"padding": "20px", "backgroundColor": "#fff", "borderRadius": "8px", "boxShadow": "0 2px 4px rgba(0,0,0,0.1)", "flex": "1"}),
            html.Div([html.H3("Revenue by Segment", style={"color": "#2c3e50"}), dcc.Graph(id="bar")], style={"padding": "20px", "backgroundColor": "#fff", "borderRadius": "8px", "boxShadow": "0 2px 4px rgba(0,0,0,0.1)", "flex": "1.5"}),
        ], style={"display": "flex", "gap": "20px", "marginBottom": "30px"}),
        
        # Scatter plot
        html.Div([html.H3("RFM Analysis: Recency vs Monetary Value", style={"color": "#2c3e50"}), dcc.Graph(id="scatter")], style={"padding": "20px", "backgroundColor": "#fff", "borderRadius": "8px", "boxShadow": "0 2px 4px rgba(0,0,0,0.1)"}),
        
    ], style={"padding": "30px", "maxWidth": "1400px", "margin": "0 auto"}),
], style={"backgroundColor": "#f5f6fa", "minHeight": "100vh", "fontFamily": "Arial, sans-serif"})

# Callback pour mettre à jour le dashboard selon le filtre
@app.callback(
    [Output("kpi-customers", "children"), Output("kpi-recency", "children"), Output("kpi-revenue", "children"), Output("pie", "figure"), Output("bar", "figure"), Output("scatter", "figure")],
    Input("segment-filter", "value")
)
def update_dashboard(selected_segment):
    # Filtrer les données
    if selected_segment == "all":
        filtered_df = df
    else:
        filtered_df = df[df["segment"] == selected_segment]
    
    # KPIs
    num_customers = len(filtered_df)
    avg_recency = f"{filtered_df['recency'].mean():.1f}d"
    avg_revenue = f"€{filtered_df['monetary'].mean():.0f}"
    
    # Pie Chart
    segment_counts = filtered_df["segment"].value_counts()
    pie = go.Figure(data=[go.Pie(
        labels=segment_counts.index,
        values=segment_counts.values,
        marker=dict(colors=[COLORS.get(seg, "#95a5a6") for seg in segment_counts.index]),
        hovertemplate="<b>%{label}</b><br>Count: %{value}<br>%{percent}<extra></extra>"
    )])
    pie.update_layout(margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=350)
    
    # Bar Chart
    revenue_by_segment = filtered_df.groupby("segment")["monetary"].sum().sort_values(ascending=False)
    bar = go.Figure(data=[go.Bar(
        x=revenue_by_segment.index,
        y=revenue_by_segment.values,
        marker=dict(color=[COLORS.get(seg, "#95a5a6") for seg in revenue_by_segment.index]),
        hovertemplate="<b>%{x}</b><br>Revenue: €%{y:.0f}<extra></extra>"
    )])
    bar.update_layout(xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridwidth=1, gridcolor="#ecf0f1"), margin=dict(l=50, r=20, t=0, b=50), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=400, showlegend=False)
    
    # Scatter Plot
    scatter = go.Figure(data=[go.Scatter(
        x=filtered_df["recency"],
        y=filtered_df["monetary"],
        mode="markers",
        marker=dict(
            size=filtered_df["frequency"] * 3,
            color=[COLORS.get(seg, "#95a5a6") for seg in filtered_df["segment"]],
            opacity=0.7,
            line=dict(width=1, color="white")
        ),
        text=filtered_df["segment"],
        hovertemplate="<b>%{text}</b><br>Recency: %{x}d<br>Monetary: €%{y:.0f}<extra></extra>"
    )])
    scatter.update_layout(xaxis=dict(title="Recency (days)", showgrid=True, gridwidth=1, gridcolor="#ecf0f1"), yaxis=dict(title="Monetary Value (€)", showgrid=True, gridwidth=1, gridcolor="#ecf0f1"), margin=dict(l=50, r=20, t=0, b=50), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=450, showlegend=False)
    
    return num_customers, avg_recency, avg_revenue, pie, bar, scatter

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)
