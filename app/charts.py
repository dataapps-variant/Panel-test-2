"""
Chart Components for Variant Analytics Dashboard - Panel Version
Uses Plotly for interactive charts with Panel integration
"""

import plotly.graph_objects as go
import panel as pn
from colors import build_plan_color_map
from theme import get_theme_colors, get_plotly_layout


def hex_to_rgba(hex_color, opacity=1.0):
    """Convert hex color to rgba string"""
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return f"rgba({r}, {g}, {b}, {opacity})"


def build_line_chart(data, display_name, format_type="dollar", date_range=None, theme="dark"):
    """
    Build a Plotly line chart for a metric by Plan over time
    
    Args:
        data: Dict with Plan_Name, Reporting_Date, metric_value lists
        display_name: Chart title
        format_type: 'dollar', 'percent', or 'number'
        date_range: Tuple of (min_date, max_date) for x-axis range
        theme: 'dark' or 'light'
    
    Returns:
        Tuple of (Plotly figure, list of unique plans)
    """
    colors = get_theme_colors(theme)
    
    # Check for empty data
    if not data or "Plan_Name" not in data or len(data["Plan_Name"]) == 0:
        fig = go.Figure()
        fig.update_layout(
            height=350,
            paper_bgcolor=colors["card_bg"],
            plot_bgcolor=colors["card_bg"],
            font=dict(family="Inter, sans-serif", size=12, color=colors["text_primary"]),
            annotations=[{
                "text": "No data available for selected filters",
                "xref": "paper",
                "yref": "paper",
                "x": 0.5,
                "y": 0.5,
                "showarrow": False,
                "font": {"size": 14, "color": colors["text_secondary"]}
            }]
        )
        return fig, []
    
    # Get unique plans and build color map
    unique_plans = sorted(set(data["Plan_Name"]))
    color_map = build_plan_color_map(unique_plans)
    
    # Organize data by plan
    plan_data = {}
    for i in range(len(data["Plan_Name"])):
        plan = data["Plan_Name"][i]
        date = data["Reporting_Date"][i]
        value = data["metric_value"][i]
        
        if plan not in plan_data:
            plan_data[plan] = {"dates": [], "values": []}
        plan_data[plan]["dates"].append(date)
        plan_data[plan]["values"].append(value if value is not None else 0)
    
    # Create figure
    fig = go.Figure()
    
    LINE_OPACITY = 0.7
    LINE_WIDTH = 1
    
    # Add trace for each plan
    for plan in unique_plans:
        if plan in plan_data:
            sorted_pairs = sorted(zip(plan_data[plan]["dates"], plan_data[plan]["values"]))
            dates = [p[0] for p in sorted_pairs]
            values = [p[1] for p in sorted_pairs]
            
            base_color = color_map.get(plan, "#6B7280")
            line_color = hex_to_rgba(base_color, LINE_OPACITY)
            
            # Custom hover template
            if format_type == "dollar":
                hover_template = f'<b>{plan}</b><br>Date: %{{x|%B %d, %Y}}<br>Value: $%{{y:,.2f}}<extra></extra>'
            elif format_type == "percent":
                hover_template = f'<b>{plan}</b><br>Date: %{{x|%B %d, %Y}}<br>Value: %{{y:.2%}}<extra></extra>'
            else:
                hover_template = f'<b>{plan}</b><br>Date: %{{x|%B %d, %Y}}<br>Value: %{{y:,.0f}}<extra></extra>'
            
            fig.add_trace(
                go.Scatter(
                    x=dates,
                    y=values,
                    mode='lines',
                    name=plan,
                    line=dict(color=line_color, width=LINE_WIDTH, shape='linear'),
                    hovertemplate=hover_template,
                    showlegend=False,
                    connectgaps=False
                )
            )
    
    # Y-axis formatting
    if format_type == "dollar":
        yaxis_tickprefix = "$"
        yaxis_tickformat = ",.2f"
    elif format_type == "percent":
        yaxis_tickprefix = ""
        yaxis_tickformat = ".1%"
    else:
        yaxis_tickprefix = ""
        yaxis_tickformat = ",d"
    
    xaxis_range = [date_range[0], date_range[1]] if date_range else None
    
    # Update layout
    fig.update_layout(
        height=350,
        margin=dict(l=60, r=20, t=20, b=50),
        hovermode="x unified",
        paper_bgcolor=colors["card_bg"],
        plot_bgcolor=colors["card_bg"],
        font=dict(family="Inter, sans-serif", size=12, color=colors["text_primary"]),
        xaxis=dict(
            gridcolor=colors["border"],
            linecolor=colors["border"],
            tickfont=dict(color=colors["text_secondary"]),
            tickformat="%b %Y",
            range=xaxis_range,
            fixedrange=False
        ),
        yaxis=dict(
            gridcolor=colors["border"],
            linecolor=colors["border"],
            tickfont=dict(color=colors["text_secondary"]),
            tickprefix=yaxis_tickprefix,
            tickformat=yaxis_tickformat,
            fixedrange=False
        ),
        dragmode="zoom"
    )
    
    return fig, unique_plans


def create_legend_html(plans, color_map, theme="dark"):
    """Create HTML legend for charts"""
    colors = get_theme_colors(theme)
    
    items_html = ""
    for plan in plans:
        color = color_map.get(plan, "#6B7280")
        items_html += f'''
            <span style="display: inline-flex; align-items: center; margin-right: 12px; margin-bottom: 4px;">
                <span style="width: 10px; height: 10px; border-radius: 50%; 
                            background-color: {color}; margin-right: 6px;"></span>
                <span style="font-size: 12px; color: {colors['text_primary']};">{plan}</span>
            </span>
        '''
    
    return f'''
        <div style="background: {colors['surface']}; border: 1px solid {colors['border']};
                    border-radius: 8px; padding: 10px 16px; margin-bottom: 16px;
                    max-height: 60px; overflow-y: auto; display: flex; flex-wrap: wrap; gap: 8px;">
            {items_html}
        </div>
    '''


def create_chart_panel(data, display_name, format_type="dollar", date_range=None, theme="dark"):
    """
    Create a complete chart panel with legend
    
    Returns:
        Panel Column with legend and chart
    """
    fig, plans = build_line_chart(data, display_name, format_type, date_range, theme)
    color_map = build_plan_color_map(plans) if plans else {}
    
    components = []
    
    if plans:
        legend_html = create_legend_html(plans, color_map, theme)
        components.append(pn.pane.HTML(legend_html))
    
    components.append(pn.pane.Plotly(fig, config={'displayModeBar': True, 'displaylogo': False}))
    
    return pn.Column(*components)
