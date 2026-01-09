"""
Theme System for Variant Analytics Dashboard - Panel Version
- Dark (default) and Light modes
- Custom CSS for Panel components
- Tabulator theme configuration
"""

import param
import panel as pn
from config import THEME_COLORS


class ThemeManager(param.Parameterized):
    """Reactive theme manager"""
    theme = param.Selector(default="dark", objects=["dark", "light"])
    
    @property
    def colors(self):
        return THEME_COLORS.get(self.theme, THEME_COLORS["dark"])
    
    @property
    def tabulator_theme(self):
        return "midnight" if self.theme == "dark" else "simple"
    
    @property
    def plotly_template(self):
        return "plotly_dark" if self.theme == "dark" else "plotly_white"


def get_theme_colors(theme="dark"):
    """Get the color palette for specified theme"""
    return THEME_COLORS.get(theme, THEME_COLORS["dark"])


def get_custom_css(theme="dark"):
    """Generate custom CSS for Panel app"""
    colors = get_theme_colors(theme)
    
    return f"""
    /* Global Styles */
    :root {{
        --primary-color: {colors['accent']};
        --background-color: {colors['background']};
        --surface-color: {colors['surface']};
        --text-color: {colors['text_primary']};
        --text-secondary: {colors['text_secondary']};
        --border-color: {colors['border']};
    }}
    
    body {{
        background-color: {colors['background']} !important;
        color: {colors['text_primary']} !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    }}
    
    /* Card styling */
    .card {{
        background: {colors['card_bg']} !important;
        border: 1px solid {colors['border']} !important;
        border-radius: 12px !important;
    }}
    
    .bk-root {{
        background-color: {colors['background']} !important;
    }}
    
    /* Panel widgets */
    .bk-input {{
        background-color: {colors['input_bg']} !important;
        color: {colors['text_primary']} !important;
        border: 1px solid {colors['border']} !important;
        border-radius: 8px !important;
    }}
    
    .bk-btn {{
        background-color: {colors['accent']} !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
    }}
    
    .bk-btn:hover {{
        background-color: {colors['accent_hover']} !important;
    }}
    
    .bk-btn-default {{
        background-color: {colors['surface']} !important;
        color: {colors['text_primary']} !important;
        border: 1px solid {colors['border']} !important;
    }}
    
    /* Tabs */
    .bk-tabs-header {{
        background-color: {colors['surface']} !important;
        border-bottom: 1px solid {colors['border']} !important;
    }}
    
    .bk-tab {{
        background-color: transparent !important;
        color: {colors['text_secondary']} !important;
        border: none !important;
    }}
    
    .bk-tab.bk-active {{
        background-color: {colors['accent']} !important;
        color: white !important;
        border-radius: 8px 8px 0 0 !important;
    }}
    
    /* Select/Dropdown */
    select, .bk-input-group select {{
        background-color: {colors['input_bg']} !important;
        color: {colors['text_primary']} !important;
        border: 1px solid {colors['border']} !important;
        border-radius: 8px !important;
        padding: 8px 12px !important;
    }}
    
    /* Checkbox */
    .bk-input[type="checkbox"] {{
        accent-color: {colors['accent']} !important;
    }}
    
    /* Markdown headers */
    .bk-Markdown h1, .bk-Markdown h2, .bk-Markdown h3 {{
        color: {colors['text_primary']} !important;
    }}
    
    .bk-Markdown p {{
        color: {colors['text_secondary']} !important;
    }}
    
    /* Alerts */
    .alert {{
        background-color: {colors['card_bg']} !important;
        border: 1px solid {colors['border']} !important;
        border-radius: 8px !important;
        color: {colors['text_primary']} !important;
    }}
    
    .alert-success {{
        border-left: 4px solid {colors['success']} !important;
    }}
    
    .alert-warning {{
        border-left: 4px solid {colors['warning']} !important;
    }}
    
    .alert-danger {{
        border-left: 4px solid {colors['danger']} !important;
    }}
    
    /* Scrollbar */
    ::-webkit-scrollbar {{
        width: 8px !important;
        height: 8px !important;
    }}
    
    ::-webkit-scrollbar-track {{
        background: {colors['background']} !important;
    }}
    
    ::-webkit-scrollbar-thumb {{
        background: {colors['border']} !important;
        border-radius: 4px !important;
    }}
    
    /* Tabulator overrides */
    .tabulator {{
        background-color: {colors['card_bg']} !important;
        border: 1px solid {colors['border']} !important;
    }}
    
    .tabulator-header {{
        background-color: {colors['table_header_bg']} !important;
        color: {colors['text_primary']} !important;
    }}
    
    .tabulator-row {{
        background-color: {colors['table_row_odd']} !important;
        color: {colors['text_primary']} !important;
    }}
    
    .tabulator-row-even {{
        background-color: {colors['table_row_even']} !important;
    }}
    
    .tabulator-row:hover {{
        background-color: {colors['hover']} !important;
    }}
    
    .tabulator-cell {{
        border-color: {colors['border']} !important;
    }}
    
    /* Accordion */
    .accordion {{
        background-color: {colors['card_bg']} !important;
        border: 1px solid {colors['border']} !important;
        border-radius: 8px !important;
    }}
    
    .accordion-header {{
        background-color: {colors['surface']} !important;
        color: {colors['text_primary']} !important;
    }}
    
    /* Filter section */
    .filter-title {{
        font-size: 13px !important;
        font-weight: 600 !important;
        color: {colors['text_secondary']} !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
        margin-bottom: 8px !important;
        padding-bottom: 6px !important;
        border-bottom: 1px solid {colors['border']} !important;
    }}
    
    /* Logo container */
    .logo-container {{
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 20px;
    }}
    
    .logo-fallback {{
        width: 80px;
        height: 80px;
        background: {colors['accent']};
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 36px;
        font-weight: bold;
        color: white;
    }}
    """


def get_plotly_layout(theme="dark"):
    """Get Plotly layout configuration based on theme"""
    colors = get_theme_colors(theme)
    
    return {
        "paper_bgcolor": colors["card_bg"],
        "plot_bgcolor": colors["card_bg"],
        "font": {
            "family": "Inter, sans-serif",
            "size": 12,
            "color": colors["text_primary"]
        },
        "xaxis": {
            "gridcolor": colors["border"],
            "linecolor": colors["border"],
            "tickfont": {"color": colors["text_secondary"]},
        },
        "yaxis": {
            "gridcolor": colors["border"],
            "linecolor": colors["border"],
            "tickfont": {"color": colors["text_secondary"]},
        },
        "legend": {
            "font": {"color": colors["text_primary"]},
            "bgcolor": "rgba(0,0,0,0)"
        }
    }


def create_logo_pane(theme="dark"):
    """Create logo pane with fallback"""
    import os
    import base64
    
    colors = get_theme_colors(theme)
    logo_path = os.path.join(os.path.dirname(__file__), "assets", "variant_logo.png")
    
    if os.path.exists(logo_path):
        try:
            with open(logo_path, "rb") as f:
                logo_b64 = base64.b64encode(f.read()).decode()
            filter_style = "filter: invert(1);" if theme == "dark" else ""
            return pn.pane.HTML(f'''
                <div class="logo-container">
                    <img src="data:image/png;base64,{logo_b64}" 
                         style="width: 80px; height: auto; {filter_style}" 
                         alt="Variant Logo">
                </div>
            ''')
        except Exception:
            pass
    
    # Fallback: Styled V
    return pn.pane.HTML(f'''
        <div class="logo-container">
            <div class="logo-fallback">V</div>
        </div>
    ''')


def create_header(title="VARIANT GROUP", subtitle=None, theme="dark"):
    """Create header with logo and title"""
    colors = get_theme_colors(theme)
    
    header_html = f'''
        <div style="text-align: center; padding: 20px 0;">
            <div style="width: 80px; height: 80px; background: {colors['accent']}; 
                        border-radius: 12px; margin: 0 auto 16px auto;
                        display: flex; align-items: center; justify-content: center;
                        font-size: 36px; font-weight: bold; color: white;">V</div>
            <h1 style="font-size: 28px; font-weight: 700; color: {colors['text_primary']};
                       margin: 0; letter-spacing: 3px;">{title}</h1>
    '''
    
    if subtitle:
        header_html += f'''
            <p style="font-size: 14px; color: {colors['text_secondary']}; margin: 8px 0 0 0;">
                {subtitle}
            </p>
        '''
    
    header_html += '</div>'
    
    return pn.pane.HTML(header_html)
