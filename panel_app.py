"""
Variant Analytics Dashboard - Panel Version
Super minimal version for debugging
"""

import panel as pn

# Must call extension before any Panel objects
pn.extension()

# Create simple content directly
content = pn.Column(
    pn.pane.Markdown("# VARIANT GROUP"),
    pn.pane.Markdown("## Dashboard is working! ✅"),
    pn.pane.Markdown("If you can see this, Panel is rendering correctly."),
    pn.widgets.Button(name="Test Button", button_type="primary"),
    sizing_mode="stretch_width"
)

# Make it servable
content.servable(title="Variant Dashboard")
