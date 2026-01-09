"""
Variant Analytics Dashboard - Panel Version
Full featured version with authentication and error handling
"""

import panel as pn
import pandas as pd
import traceback
import hashlib
import secrets
from datetime import datetime, date, timedelta

# Initialize Panel FIRST
pn.extension('tabulator', 'plotly')

# =============================================================================
# IMPORT LOCAL MODULES WITH ERROR HANDLING
# =============================================================================

IMPORTS_OK = False
IMPORT_ERROR = ""

try:
    from config import (
        APP_NAME, DASHBOARDS, BC_OPTIONS, COHORT_OPTIONS,
        DEFAULT_BC, DEFAULT_COHORT, DEFAULT_PLAN,
        METRICS_CONFIG, CHART_METRICS, DEFAULT_USERS
    )
    from bigquery_client import (
        load_date_bounds, load_plan_groups, load_pivot_data, load_all_chart_data,
        refresh_bq_to_staging, refresh_gcs_from_staging, get_cache_info
    )
    from charts import build_line_chart
    from colors import build_plan_color_map
    IMPORTS_OK = True
except Exception as e:
    IMPORT_ERROR = f"{str(e)}\n\n{traceback.format_exc()}"


# =============================================================================
# THEME COLORS
# =============================================================================

COLORS = {
    "background": "#0F172A",
    "surface": "#1E293B",
    "border": "#334155",
    "text_primary": "#F1F5F9",
    "text_secondary": "#94A3B8",
    "accent": "#14B8A6",
    "accent_hover": "#0D9488",
    "card_bg": "#1E293B",
    "danger": "#F87171",
    "warning": "#FBBF24",
    "success": "#34D399",
}


# =============================================================================
# SESSION MANAGEMENT (Simple in-memory)
# =============================================================================

_sessions = {}  # session_id -> {user_id, name, role, expires_at}


def hash_password(password):
    """Simple password hashing"""
    return hashlib.sha256(password.encode()).hexdigest()


def authenticate(user_id, password):
    """Authenticate user and create session"""
    if not IMPORTS_OK:
        return False, None, None
    
    users = DEFAULT_USERS
    if user_id not in users:
        return False, None, None
    
    user = users[user_id]
    if user["password"] != password:
        return False, None, None
    
    # Create session
    session_id = secrets.token_hex(32)
    expires_at = datetime.now() + timedelta(days=1)
    
    _sessions[session_id] = {
        "user_id": user_id,
        "name": user["name"],
        "role": user["role"],
        "expires_at": expires_at
    }
    
    return True, session_id, user


def get_session(session_id):
    """Get session if valid"""
    if not session_id or session_id not in _sessions:
        return None
    
    session = _sessions[session_id]
    if datetime.now() > session["expires_at"]:
        del _sessions[session_id]
        return None
    
    return session


def logout(session_id):
    """Remove session"""
    if session_id in _sessions:
        del _sessions[session_id]


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_plans_by_app(plan_groups):
    """Group plans by App_Name"""
    result = {}
    for app, plan in zip(plan_groups["App_Name"], plan_groups["Plan_Name"]):
        if app not in result:
            result[app] = []
        if plan not in result[app]:
            result[app].append(plan)
    return result


def format_metric_value(value, metric_name, is_crystal_ball=False):
    """Format value based on metric type"""
    if value is None or pd.isna(value):
        return None
    config = METRICS_CONFIG.get(metric_name, {})
    format_type = config.get("format", "number")
    try:
        if metric_name == "Rebills" and is_crystal_ball:
            return round(float(value))
        if format_type == "percent":
            return round(float(value) * 100, 2)
        return round(float(value), 2)
    except:
        return None


def get_display_metric_name(metric_name):
    """Get display name with suffix"""
    config = METRICS_CONFIG.get(metric_name, {})
    display = config.get("display", metric_name)
    suffix = config.get("suffix", "")
    return f"{display}{suffix}"


def process_pivot_data(pivot_data, selected_metrics, is_crystal_ball=False):
    """Process pivot data into DataFrame for Tabulator"""
    if not pivot_data or "Reporting_Date" not in pivot_data or len(pivot_data["Reporting_Date"]) == 0:
        return None
    
    unique_dates = sorted(set(pivot_data["Reporting_Date"]), reverse=True)
    date_map = {d: d.strftime("%m/%d/%Y") if hasattr(d, 'strftime') else str(d) for d in unique_dates}
    
    plan_combos = []
    seen = set()
    for i in range(len(pivot_data["App_Name"])):
        combo = (pivot_data["App_Name"][i], pivot_data["Plan_Name"][i])
        if combo not in seen:
            plan_combos.append(combo)
            seen.add(combo)
    plan_combos.sort(key=lambda x: (x[0], x[1]))
    
    lookup = {}
    for i in range(len(pivot_data["Reporting_Date"])):
        key = (pivot_data["App_Name"][i], pivot_data["Plan_Name"][i], pivot_data["Reporting_Date"][i])
        if key not in lookup:
            lookup[key] = {}
        for metric in selected_metrics:
            if metric in pivot_data:
                lookup[key][metric] = pivot_data[metric][i]
    
    rows = []
    for app_name, plan_name in plan_combos:
        for metric in selected_metrics:
            row = {"App": app_name, "Plan": plan_name, "Metric": get_display_metric_name(metric)}
            for d in unique_dates:
                key = (app_name, plan_name, d)
                raw_value = lookup.get(key, {}).get(metric, None)
                row[date_map[d]] = format_metric_value(raw_value, metric, is_crystal_ball)
            rows.append(row)
    
    return pd.DataFrame(rows)


def create_error_pane(title, message, error_type="danger"):
    """Create a styled error pane"""
    color = COLORS.get(error_type, COLORS["danger"])
    return pn.pane.HTML(f'''
        <div style="background: {COLORS['card_bg']}; border-left: 4px solid {color}; 
                    padding: 20px; border-radius: 8px; margin: 20px 0;">
            <h3 style="color: {color}; margin: 0 0 10px 0;">{title}</h3>
            <pre style="color: {COLORS['text_secondary']}; white-space: pre-wrap; 
                        word-wrap: break-word; margin: 0;">{message}</pre>
        </div>
    ''')


# =============================================================================
# LOGIN PAGE
# =============================================================================

def create_login_page(main_area, session_store):
    """Create the login page"""
    
    # Header
    header = pn.pane.HTML(f'''
        <div style="text-align: center; padding: 40px 0;">
            <div style="width: 80px; height: 80px; background: {COLORS['accent']}; 
                        border-radius: 12px; margin: 0 auto 16px auto;
                        display: flex; align-items: center; justify-content: center;
                        font-size: 36px; font-weight: bold; color: white;">V</div>
            <h1 style="font-size: 28px; font-weight: 700; color: {COLORS['text_primary']};
                       margin: 0; letter-spacing: 3px;">VARIANT GROUP</h1>
            <p style="font-size: 14px; color: {COLORS['text_secondary']}; margin: 8px 0 0 0;">
                Sign in to access your dashboards
            </p>
        </div>
    ''', sizing_mode='stretch_width')
    
    # Form inputs
    username_input = pn.widgets.TextInput(name="Username", placeholder="Enter username", width=300)
    password_input = pn.widgets.PasswordInput(name="Password", placeholder="Enter password", width=300)
    login_btn = pn.widgets.Button(name="Sign In", button_type="primary", width=300)
    error_msg = pn.pane.HTML("", sizing_mode='stretch_width')
    
    def do_login(event):
        username = username_input.value
        password = password_input.value
        
        if not username or not password:
            error_msg.object = f'<p style="color: {COLORS["warning"]}; text-align: center;">Please enter both username and password</p>'
            return
        
        success, session_id, user = authenticate(username, password)
        
        if success:
            session_store["session_id"] = session_id
            session_store["user"] = user
            # Navigate to landing page
            main_area.clear()
            main_area.append(create_landing_page(main_area, session_store))
        else:
            error_msg.object = f'<p style="color: {COLORS["danger"]}; text-align: center;">Invalid username or password</p>'
    
    login_btn.on_click(do_login)
    
    # Demo credentials
    demo_info = pn.pane.HTML(f'''
        <div style="background: {COLORS['card_bg']}; border: 1px solid {COLORS['border']}; 
                    border-radius: 8px; padding: 15px; margin-top: 20px;">
            <p style="color: {COLORS['text_secondary']}; margin: 0 0 8px 0; font-weight: 600;">Demo Credentials:</p>
            <p style="color: {COLORS['text_secondary']}; margin: 0;">Admin: admin / admin123</p>
            <p style="color: {COLORS['text_secondary']}; margin: 0;">Viewer: viewer / viewer123</p>
        </div>
    ''')
    
    # Login card
    login_card = pn.Column(
        username_input,
        password_input,
        pn.Spacer(height=10),
        login_btn,
        error_msg,
        demo_info,
        styles={
            'background': COLORS['card_bg'],
            'border': f'1px solid {COLORS["border"]}',
            'border-radius': '12px',
            'padding': '30px'
        }
    )
    
    return pn.Column(
        header,
        pn.Row(pn.Spacer(), login_card, pn.Spacer()),
        sizing_mode='stretch_width'
    )


# =============================================================================
# LANDING PAGE
# =============================================================================

def create_landing_page(main_area, session_store):
    """Create the landing page"""
    
    user = session_store.get("user", {})
    user_name = user.get("name", "User")
    
    # Header with logout
    header = pn.pane.HTML(f'''
        <div style="text-align: center; padding: 40px 0;">
            <div style="width: 80px; height: 80px; background: {COLORS['accent']}; 
                        border-radius: 12px; margin: 0 auto 16px auto;
                        display: flex; align-items: center; justify-content: center;
                        font-size: 36px; font-weight: bold; color: white;">V</div>
            <h1 style="font-size: 28px; font-weight: 700; color: {COLORS['text_primary']};
                       margin: 0; letter-spacing: 3px;">VARIANT GROUP</h1>
            <p style="font-size: 14px; color: {COLORS['text_secondary']}; margin: 8px 0 0 0;">
                Welcome back, {user_name}
            </p>
        </div>
    ''', sizing_mode='stretch_width')
    
    # Logout button
    logout_btn = pn.widgets.Button(name="🚪 Logout", button_type="default", width=100)
    
    def do_logout(event):
        session_id = session_store.get("session_id")
        if session_id:
            logout(session_id)
        session_store.clear()
        main_area.clear()
        main_area.append(create_login_page(main_area, session_store))
    
    logout_btn.on_click(do_logout)
    
    # Cache info
    try:
        cache_info = get_cache_info()
    except Exception as e:
        cache_info = {"last_bq_refresh": "--", "last_gcs_refresh": "--", "error": str(e)}
    
    # Dashboard table
    dashboard_data = []
    for dashboard in DASHBOARDS:
        is_enabled = dashboard.get("enabled", False)
        dashboard_data.append({
            "Dashboard": dashboard["name"],
            "Status": "✅ Active" if is_enabled else "⏸️ Disabled",
            "Last BQ Refresh": cache_info.get("last_bq_refresh", "--") if is_enabled else "--",
            "Last GCS Refresh": cache_info.get("last_gcs_refresh", "--") if is_enabled else "--"
        })
    
    table = pn.widgets.Tabulator(
        pd.DataFrame(dashboard_data),
        theme='midnight',
        height=250,
        show_index=False,
        disabled=True
    )
    
    # Button to open ICARUS
    icarus_btn = pn.widgets.Button(name="📊 ICARUS - Plan (Historical)", button_type="primary", width=280)
    
    def open_icarus(event):
        try:
            # Create new content FIRST, before clearing
            new_content = create_icarus_dashboard(main_area, session_store)
            # Only clear and append if creation succeeded
            main_area.clear()
            main_area.append(new_content)
        except Exception as e:
            # Show error without clearing existing content
            main_area.clear()
            main_area.append(pn.Column(
                create_error_pane("Failed to Load Dashboard", f"{str(e)}\n\n{traceback.format_exc()}"),
                pn.widgets.Button(name="← Back to Home", button_type="default", width=150,
                                  on_click=lambda e: (main_area.clear(), main_area.append(create_landing_page(main_area, session_store)))),
                sizing_mode='stretch_width'
            ))
    
    icarus_btn.on_click(open_icarus)
    
    # Disabled dashboards info
    disabled_list = ", ".join([d["name"] for d in DASHBOARDS if not d.get("enabled", False)])
    
    return pn.Column(
        pn.Row(pn.Spacer(), logout_btn),
        header,
        pn.pane.Markdown("## 📊 Available Dashboards"),
        table,
        pn.Spacer(height=20),
        pn.pane.HTML(f'<p style="text-align: center; color: {COLORS["text_secondary"]};">Click to open a dashboard:</p>'),
        pn.Row(pn.Spacer(), icarus_btn, pn.Spacer()),
        pn.Spacer(height=20),
        pn.pane.HTML(f'<p style="text-align: center; color: {COLORS["text_secondary"]}; font-size: 12px;">Disabled: {disabled_list}</p>'),
        sizing_mode='stretch_width'
    )


# =============================================================================
# ICARUS DASHBOARD
# =============================================================================

def create_icarus_dashboard(main_area, session_store):
    """Create the ICARUS Historical dashboard"""
    
    # Load date bounds with error handling
    try:
        date_bounds = load_date_bounds()
        min_date, max_date = date_bounds["min_date"], date_bounds["max_date"]
    except Exception as e:
        return pn.Column(
            create_error_pane("Error Loading Date Bounds", f"{str(e)}\n\n{traceback.format_exc()}"),
            pn.widgets.Button(name="← Back to Home", button_type="default", width=150,
                              on_click=lambda e: (main_area.clear(), main_area.append(create_landing_page(main_area, session_store)))),
            sizing_mode='stretch_width'
        )
    
    # Load plan groups with error handling
    try:
        plan_groups = load_plan_groups("Active")
        if not plan_groups["Plan_Name"]:
            return pn.Column(
                create_error_pane("No Active Plans", "No active plans found in the database.", "warning"),
                pn.widgets.Button(name="← Back to Home", button_type="default", width=150,
                                  on_click=lambda e: (main_area.clear(), main_area.append(create_landing_page(main_area, session_store)))),
                sizing_mode='stretch_width'
            )
    except Exception as e:
        return pn.Column(
            create_error_pane("Error Loading Plans", f"{str(e)}\n\n{traceback.format_exc()}"),
            pn.widgets.Button(name="← Back to Home", button_type="default", width=150,
                              on_click=lambda e: (main_area.clear(), main_area.append(create_landing_page(main_area, session_store)))),
            sizing_mode='stretch_width'
        )
    
    plans_by_app = get_plans_by_app(plan_groups)
    
    # Back button
    back_btn = pn.widgets.Button(name="← Back", button_type="default", width=100)
    def go_back(event):
        main_area.clear()
        main_area.append(create_landing_page(main_area, session_store))
    back_btn.on_click(go_back)
    
    # Logout button
    logout_btn = pn.widgets.Button(name="🚪 Logout", button_type="default", width=100)
    def do_logout(event):
        session_id = session_store.get("session_id")
        if session_id:
            logout(session_id)
        session_store.clear()
        main_area.clear()
        main_area.append(create_login_page(main_area, session_store))
    logout_btn.on_click(do_logout)
    
    # Filters
    from_date = pn.widgets.DatePicker(name="From", value=min_date, start=min_date, end=max_date)
    to_date = pn.widgets.DatePicker(name="To", value=max_date, start=min_date, end=max_date)
    bc_select = pn.widgets.Select(name="BC", options=BC_OPTIONS, value=DEFAULT_BC, width=80)
    cohort_select = pn.widgets.Select(name="Cohort", options=COHORT_OPTIONS, value=DEFAULT_COHORT, width=100)
    
    # Plan checkboxes
    plan_checklists = {}
    plan_cols = []
    for app_name in sorted(plans_by_app.keys()):
        plans = sorted(plans_by_app[app_name])
        default = [DEFAULT_PLAN] if DEFAULT_PLAN in plans else []
        checklist = pn.widgets.CheckBoxGroup(name=app_name, options=plans, value=default)
        plan_checklists[app_name] = checklist
        plan_cols.append(pn.Column(
            pn.pane.HTML(f'<b style="color:{COLORS["text_secondary"]};font-size:12px;">{app_name}</b>'),
            checklist, width=120, styles={"max-height": "150px", "overflow-y": "auto"}
        ))
    
    # Metrics
    metrics_list = list(METRICS_CONFIG.keys())
    metrics_check = pn.widgets.CheckBoxGroup(name="Metrics", options=metrics_list, value=metrics_list, inline=True)
    
    # Results area
    results = pn.Column()
    
    # Load button
    load_btn = pn.widgets.Button(name="📊 Load Data", button_type="primary", width=150)
    
    def load_data(event):
        results.clear()
        results.append(pn.indicators.LoadingSpinner(value=True, size=50, name="Loading..."))
        
        try:
            # Get selected plans
            selected_plans = []
            for checklist in plan_checklists.values():
                selected_plans.extend(checklist.value)
            
            if not selected_plans:
                results.clear()
                results.append(create_error_pane("No Plans Selected", "Please select at least one Plan.", "warning"))
                return
            
            selected_metrics = metrics_check.value
            if not selected_metrics:
                results.clear()
                results.append(create_error_pane("No Metrics Selected", "Please select at least one Metric.", "warning"))
                return
            
            # Load Regular data
            pivot_regular = load_pivot_data(
                from_date.value, to_date.value, bc_select.value, cohort_select.value,
                selected_plans, selected_metrics, "Regular", "Active"
            )
            df_regular = process_pivot_data(pivot_regular, selected_metrics, False)
            
            # Load Crystal Ball data
            pivot_crystal = load_pivot_data(
                from_date.value, to_date.value, bc_select.value, cohort_select.value,
                selected_plans, selected_metrics, "Crystal Ball", "Active"
            )
            df_crystal = process_pivot_data(pivot_crystal, selected_metrics, True)
            
            results.clear()
            
            # Regular table
            if df_regular is not None and not df_regular.empty:
                results.append(pn.pane.Markdown("### 📊 Plan Overview (Regular)"))
                results.append(pn.widgets.Tabulator(
                    df_regular, theme='midnight', height=350, show_index=False,
                    frozen_columns=["App", "Plan", "Metric"], pagination='local', page_size=15
                ))
            
            # Crystal Ball table
            if df_crystal is not None and not df_crystal.empty:
                results.append(pn.Spacer(height=20))
                results.append(pn.pane.Markdown("### 🔮 Plan Overview (Crystal Ball)"))
                results.append(pn.widgets.Tabulator(
                    df_crystal, theme='midnight', height=350, show_index=False,
                    frozen_columns=["App", "Plan", "Metric"], pagination='local', page_size=15
                ))
            
            # Charts
            results.append(pn.Spacer(height=20))
            results.append(pn.pane.Markdown("### 📈 Charts"))
            chart_metrics = [cm["metric"] for cm in CHART_METRICS]
            
            all_regular = load_all_chart_data(
                from_date.value, to_date.value, bc_select.value, cohort_select.value,
                selected_plans, chart_metrics, "Regular", "Active"
            )
            all_crystal = load_all_chart_data(
                from_date.value, to_date.value, bc_select.value, cohort_select.value,
                selected_plans, chart_metrics, "Crystal Ball", "Active"
            )
            
            for cfg in CHART_METRICS:
                metric, display, fmt = cfg["metric"], cfg["display"], cfg["format"]
                
                data_r = all_regular.get(metric, {"Plan_Name": [], "Reporting_Date": [], "metric_value": []})
                data_c = all_crystal.get(metric, {"Plan_Name": [], "Reporting_Date": [], "metric_value": []})
                
                fig_r, _ = build_line_chart(data_r, display, fmt, (from_date.value, to_date.value), "dark")
                fig_c, _ = build_line_chart(data_c, f"{display} (CB)", fmt, (from_date.value, to_date.value), "dark")
                
                results.append(pn.Row(
                    pn.Column(pn.pane.Markdown(f"**{display}**"), pn.pane.Plotly(fig_r, height=300)),
                    pn.Column(pn.pane.Markdown(f"**{display} (Crystal Ball)**"), pn.pane.Plotly(fig_c, height=300))
                ))
            
            if (df_regular is None or df_regular.empty) and (df_crystal is None or df_crystal.empty):
                results.append(create_error_pane("No Data", "No data found for selected filters.", "warning"))
                
        except Exception as e:
            results.clear()
            results.append(create_error_pane("Error Loading Data", f"{str(e)}\n\n{traceback.format_exc()}"))
    
    load_btn.on_click(load_data)
    
    # Filters accordion
    filters = pn.Accordion(
        ("📊 Filters", pn.Column(
            pn.Row(pn.Column("**Date Range**", pn.Row(from_date, to_date)), bc_select, cohort_select),
            pn.layout.Divider(),
            pn.pane.HTML(f'<b style="color:{COLORS["text_secondary"]}">Plan Groups</b>'),
            pn.Row(*plan_cols[:7]),
            pn.Row(*plan_cols[7:]) if len(plan_cols) > 7 else pn.Spacer(height=0),
            pn.layout.Divider(),
            pn.pane.HTML(f'<b style="color:{COLORS["text_secondary"]}">Metrics</b>'),
            metrics_check
        )),
        active=[0]
    )
    
    return pn.Column(
        pn.Row(back_btn, pn.Spacer(), pn.pane.HTML(f'<h3 style="color:{COLORS["text_primary"]}">ICARUS - Plan (Historical)</h3>'), pn.Spacer(), logout_btn),
        pn.layout.Divider(),
        filters,
        pn.Row(pn.Spacer(), load_btn, pn.Spacer()),
        pn.layout.Divider(),
        results,
        sizing_mode='stretch_width'
    )


# =============================================================================
# MAIN APP
# =============================================================================

def create_app():
    """Create the main application"""
    
    # Check imports first
    if not IMPORTS_OK:
        return pn.pane.HTML(f'''
            <div style="padding: 50px; background: {COLORS['background']}; color: {COLORS['text_primary']}; min-height: 100vh;">
                <h1 style="color: {COLORS['danger']};">⚠️ Import Error</h1>
                <p>Failed to load required modules:</p>
                <pre style="background: {COLORS['card_bg']}; padding: 20px; border-radius: 8px; 
                           color: {COLORS['text_secondary']}; white-space: pre-wrap;">{IMPORT_ERROR}</pre>
            </div>
        ''')
    
    # Session store (per-user state)
    session_store = {}
    
    # Main content area
    main_area = pn.Column(sizing_mode='stretch_both')
    
    # Start with login page
    main_area.append(create_login_page(main_area, session_store))
    
    # Wrap in styled container
    app = pn.Column(
        main_area,
        sizing_mode='stretch_both',
        styles={'background': COLORS['background'], 'padding': '20px', 'min-height': '100vh'}
    )
    
    return app


# =============================================================================
# SERVE
# =============================================================================

app = create_app()
app.servable(title="Variant Dashboard")
