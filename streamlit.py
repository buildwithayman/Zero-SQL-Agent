"""
AI SQL AGENT - Futuristic Neural Data Copilot
A sleek, modern, ultra-crisp interface for Natural Language to PostgreSQL analytics.
"""

import os
import time
import json
import uuid
import pandas as pd
import requests
import streamlit as st
from datetime import datetime
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from backend.main import app as fastapi_app

# Local imports
from sql_validator import is_query, FORBIDDEN_KEYWORDS
from database import (
    check_db_health,
    seed_database,
    get_db_schema,
    execute_query,
    get_tables_list,
    get_table_details,
    get_table_row_counts,
    get_db_server_info,
)
from agents import ask_agent, reset_agent_memory

# Environment setup
load_dotenv()
DEFAULT_GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
HARDCODED_TEMPERATURE = 0.0  # Deterministic SQL generation

# ==============================================================================
# 1. PAGE CONFIGURATION & FUTURISTIC THEME
# ==============================================================================
st.set_page_config(
    page_title="ZeroSQL AI — No SQL Required",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Futuristic Cyber / Glassmorphic UI CSS
FUTURISTIC_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

/* Global Reset & Typography */
html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
    color: #e2e8f0;
}

h1, h2, h3, .futuristic-title {
    font-family: 'Space Grotesk', sans-serif !important;
    letter-spacing: -0.02em;
}

code, pre, .stCodeBlock {
    font-family: 'JetBrains Mono', monospace !important;
}

/* Background Atmosphere */
.stApp {
    background: radial-gradient(circle at 50% -20%, #1e1b4b 0%, #090d16 50%, #030712 100%) !important;
}

/* Header Container */
.cyber-header {
    background: rgba(15, 23, 42, 0.65);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    padding: 20px 24px;
    margin-bottom: 20px;
    backdrop-filter: blur(20px);
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 16px;
}

.brand-glow {
    font-size: 1.65rem;
    font-weight: 800;
    background: linear-gradient(135deg, #38bdf8 0%, #818cf8 50%, #c084fc 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    display: flex;
    align-items: center;
    gap: 10px;
    font-family: 'Space Grotesk', sans-serif;
}

/* Status Badges & Pills */
.pill-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 5px 12px;
    border-radius: 9999px;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.02em;
}

.pill-active {
    background: rgba(16, 185, 129, 0.12);
    border: 1px solid rgba(16, 185, 129, 0.3);
    color: #34d399;
}

.pill-nosql {
    background: rgba(245, 158, 11, 0.12);
    border: 1px solid rgba(245, 158, 11, 0.35);
    color: #fbbf24;
}

.pill-model {
    background: rgba(129, 140, 248, 0.12);
    border: 1px solid rgba(129, 140, 248, 0.3);
    color: #a5b4fc;
}

.pulse-dot {
    width: 7px;
    height: 7px;
    background-color: #34d399;
    border-radius: 50%;
    box-shadow: 0 0 8px #34d399;
    animation: pulse 1.6s infinite;
}

@keyframes pulse {
    0% { transform: scale(0.9); opacity: 0.8; }
    50% { transform: scale(1.3); opacity: 1; box-shadow: 0 0 12px #34d399; }
    100% { transform: scale(0.9); opacity: 0.8; }
}

/* Prompt Action Cards (Empty State Hero) */
.prompt-card {
    background: rgba(15, 23, 42, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 12px;
    padding: 16px 18px;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    cursor: pointer;
    backdrop-filter: blur(10px);
    margin-bottom: 10px;
}

.prompt-card:hover {
    border-color: #38bdf8;
    background: rgba(56, 189, 248, 0.08);
    transform: translateY(-2px);
    box-shadow: 0 8px 20px -4px rgba(56, 189, 248, 0.15);
}

.prompt-card-icon {
    font-size: 1.3rem;
    margin-bottom: 6px;
}

.prompt-card-title {
    font-weight: 600;
    font-size: 0.95rem;
    color: #f1f5f9;
    margin-bottom: 4px;
}

.prompt-card-desc {
    font-size: 0.8rem;
    color: #94a3b8;
    line-height: 1.4;
}

/* SQL Result Box */
.sql-container {
    background: #090d16;
    border: 1px solid rgba(56, 189, 248, 0.25);
    border-left: 3px solid #38bdf8;
    border-radius: 8px;
    padding: 10px 14px;
    margin: 12px 0;
}

/* Tabs Styling */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    padding-bottom: 4px;
}

.stTabs [data-baseweb="tab"] {
    border-radius: 8px 8px 0 0;
    padding: 8px 18px;
    font-weight: 600;
    font-size: 0.88rem;
    color: #94a3b8;
}

.stTabs [aria-selected="true"] {
    background-color: rgba(56, 189, 248, 0.1) !important;
    color: #38bdf8 !important;
    border-bottom: 2px solid #38bdf8 !important;
}

/* Sidebar Styling */
[data-testid="stSidebar"] {
    background-color: #070b14 !important;
    border-right: 1px solid rgba(255, 255, 255, 0.06);
}

/* Main Content Bottom Bar - Perfectly Centered in Viewport */
[data-testid="stBottom"] {
    background: transparent !important;
}

[data-testid="stBottom"] > div {
    background: transparent !important;
    max-width: 840px !important;
    margin: 0 auto !important;
    padding: 0 16px 16px 16px !important;
}

/* Animated Continuous Flowing Laser Light Border on Chat Input */
@keyframes continuousLaserFlow {
    0% {
        background-position: 0% 50%;
        box-shadow: 0 0 18px rgba(0, 242, 254, 0.45), 0 0 35px rgba(139, 92, 246, 0.2), 0 16px 40px -8px rgba(0, 0, 0, 0.8);
    }
    50% {
        background-position: 100% 50%;
        box-shadow: 0 0 28px rgba(236, 72, 153, 0.55), 0 0 50px rgba(0, 242, 254, 0.3), 0 16px 40px -8px rgba(0, 0, 0, 0.8);
    }
    100% {
        background-position: 200% 50%;
        box-shadow: 0 0 18px rgba(0, 242, 254, 0.45), 0 0 35px rgba(139, 92, 246, 0.2), 0 16px 40px -8px rgba(0, 0, 0, 0.8);
    }
}

[data-testid="stChatInput"] {
    background: linear-gradient(135deg, rgba(15, 23, 42, 0.95), rgba(8, 12, 22, 0.98)) padding-box,
                linear-gradient(90deg, #00f2fe 0%, #8b5cf6 25%, #ec4899 50%, #06b6d4 75%, #00f2fe 100%) border-box !important;
    background-size: 200% 200% !important;
    border: 2.5px solid transparent !important;
    border-radius: 18px !important;
    animation: continuousLaserFlow 2.8s linear infinite !important;
    backdrop-filter: blur(24px) !important;
    width: 100% !important;
    margin: 0 auto !important;
}

[data-testid="stChatInput"]:focus-within {
    animation: continuousLaserFlow 1.6s linear infinite !important;
    box-shadow: 0 0 35px rgba(0, 242, 254, 0.75), 0 0 65px rgba(236, 72, 153, 0.45), 0 16px 40px -8px rgba(0, 0, 0, 0.9) !important;
}

/* Chat container bottom padding so messages never get covered by the bottom bar */
.chat-bottom-spacer {
    height: 95px;
}
</style>
"""
st.markdown(FUTURISTIC_CSS, unsafe_allow_html=True)


# ==============================================================================
# 2. STATE MANAGEMENT & METADATA
# ==============================================================================
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

if "pending_prompt" not in st.session_state:
    st.session_state.pending_prompt = None

if "admin_token" not in st.session_state:
    st.session_state.admin_token = None

if "admin_user" not in st.session_state:
    st.session_state.admin_user = None

if "last_upload_result" not in st.session_state:
    st.session_state.last_upload_result = None

if "processed_datasets" not in st.session_state:
    st.session_state.processed_datasets = {}

if "selected_dataset_id" not in st.session_state:
    st.session_state.selected_dataset_id = "ALL"

FASTAPI_SERVER_URL = os.getenv("FASTAPI_SERVER_URL", "http://127.0.0.1:8000")
_fastapi_client = None


def get_fastapi_client():
    """Cached singleton TestClient for in-process ASGI fallback."""
    global _fastapi_client
    if _fastapi_client is None:
        _fastapi_client = TestClient(fastapi_app)
    return _fastapi_client


def call_backend_api(method: str, endpoint: str, **kwargs):
    """
    Routes API requests to the live FastAPI server if available,
    falling back seamlessly to direct in-process ASGI client.
    Guarantees that all dataset operations strictly execute via FastAPI!
    """
    token = st.session_state.get("admin_token")
    headers = kwargs.pop("headers", {})
    if token and "Authorization" not in headers:
        headers["Authorization"] = f"Bearer {token}"

    try:
        url = f"{FASTAPI_SERVER_URL}{endpoint}"
        resp = requests.request(method, url, headers=headers, timeout=4, **kwargs)
        return resp
    except Exception:
        client = get_fastapi_client()
        client_fn = getattr(client, method.lower())
        return client_fn(endpoint, headers=headers, **kwargs)


@st.cache_data(ttl=20)
def get_db_status_cached():
    """Cached database health and table inspection."""
    healthy = check_db_health()
    tables = get_tables_list() if healthy else []
    counts = get_table_row_counts() if healthy else {}
    server_info = get_db_server_info() if healthy else {}
    return {
        "healthy": healthy,
        "tables": tables,
        "counts": counts,
        "total_rows": sum(counts.values()) if counts else 0,
        "server_info": server_info
    }


db_meta = get_db_status_cached()


def execute_sql_safe(sql_str: str) -> tuple[bool, pd.DataFrame | None, str]:
    """Validates read-only query and executes against PostgreSQL."""
    clean_sql = sql_str.strip()
    if not clean_sql.endswith(";"):
        clean_sql += ";"

    if not is_query(clean_sql):
        return (
            False,
            None,
            "Security Policy Violation: Only read-only SELECT or WITH statements are allowed. Destructive statements (DROP, DELETE, UPDATE, INSERT, ALTER, TRUNCATE) are strictly blocked."
        )

    try:
        t0 = time.time()
        results = execute_query(clean_sql)
        ms = round((time.time() - t0) * 1000, 1)
        df = pd.DataFrame(results) if results else pd.DataFrame()
        return True, df, f"Executed in {ms}ms ({len(df)} rows)"
    except Exception as e:
        return False, None, f"Database Error: {str(e)}"


def render_auto_chart(df: pd.DataFrame, key_id: str):
    """Clean, minimalistic chart visualization engine."""
    if df.empty or len(df.columns) < 2:
        return

    num_cols = df.select_dtypes(include=["number", "float", "int"]).columns.tolist()
    cat_cols = [c for c in df.columns if c not in num_cols]

    if not num_cols or not cat_cols:
        return

    with st.expander("📈 Visual Data Analytics", expanded=False):
        c1, c2, c3 = st.columns([2, 2, 1.5])
        with c1:
            x_col = st.selectbox("X-Axis (Category)", cat_cols, key=f"x_{key_id}")
        with c2:
            y_col = st.selectbox("Y-Axis (Metric)", num_cols, key=f"y_{key_id}")
        with c3:
            c_type = st.selectbox("Chart", ["Bar", "Line", "Area"], key=f"type_{key_id}")

        try:
            plot_df = df[[x_col, y_col]].dropna().set_index(x_col)
            if c_type == "Bar":
                st.bar_chart(plot_df, use_container_width=True)
            elif c_type == "Line":
                st.line_chart(plot_df, use_container_width=True)
            elif c_type == "Area":
                st.area_chart(plot_df, use_container_width=True)
        except Exception as e:
            st.caption(f"Chart render notice: {e}")


# ==============================================================================
# 3. SLEEK SIDEBAR WITH HEALTH & SESSION STATS
# ==============================================================================
with st.sidebar:
    # Minimalist Showcase Branding
    st.markdown("""
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 16px; padding: 2px 0;">
            <div style="background: linear-gradient(135deg, #00f2fe 0%, #4facfe 100%); width: 36px; height: 36px; min-width: 36px; border-radius: 9px; display: flex; align-items: center; justify-content: center; font-size: 19px; box-shadow: 0 0 16px rgba(0, 242, 254, 0.4);">
                ⚡
            </div>
            <div style="display: flex; flex-direction: column; justify-content: center; line-height: 1;">
                <div style="font-size: 1.15rem; font-weight: 800; color: #f8fafc; font-family: 'Space Grotesk', sans-serif; letter-spacing: -0.02em; line-height: 1.1; margin: 0; padding: 0;">ZeroSQL AI</div>
                <div style="font-size: 0.68rem; color: #38bdf8; font-weight: 700; font-family: 'JetBrains Mono', monospace; letter-spacing: 0.05em; line-height: 1; margin-top: 2px; padding: 0;">NO SQL NEEDED</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # 1. LIVE POSTGRES CONNECTION & DB HEALTH CARD
    db_name = db_meta["server_info"].get("database", "ai_sql_agent")
    is_healthy = db_meta["healthy"]
    
    st.markdown(f"""
        <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 12px; padding: 14px; margin-bottom: 14px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span style="font-size: 0.75rem; font-weight: 700; color: #94a3b8; letter-spacing: 0.05em;">POSTGRES HEALTH</span>
                {'<span class="pill-badge pill-active" style="padding: 2px 8px; font-size: 0.72rem;"><span class="pulse-dot"></span> Healthy</span>' if is_healthy else '<span class="pill-badge" style="background: rgba(239,68,68,0.15); color: #f87171; padding: 2px 8px; font-size: 0.72rem;">Offline</span>'}
            </div>
            <div style="font-size: 0.82rem; color: #cbd5e1; line-height: 1.6;">
                <div style="display: flex; justify-content: space-between;">
                    <span style="color: #94a3b8;">Database:</span>
                    <strong style="color: #38bdf8;">{db_name}</strong>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span style="color: #94a3b8;">Tables:</span>
                    <span>{len(db_meta['tables'])} tables</span>
                </div>
                <div style="display: flex; justify-content: space-between;">
                    <span style="color: #94a3b8;">Total Records:</span>
                    <span>{db_meta['total_rows']} rows</span>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # 2. SESSION QUESTIONS COUNTER & AI ENGINE CARD
    user_questions_count = len([m for m in st.session_state.messages if m.get("role") == "user"])
    
    st.markdown(f"""
        <div style="background: rgba(15, 23, 42, 0.7); border: 1px solid rgba(56, 189, 248, 0.2); border-radius: 12px; padding: 14px; margin-bottom: 16px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span style="font-size: 0.75rem; font-weight: 700; color: #94a3b8; letter-spacing: 0.05em;">SESSION METRICS</span>
                <span style="background: rgba(56, 189, 248, 0.15); border: 1px solid rgba(56, 189, 248, 0.3); color: #38bdf8; font-weight: 700; font-size: 0.8rem; padding: 2px 8px; border-radius: 10px;">
                    {user_questions_count} {'Questions' if user_questions_count != 1 else 'Question'}
                </span>
            </div>
            <div style="font-size: 0.8rem; color: #cbd5e1;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="color: #94a3b8;">AI Engine:</span>
                    <span style="color: #a78bfa; font-weight: 600; font-family: 'JetBrains Mono', monospace; font-size: 0.75rem;">{DEFAULT_GROQ_MODEL.split('/')[-1]}</span>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Quick Starters
    st.markdown("<div style='font-size: 0.78rem; font-weight: 700; color: #94a3b8; letter-spacing: 0.05em; margin-bottom: 8px;'>TRY SAMPLE PROMPTS</div>", unsafe_allow_html=True)

    quick_prompts = [
        ("👥 Top Paid Talent", "Show the top 3 employees with highest salary and their department names."),
        ("📊 Category Revenue", "Calculate total revenue by product category from the orders table."),
        ("🎓 CS Honor Roll", "List all students in Computer Science with marks > 85 ordered by marks desc."),
        ("🛒 High Value Orders", "Find users from Delhi who placed orders greater than $500.")
    ]

    for label, query in quick_prompts:
        if st.button(label, key=f"side_{label}", use_container_width=True):
            st.session_state.pending_prompt = query

    st.markdown("---")

    # Essential Actions Only
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        if st.button("🔄 Sync DB", use_container_width=True, help="Refresh database schema cache"):
            st.cache_data.clear()
            st.rerun()
    with col_s2:
        if st.button("🗑️ Reset Chat", use_container_width=True):
            if "thread_id" in st.session_state:
                reset_agent_memory(st.session_state.thread_id)
            st.session_state.thread_id = str(uuid.uuid4())
            st.session_state.messages = []
            st.session_state.pending_prompt = None
            st.rerun()

    # Seed Database expander
    with st.expander("🌱 Seed Sample Data", expanded=False):
        st.caption("Populate sample tables (employees, departments, orders, products, students, users).")
        if st.button("Seed Database", type="primary", use_container_width=True):
            with st.spinner("Seeding..."):
                ok, msg = seed_database()
                if ok:
                    st.success("Seeded!")
                    st.cache_data.clear()
                    time.sleep(0.8)
                    st.rerun()
                else:
                    st.error(msg)


# ==============================================================================
# 4. SHOWCASE HERO HEADER
# ==============================================================================
status_html = '<span class="pill-badge pill-active"><span class="pulse-dot"></span> PostgreSQL Online</span>' if db_meta["healthy"] else '<span class="pill-badge" style="background: rgba(239,68,68,0.15); color: #f87171;">Offline</span>'

st.markdown(f"""
    <div class="cyber-header">
        <div>
            <div class="brand-glow">⚡ ZeroSQL</div>
            <div style="font-size: 0.88rem; color: #cbd5e1; margin-top: 3px; font-weight: 500;">
                <span style="color: #38bdf8; font-weight: 700;">Don't know SQL? Haha, don't worry!</span> Just tell me what you want in any language — I'll get it for you. ⚡
            </div>
        </div>
        <div style="display: flex; gap: 8px; flex-wrap: wrap; align-items: center;">
            {status_html}
            <span class="pill-badge pill-model">📦 {len(db_meta['tables'])} Tables</span>
            <span class="pill-badge pill-active">🛡️ Read-Only</span>
        </div>
    </div>
""", unsafe_allow_html=True)


# ==============================================================================
# 5. CORE INTERACTION TABS
# ==============================================================================
tab_assistant, tab_hub, tab_explorer, tab_lab, tab_admin = st.tabs([
    "💬 Plain English Copilot",
    "🌐 Dataset Hub",
    "📊 Data Matrix (Explorer)",
    "⚡ SQL Query Lab",
    "⚙️ Admin Hub"
])


# ------------------------------------------------------------------------------
# TAB 1: NEURAL CHAT & ANALYTICS
# ------------------------------------------------------------------------------
with tab_assistant:
    # --------------------------------------------------------------------------
    # ACTIVE DATASET & DYNAMIC PROMPT SUGGESTIONS BAR
    # --------------------------------------------------------------------------
    ready_datasets = []
    try:
        resp_all = call_backend_api("GET", "/api/v1/admin/datasets")
        if resp_all.status_code == 200:
            all_ds = resp_all.json().get("datasets", [])
            ready_datasets = [d for d in all_ds if d.get("processing_status") == "READY" and d.get("table_name")]
    except Exception:
        ready_datasets = []

    ds_options = {"ALL": "🌐 All Database Tables (Full Schema)"}
    ds_lookup = {}
    for d in ready_datasets:
        ds_options[d["dataset_id"]] = f"📊 {d['dataset_name']} (Table: {d['table_name']})"
        ds_lookup[d["dataset_id"]] = d

    # Ensure selected_dataset_id is valid
    if st.session_state.selected_dataset_id not in ds_options:
        st.session_state.selected_dataset_id = "ALL"

    top_c1, top_c2 = st.columns([3, 1])
    with top_c1:
        chosen_ds_id = st.selectbox(
            "Active Dataset Context",
            options=list(ds_options.keys()),
            format_func=lambda k: ds_options[k],
            index=list(ds_options.keys()).index(st.session_state.selected_dataset_id),
            key="ds_selector_dropdown",
            help="Select a dataset to focus queries and see automatic one-click question suggestions."
        )
        if chosen_ds_id != st.session_state.selected_dataset_id:
            st.session_state.selected_dataset_id = chosen_ds_id
            st.rerun()

    with top_c2:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        if st.button("🔄 Refresh Schema", use_container_width=True, help="Force refresh database table and schema caches"):
            st.cache_data.clear()
            st.success("Schema cache refreshed!")
            time.sleep(0.4)
            st.rerun()

    active_table_name = None
    active_dataset = ds_lookup.get(st.session_state.selected_dataset_id)
    if active_dataset:
        active_table_name = active_dataset.get("table_name")
        prompts = active_dataset.get("suggested_prompts") or []

        # Render Active Dataset Badge & Suggested Prompts Card
        st.markdown(f"""
            <div style="background: rgba(15, 23, 42, 0.85); border: 1px solid rgba(56, 189, 248, 0.35); border-radius: 10px; padding: 12px 16px; margin: 8px 0 14px 0;">
                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; margin-bottom: 8px;">
                    <div>
                        <span style="font-weight: 700; color: #38bdf8; font-size: 0.92rem;">📊 ACTIVE DATASET:</span>
                        <span style="font-weight: 600; color: #f8fafc; font-size: 0.92rem; margin-left: 6px;">{active_dataset.get('dataset_name')}</span>
                        <span style="color: #94a3b8; font-size: 0.8rem; margin-left: 8px;">(Table: <code>{active_table_name}</code> • {active_dataset.get('row_count')} rows)</span>
                    </div>
                    <span class="pill-badge pill-active">⚡ AI-READY</span>
                </div>
                <div style="font-size: 0.82rem; font-weight: 600; color: #cbd5e1; margin-bottom: 6px;">💡 ONE-CLICK SUGGESTED QUESTIONS:</div>
            </div>
        """, unsafe_allow_html=True)

        if prompts:
            p_cols = st.columns(2)
            for p_idx, p_text in enumerate(prompts):
                target_col = p_cols[p_idx % 2]
                with target_col:
                    if st.button(f"👉 {p_text}", key=f"sug_btn_{active_dataset['dataset_id']}_{p_idx}", use_container_width=True):
                        st.session_state.pending_prompt = p_text
                        st.rerun()
        else:
            st.caption("Suggested questions are temporarily unavailable. You can still ask your own question below.")

    # Empty State Hero when no messages yet and no specific dataset selected
    elif not st.session_state.messages and not st.session_state.pending_prompt:
        st.markdown("<div style='margin: 16px 0 12px 0; font-size: 0.95rem; font-weight: 600; color: #cbd5e1;'>✨ Ask anything or pick a quick starter below:</div>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("👥 Highest Paid Employees\n\nShow the top 3 highest earning employees with their department names", key="hero_prompt_1", use_container_width=True):
                st.session_state.pending_prompt = "Show the top 3 highest earning employees with their department names."
                st.rerun()
            if st.button("📊 Category Revenue Breakdown\n\nCalculate total sales revenue generated across each product category", key="hero_prompt_2", use_container_width=True):
                st.session_state.pending_prompt = "Calculate total sales revenue generated across each product category."
                st.rerun()
        with col2:
            if st.button("🎓 CS Honor Students\n\nList all students in Computer Science with marks > 85 ordered by marks desc", key="hero_prompt_3", use_container_width=True):
                st.session_state.pending_prompt = "List all students in Computer Science with marks > 85 ordered by marks desc."
                st.rerun()
            if st.button("🛒 High Value Orders in Delhi\n\nFind all users from Delhi who have placed orders with total amount > $200", key="hero_prompt_4", use_container_width=True):
                st.session_state.pending_prompt = "Find all users from Delhi who have placed orders with total amount > $200."
                st.rerun()

    # Render Chat History
    for idx, msg in enumerate(st.session_state.messages):
        role = msg.get("role", "user")
        with st.chat_message(role, avatar="🧑‍💻" if role == "user" else "⚡"):
            if role == "user":
                st.markdown(f"**{msg['content']}**")
            else:
                st.markdown(msg.get("answer", ""))

                if msg.get("sql_query"):
                    st.code(msg["sql_query"], language="sql")

                if msg.get("df_json"):
                    try:
                        df_hist = pd.read_json(msg["df_json"])
                        if not df_hist.empty:
                            st.dataframe(df_hist, use_container_width=True)
                            render_auto_chart(df_hist, key_id=f"hist_{idx}")
                    except Exception:
                        pass

    # Check for prompt from input or button trigger
    prompt_input = st.chat_input("Ask a question about your database in plain English...")
    active_prompt = None

    if prompt_input:
        active_prompt = prompt_input
    elif st.session_state.pending_prompt:
        active_prompt = st.session_state.pending_prompt
        st.session_state.pending_prompt = None

    if active_prompt:
        # Display and record User Message
        st.session_state.messages.append({"role": "user", "content": active_prompt})
        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown(f"**{active_prompt}**")

        # Query Assistant
        with st.chat_message("assistant", avatar="⚡"):
            with st.status("⚡ Neural Agent reasoning & executing...", expanded=True) as status_box:
                try:
                    t_start = time.time()
                    response = ask_agent(
                        user_question=active_prompt,
                        thread_id=st.session_state.thread_id,
                        model_name=DEFAULT_GROQ_MODEL,
                        temperature=HARDCODED_TEMPERATURE,
                        active_table=active_table_name
                    )
                    latency = round(time.time() - t_start, 2)
                    status_box.update(label=f"✅ Query complete ({latency}s)", state="complete", expanded=False)

                    answer = response.get("answer", "")
                    sql_query = response.get("sql_query")
                    val_passed = response.get("validation_passed", True)
                    query_result = response.get("query_result")

                    # Display Answer
                    st.markdown(answer)

                    # Display SQL & Data Table (Directly reusing single database execution result)
                    df_to_save = None
                    if sql_query:
                        st.markdown("<div style='font-size: 0.78rem; font-weight: 600; color: #38bdf8; margin: 8px 0 4px 0;'>⚡ EXECUTED SQL QUERY</div>", unsafe_allow_html=True)
                        st.code(sql_query, language="sql")

                        if val_passed:
                            if query_result and query_result.get("rows"):
                                rows = query_result["rows"]
                                df_res = pd.DataFrame(rows)
                                df_to_save = df_res
                                duration_ms = query_result.get("execution_time_ms", 0.0)
                                st.markdown(f"<div style='font-size: 0.8rem; color: #94a3b8; margin: 8px 0 4px 0;'>📊 Retrieved Data ({len(df_res)} rows • {duration_ms}ms)</div>", unsafe_allow_html=True)
                                st.dataframe(df_res, use_container_width=True)

                                # Auto Charts
                                render_auto_chart(df_res, key_id="live")

                                # CSV Export
                                csv_bytes = df_res.to_csv(index=False).encode("utf-8")
                                st.download_button("📥 Export CSV", data=csv_bytes, file_name="query_result.csv", mime="text/csv", key="dl_live_csv")
                            elif query_result and query_result.get("row_count") == 0 and not query_result.get("error"):
                                st.info("Query executed successfully. Result: 0 rows returned.")
                            elif query_result and query_result.get("error"):
                                st.error(f"Execution Error: {query_result.get('error')}")
                        else:
                            st.error("⚠️ Security Alert: Query blocked by validator guardrails.")

                    # Save Assistant interaction
                    st.session_state.messages.append({
                        "role": "assistant",
                        "answer": answer,
                        "sql_query": sql_query,
                        "validation_passed": val_passed,
                        "df_json": df_to_save.to_json() if df_to_save is not None else None
                    })

                except Exception as err:
                    status_box.update(label="❌ Query failed", state="error")
                    st.error(f"Error: {str(err)}")

    # Bottom Spacer to guarantee chat content is never covered by the sticky input bar
    st.markdown("<div class='chat-bottom-spacer'></div>", unsafe_allow_html=True)


# ------------------------------------------------------------------------------
# TAB 2: POPULAR DATASET HUB & AI RECOMMENDATIONS
# ------------------------------------------------------------------------------
with tab_hub:
    st.markdown("""
        <div style="margin-bottom: 16px;">
            <div style="font-size: 1.25rem; font-weight: 700; color: #f8fafc;">🌐 Popular Dataset Hub & AI Recommendations</div>
            <div style="font-size: 0.85rem; color: #94a3b8;">
                Explore real public datasets across popular industries, ask for intelligent recommendations, and provision them instantly into the AI SQL Agent.
            </div>
        </div>
    """, unsafe_allow_html=True)

    # 1. AI RECOMMENDATION ASSISTANT SECTION
    st.markdown("""
        <div style="background: rgba(30, 41, 59, 0.6); border: 1px solid rgba(56, 189, 248, 0.25); border-radius: 12px; padding: 16px; margin-bottom: 20px;">
            <div style="font-size: 0.98rem; font-weight: 700; color: #38bdf8; margin-bottom: 4px;">🤖 AI Dataset Recommendation Assistant</div>
            <div style="font-size: 0.82rem; color: #cbd5e1; margin-bottom: 10px;">
                Describe what you want to analyze or practice (e.g. <i>"sales and profit trends"</i>, <i>"customer retention churn"</i>, <i>"employee compensation"</i>):
            </div>
        </div>
    """, unsafe_allow_html=True)

    rec_c1, rec_c2 = st.columns([3.5, 1])
    with rec_c1:
        rec_query = st.text_input("Analytical Goal / Question", placeholder="e.g. I want to practice retail sales, revenue, and regional trends...", label_visibility="collapsed", key="hub_rec_input")
    with rec_c2:
        rec_btn = st.button("✨ Recommend Datasets", type="primary", use_container_width=True, key="hub_rec_btn")

    if rec_query and (rec_btn or st.session_state.get("last_rec_query") == rec_query):
        st.session_state["last_rec_query"] = rec_query
        try:
            r_rec = call_backend_api("POST", "/api/v1/datasets/recommendations", json={"query": rec_query, "limit": 3})
            if r_rec.status_code == 200:
                rec_data = r_rec.json()
                recs = rec_data.get("recommended_datasets", [])
                reasoning = rec_data.get("reasoning", "")
                if recs:
                    st.markdown(f"<div style='font-size: 0.85rem; font-weight: 600; color: #4ade80; margin: 10px 0 6px 0;'>💡 Top Recommendations for: \"{rec_query}\"</div>", unsafe_allow_html=True)
                    r_cols = st.columns(len(recs))
                    for r_idx, r_ds in enumerate(recs):
                        with r_cols[r_idx]:
                            st.markdown(f"""
                                <div style="background: rgba(15, 23, 42, 0.9); border: 1px solid rgba(74, 222, 128, 0.4); border-radius: 10px; padding: 14px; min-height: 140px;">
                                    <div style="font-size: 0.92rem; font-weight: 700; color: #f8fafc; margin-bottom: 4px;">{r_ds.get('name')}</div>
                                    <div style="font-size: 0.78rem; color: #94a3b8; margin-bottom: 8px;">{r_ds.get('description', '')[:95]}...</div>
                                    <div style="font-size: 0.75rem; color: #38bdf8; margin-bottom: 10px;">🏷️ {', '.join(r_ds.get('analytics_topics', [])[:2])}</div>
                                </div>
                            """, unsafe_allow_html=True)
                            if st.button(f"⚡ Use Dataset", key=f"btn_rec_use_{r_ds['catalog_id']}", use_container_width=True, type="secondary"):
                                with st.spinner(f"Loading '{r_ds['name']}' into PostgreSQL..."):
                                    u_resp = call_backend_api("POST", f"/api/v1/datasets/catalog/{r_ds['catalog_id']}/use")
                                    if u_resp.status_code == 200:
                                        u_data = u_resp.json()
                                        st.session_state.selected_dataset_id = u_data["dataset_id"]
                                        st.cache_data.clear()
                                        st.success(f"🎉 '{r_ds['name']}' is now loaded & active! Switch to Plain English Copilot tab to query.")
                                        time.sleep(1.0)
                                        st.rerun()
                                    else:
                                        st.error(f"Failed to use dataset: {u_resp.text}")
                else:
                    st.info("No matching datasets found for your query. Browse the catalog below.")
            else:
                st.error(f"Recommendation API error: {r_rec.text}")
        except Exception as e:
            st.warning(f"Could not load recommendations: {str(e)}")

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # 2. POPULAR DATASET CATALOG BROWSER
    st.markdown("#### 🔥 Curated Popular Datasets")

    # Category Filter Bar
    cat_resp = call_backend_api("GET", "/api/v1/datasets/catalog/categories")
    categories_list = ["All Categories"]
    if cat_resp.status_code == 200:
        for c in cat_resp.json().get("categories", []):
            categories_list.append(c["name"])

    chosen_cat = st.selectbox("Filter by Category", options=categories_list, key="hub_category_filter")
    effective_cat = None if chosen_cat == "All Categories" else chosen_cat

    # Fetch Catalog Datasets
    params = {"category": effective_cat} if effective_cat else {}
    cat_data_resp = call_backend_api("GET", "/api/v1/datasets/catalog", params=params)

    if cat_data_resp.status_code == 200:
        catalog_datasets = cat_data_resp.json().get("datasets", [])
        if not catalog_datasets:
            st.info("No datasets found in this category.")
        else:
            for i in range(0, len(catalog_datasets), 2):
                col_a, col_b = st.columns(2)
                pair = [catalog_datasets[i]]
                if i + 1 < len(catalog_datasets):
                    pair.append(catalog_datasets[i + 1])

                for col_idx, ds_item in enumerate(pair):
                    target_col = col_a if col_idx == 0 else col_b
                    with target_col:
                        is_imported = ds_item.get("is_imported", False)
                        imported_tbl = ds_item.get("imported_table_name")
                        status_badge = f'<span class="pill-badge pill-active">🟢 Active Table: {imported_tbl}</span>' if is_imported else '<span class="pill-badge pill-model">⚪ Available</span>'
                        topics_html = " ".join([f'<span class="pill-badge" style="font-size: 0.72rem; padding: 2px 6px;">{t}</span>' for t in ds_item.get("analytics_topics", [])])

                        st.markdown(f"""
                            <div style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(51, 65, 85, 0.8); border-radius: 12px; padding: 16px; margin-bottom: 12px; min-height: 220px; display: flex; flex-direction: column; justify-content: space-between;">
                                <div>
                                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 6px;">
                                        <div style="font-size: 1.02rem; font-weight: 700; color: #f8fafc;">
                                            {ds_item.get('name')}
                                        </div>
                                        {status_badge}
                                    </div>
                                    <div style="font-size: 0.8rem; color: #94a3b8; margin-bottom: 8px; line-height: 1.35;">
                                        {ds_item.get('description')}
                                    </div>
                                    <div style="font-size: 0.75rem; color: #64748b; margin-bottom: 8px;">
                                        <b>Category:</b> {ds_item.get('category')} &nbsp;•&nbsp; 
                                        <b>Format:</b> {ds_item.get('file_format', 'CSV').upper()} &nbsp;•&nbsp; 
                                        <b>Source:</b> <a href="{ds_item.get('source_url', '#')}" target="_blank" style="color: #38bdf8; text-decoration: none;">{ds_item.get('source_name')}</a>
                                    </div>
                                </div>
                                <div style="margin-top: 6px;">
                                    <div style="font-size: 0.72rem; font-weight: 600; color: #cbd5e1; margin-bottom: 6px;">Key Topics: {topics_html}</div>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)

                        btn_label = f"🎯 Select Active Dataset" if is_imported else f"⚡ Use Dataset"
                        if st.button(btn_label, key=f"hub_use_btn_{ds_item['catalog_id']}", use_container_width=True, type="primary" if not is_imported else "secondary"):
                            with st.spinner(f"Loading '{ds_item['name']}' through unified pipeline..."):
                                use_r = call_backend_api("POST", f"/api/v1/datasets/catalog/{ds_item['catalog_id']}/use")
                                if use_r.status_code == 200:
                                    u_res = use_r.json()
                                    st.session_state.selected_dataset_id = u_res["dataset_id"]
                                    st.cache_data.clear()
                                    st.success(f"🎉 '{ds_item['name']}' is ready! Table '{u_res['table_name']}' is now the Active Dataset context.")
                                    time.sleep(1.0)
                                    st.rerun()
                                else:
                                    st.error(f"Error loading dataset: {use_r.text}")
    else:
        st.error(f"Failed to load dataset catalog: {cat_data_resp.text}")

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # 3. UPLOAD YOUR OWN DATASET CALL-TO-ACTION
    st.markdown("""
        <div style="background: rgba(30, 41, 59, 0.4); border: 1px dashed rgba(148, 163, 184, 0.3); border-radius: 12px; padding: 16px; text-align: center; margin-top: 14px;">
            <div style="font-size: 0.95rem; font-weight: 700; color: #f8fafc; margin-bottom: 4px;">📤 Have Your Own Custom Dataset?</div>
            <div style="font-size: 0.82rem; color: #94a3b8; margin-bottom: 10px;">
                Upload CSV, XLSX, JSON, or Parquet datasets with automated cleaning, schema type inference, and dynamic table creation.
            </div>
            <div style="font-size: 0.8rem; color: #38bdf8; font-weight: 600;">
                👉 Switch to the <b>⚙️ Admin Hub</b> tab to upload and manage custom datasets.
            </div>
        </div>
    """, unsafe_allow_html=True)


# ------------------------------------------------------------------------------
# TAB 3: DATA MATRIX (SCHEMA & TABLE EXPLORER)
# ------------------------------------------------------------------------------
with tab_explorer:
    if not db_meta["healthy"]:
        st.warning("PostgreSQL is currently disconnected.")
    elif not db_meta["tables"]:
        st.info("No tables detected. Click 'Seed Sample Data' in the sidebar to populate.")
    else:
        tbl_col1, tbl_col2 = st.columns([1, 2.5])

        with tbl_col1:
            st.markdown("<div style='font-size: 0.85rem; font-weight: 600; color: #94a3b8; margin-bottom: 8px;'>SELECT TABLE</div>", unsafe_allow_html=True)
            chosen_tbl = st.selectbox(
                "Table",
                options=db_meta["tables"],
                format_func=lambda t: f"📁 {t} ({db_meta['counts'].get(t, 0)} rows)",
                label_visibility="collapsed"
            )

            if chosen_tbl:
                cols_data = get_table_details(chosen_tbl)
                if cols_data:
                    st.markdown(f"<div style='font-size: 0.82rem; font-weight: 600; color: #38bdf8; margin: 12px 0 6px 0;'>STRUCTURE: {chosen_tbl}</div>", unsafe_allow_html=True)
                    st.dataframe(pd.DataFrame(cols_data), use_container_width=True, hide_index=True)

                if st.button(f"⚡ Analyze `{chosen_tbl}` with AI", use_container_width=True):
                    st.session_state.pending_prompt = f"Analyze the data in the '{chosen_tbl}' table and give me key insights."
                    st.rerun()

        with tbl_col2:
            if chosen_tbl:
                st.markdown(f"<div style='font-size: 0.85rem; font-weight: 600; color: #94a3b8; margin-bottom: 8px;'>LIVE RECORDS: {chosen_tbl}</div>", unsafe_allow_html=True)
                ok, df_preview, _ = execute_sql_safe(f'SELECT * FROM "{chosen_tbl}" LIMIT 50;')
                if ok and df_preview is not None:
                    st.dataframe(df_preview, use_container_width=True)
                    csv_tbl = df_preview.to_csv(index=False).encode("utf-8")
                    st.download_button(f"📥 Download {chosen_tbl}.csv", data=csv_tbl, file_name=f"{chosen_tbl}.csv", mime="text/csv")


# ------------------------------------------------------------------------------
# TAB 3: SQL QUERY LAB (PLAYGROUND)
# ------------------------------------------------------------------------------
with tab_lab:
    st.markdown("<div style='font-size: 0.88rem; color: #94a3b8; margin-bottom: 12px;'>Execute custom read-only SQL queries with instant latency measurement and AI breakdown.</div>", unsafe_allow_html=True)

    templates = {
        "Top Salaries": "SELECT id, name, salary FROM employees ORDER BY salary DESC LIMIT 5;",
        "Employees & Departments Join": """SELECT e.name, e.salary, d.name AS department, d.location
FROM employees e
JOIN departments d ON e.department_id = d.id
ORDER BY e.salary DESC;""",
        "Category Revenue Aggregation": """SELECT p.category, COUNT(o.id) AS orders_count, SUM(o.total_amount) AS revenue
FROM orders o
JOIN products p ON o.product_id = p.id
GROUP BY p.category
ORDER BY revenue DESC;"""
    }

    c_temp, _ = st.columns([2, 1])
    with c_temp:
        selected_temp = st.selectbox("Load Sample Query:", list(templates.keys()))

    manual_sql = st.text_area("SQL Statement (Read-Only SELECT / WITH):", value=templates[selected_temp], height=120)

    btn_c1, btn_c2, _ = st.columns([1, 1, 2])
    with btn_c1:
        run_query = st.button("▶️ Execute", type="primary", use_container_width=True)
    with btn_c2:
        explain_query = st.button("🤖 Explain SQL", use_container_width=True)

    if run_query and manual_sql:
        ok, res_df, status_msg = execute_sql_safe(manual_sql)
        if ok and res_df is not None:
            st.success(status_msg)
            st.dataframe(res_df, use_container_width=True)
            render_auto_chart(res_df, key_id="manual")
        else:
            st.error(status_msg)

    if explain_query and manual_sql:
        with st.spinner("AI analyzing SQL logic..."):
            prompt = f"Explain this SQL query concisely, break down the logic, and suggest any performance tips:\n\n```sql\n{manual_sql}\n```"
            res = ask_agent(prompt, model_name=DEFAULT_GROQ_MODEL, temperature=HARDCODED_TEMPERATURE)
            st.markdown("### 💡 AI Query Breakdown")
            st.markdown(res.get("answer", "Unable to analyze."))


# ------------------------------------------------------------------------------
# TAB 4: SECURE ADMIN DATASET MANAGEMENT (V2 STEP 2)
# ------------------------------------------------------------------------------
with tab_admin:
    st.markdown("""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
            <div>
                <div style="font-size: 1.25rem; font-weight: 800; color: #f8fafc; font-family: 'Space Grotesk', sans-serif;">
                    ⚙️ ADMIN DATASET MANAGEMENT
                </div>
                <div style="font-size: 0.82rem; color: #94a3b8;">
                    Secure dataset ingestion, schema tracking, and metadata administration via FastAPI backend.
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Check authentication state
    is_authenticated = bool(st.session_state.get("admin_token"))

    if not is_authenticated:
        # Show Admin Login Box
        st.markdown("""
            <div style="background: rgba(15, 23, 42, 0.75); border: 1px solid rgba(56, 189, 248, 0.25); border-radius: 14px; padding: 24px; max-width: 480px; margin: 20px auto; backdrop-filter: blur(16px); box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);">
                <div style="font-size: 1.1rem; font-weight: 700; color: #38bdf8; margin-bottom: 8px; display: flex; align-items: center; gap: 8px;">
                    🔒 Admin Authentication Required
                </div>
                <div style="font-size: 0.82rem; color: #94a3b8; margin-bottom: 16px;">
                    Enter your administrator credentials to access dataset ingestion and deletion controls.
                </div>
            </div>
        """, unsafe_allow_html=True)

        col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
        with col_l2:
            with st.form("admin_login_form"):
                admin_user_input = st.text_input("Username", value="", placeholder="e.g. admin")
                admin_pass_input = st.text_input("Password", type="password", placeholder="••••••••")
                login_submitted = st.form_submit_button("🔑 Authenticate & Enter", type="primary", use_container_width=True)

                if login_submitted:
                    if not admin_user_input or not admin_pass_input:
                        st.error("Please enter both username and password.")
                    else:
                        resp = call_backend_api(
                            "POST",
                            "/api/v1/admin/auth/login",
                            json={"username": admin_user_input, "password": admin_pass_input}
                        )
                        if resp.status_code == 200:
                            data = resp.json()
                            st.session_state.admin_token = data.get("access_token")
                            st.session_state.admin_user = data.get("username", admin_user_input)
                            st.success(f"Authenticated successfully as {st.session_state.admin_user}!")
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("Invalid credentials. Access denied.")

    else:
        # Authenticated Admin View
        top_c1, top_c2 = st.columns([3, 1])
        with top_c1:
            st.markdown(f"""
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 14px;">
                    <span class="pill-badge pill-active"><span class="pulse-dot"></span> Authenticated as <strong>{st.session_state.admin_user}</strong></span>
                    <span class="pill-badge pill-model">🛡️ Admin Role Active</span>
                </div>
            """, unsafe_allow_html=True)
        with top_c2:
            if st.button("🚪 Log Out", use_container_width=True):
                st.session_state.admin_token = None
                st.session_state.admin_user = None
                st.session_state.last_upload_result = None
                st.rerun()

        st.markdown("---")

        # ----------------------------------------------------------------------
        # 1. UPLOAD DATASET SECTION
        # ----------------------------------------------------------------------
        st.markdown("""
            <div style="font-size: 1.05rem; font-weight: 700; color: #f1f5f9; margin-bottom: 6px;">
                📤 Upload Dataset
            </div>
            <div style="font-size: 0.82rem; color: #94a3b8; margin-bottom: 12px;">
                Supported Formats: <span style="color: #38bdf8; font-weight: 600;">CSV</span> | <span style="color: #38bdf8; font-weight: 600;">XLSX</span> | <span style="color: #38bdf8; font-weight: 600;">JSON</span> | <span style="color: #38bdf8; font-weight: 600;">Parquet</span> (Max 50MB)
            </div>
        """, unsafe_allow_html=True)

        up_col1, up_col2 = st.columns([2, 1])
        with up_col1:
            uploaded_file = st.file_uploader(
                "Choose a dataset file",
                type=["csv", "xlsx", "json", "parquet"],
                help="Select a CSV, Excel, JSON, or Parquet dataset file for secure storage and metadata registration."
            )
        with up_col2:
            custom_name = st.text_input(
                "Dataset Display Name (Optional)",
                placeholder="e.g. Q1 Sales Report",
                help="Custom title for easy reference in metadata."
            )
            upload_btn = st.button("⚡ Upload & Validate Dataset", type="primary", use_container_width=True, disabled=(uploaded_file is None))

        if upload_btn and uploaded_file is not None:
            with st.spinner("Uploading and validating file via FastAPI..."):
                file_bytes = uploaded_file.getvalue()
                files = {"file": (uploaded_file.name, file_bytes, uploaded_file.type or "application/octet-stream")}
                data = {"dataset_name": custom_name} if custom_name else {}

                resp = call_backend_api(
                    "POST",
                    "/api/v1/admin/datasets/upload",
                    files=files,
                    data=data
                )

                if resp.status_code == 201:
                    res_json = resp.json()
                    st.session_state.last_upload_result = res_json.get("dataset")
                    st.success(res_json.get("message", "Dataset uploaded successfully!"))
                else:
                    err_msg = resp.json().get("detail", "Upload failed.") if resp.headers.get("content-type", "").startswith("application/json") else resp.text
                    st.error(f"Upload Error: {err_msg}")

        # Show Last Upload Result Card
        if st.session_state.get("last_upload_result"):
            last_ds = st.session_state.last_upload_result
            st.markdown(f"""
                <div style="background: rgba(56, 189, 248, 0.08); border: 1px solid rgba(56, 189, 248, 0.3); border-radius: 12px; padding: 14px; margin: 12px 0;">
                    <div style="font-size: 0.85rem; font-weight: 700; color: #38bdf8; margin-bottom: 8px;">✅ LATEST UPLOAD REGISTERED</div>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 10px; font-size: 0.8rem; color: #cbd5e1;">
                        <div><strong style="color: #94a3b8;">Dataset:</strong> {last_ds.get('dataset_name')}</div>
                        <div><strong style="color: #94a3b8;">File:</strong> {last_ds.get('original_filename')}</div>
                        <div><strong style="color: #94a3b8;">Format:</strong> <span class="pill-badge pill-model">{last_ds.get('file_format', '').upper()}</span></div>
                        <div><strong style="color: #94a3b8;">Size:</strong> {last_ds.get('file_size_formatted')}</div>
                        <div><strong style="color: #94a3b8;">Status:</strong> <span class="pill-badge pill-active">{last_ds.get('processing_status')}</span></div>
                        <div><strong style="color: #94a3b8;">ID:</strong> <code>{last_ds.get('dataset_id')}</code></div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # ----------------------------------------------------------------------
        # 2. EXISTING DATASETS REPOSITORY
        # ----------------------------------------------------------------------
        st.markdown("""
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                <div style="font-size: 1.05rem; font-weight: 700; color: #f1f5f9;">📚 Existing Datasets</div>
            </div>
        """, unsafe_allow_html=True)

        # Fetch dataset list via FastAPI
        resp_list = call_backend_api("GET", "/api/v1/admin/datasets")
        if resp_list.status_code == 200:
            dataset_list_data = resp_list.json().get("datasets", [])
            if not dataset_list_data:
                st.info("No datasets uploaded yet. Upload a dataset using the form above.")
            else:
                for ds in dataset_list_data:
                    ds_id = ds["dataset_id"]
                    status_str = ds["processing_status"]
                    is_ready = status_str == "READY"
                    is_failed = status_str == "FAILED"
                    proc_info = st.session_state.processed_datasets.get(ds_id)

                    with st.container():
                        badge_color = "pill-active" if is_ready else ("pill-badge" if not is_failed else "pill-nosql")
                        st.markdown(f"""
                            <div style="background: rgba(15, 23, 42, 0.65); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 10px; padding: 12px 16px; margin-bottom: 8px;">
                                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
                                    <div>
                                        <span style="font-weight: 700; color: #f8fafc; font-size: 0.95rem;">{ds['dataset_name']}</span>
                                        <span style="font-size: 0.78rem; color: #94a3b8; margin-left: 8px;">({ds['original_filename']})</span>
                                        {f"<span style='font-size: 0.78rem; color: #38bdf8; margin-left: 8px;'>📁 Table: <code>{ds['table_name']}</code> ({ds['row_count']} rows)</span>" if is_ready else ""}
                                    </div>
                                    <div style="display: flex; gap: 6px; align-items: center;">
                                        <span class="pill-badge pill-model">{ds['file_format'].upper()}</span>
                                        <span class="pill-badge" style="background: rgba(255,255,255,0.06); color: #cbd5e1;">{ds['file_size_formatted']}</span>
                                        <span class="pill-badge {badge_color}">{status_str}</span>
                                    </div>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)

                        # Action Toolbar
                        c_act1, c_act2, c_act3, _ = st.columns([1.5, 1.2, 1, 3])
                        with c_act1:
                            if not is_ready:
                                if st.button("⚡ Process & Analyze", key=f"proc_btn_{ds_id}", type="primary", use_container_width=True):
                                    with st.spinner("Parsing, cleaning, and profiling dataset..."):
                                        p_resp = call_backend_api("POST", f"/api/v1/admin/datasets/{ds_id}/process")
                                        if p_resp.status_code == 200:
                                            st.session_state.processed_datasets[ds_id] = p_resp.json()
                                            st.success("Analysis complete! Review preview and schema below.")
                                            st.rerun()
                                        else:
                                            st.error(f"Processing failed: {p_resp.text}")
                        with c_act2:
                            with st.expander("🔍 Metadata", expanded=False):
                                st.json({
                                    "dataset_id": ds["dataset_id"],
                                    "dataset_name": ds["dataset_name"],
                                    "original_filename": ds["original_filename"],
                                    "file_format": ds["file_format"],
                                    "file_size": ds["file_size_formatted"],
                                    "upload_timestamp": ds["upload_timestamp"],
                                    "processing_status": ds["processing_status"],
                                    "destination_table": ds.get("table_name") or "Pending Table Creation",
                                    "row_count": ds.get("row_count"),
                                    "column_count": ds.get("column_count")
                                })
                        with c_act3:
                            if st.button("🗑️ Delete", key=f"del_{ds_id}", type="secondary", use_container_width=True):
                                del_resp = call_backend_api("DELETE", f"/api/v1/admin/datasets/{ds_id}")
                                if del_resp.status_code == 200:
                                    st.session_state.processed_datasets.pop(ds_id, None)
                                    st.success(f"Dataset deleted!")
                                    time.sleep(0.5)
                                    st.rerun()
                                else:
                                    st.error("Failed to delete dataset.")

                        # Show Step 3 Ingestion Preview, Cleaning Report & Confirmation if processed
                        if proc_info:
                            st.markdown(f"""
                                <div style="background: rgba(15, 23, 42, 0.9); border: 1.5px solid rgba(56, 189, 248, 0.4); border-radius: 12px; padding: 18px; margin: 12px 0 20px 0;">
                                    <div style="font-size: 1.05rem; font-weight: 700; color: #38bdf8; margin-bottom: 12px;">
                                        📋 DATASET ANALYSIS & INGESTION PREVIEW: {ds['dataset_name']}
                                    </div>
                                </div>
                            """, unsafe_allow_html=True)

                            # 1. Preview Table
                            prev = proc_info.get("preview", {})
                            st.markdown(f"**📊 DATA PREVIEW** — Total Rows: `{prev.get('total_rows')}` | Total Columns: `{prev.get('total_columns')}` (Showing first {prev.get('preview_rows')} rows)")
                            if prev.get("records"):
                                st.dataframe(pd.DataFrame(prev["records"]), use_container_width=True)

                            # 2. Detected Schema
                            schema_list = proc_info.get("schema_detected", [])
                            st.markdown("**🔎 DETECTED POSTGRESQL SCHEMA**")
                            if schema_list:
                                schema_df = pd.DataFrame(schema_list)[["original_name", "normalized_name", "detected_type", "null_count", "null_percentage", "sample_value"]]
                                schema_df.columns = ["Original Column", "Normalized Column", "PostgreSQL Type", "Null Count", "Null %", "Sample Value"]
                                st.dataframe(schema_df, use_container_width=True, hide_index=True)

                            # 3. Cleaning Report
                            clean_rep = proc_info.get("cleaning_report", {})
                            st.markdown("**🧹 CLEANING REPORT**")
                            m_c1, m_c2, m_c3, m_c4 = st.columns(4)
                            m_c1.metric("Rows Cleaned", f"{clean_rep.get('rows_after')} / {clean_rep.get('rows_before')}")
                            m_c2.metric("Duplicates Dropped", clean_rep.get("duplicate_rows_removed", 0))
                            m_c3.metric("Empty Rows Dropped", clean_rep.get("empty_rows_removed", 0))
                            m_c4.metric("Nulls Preserved", clean_rep.get("null_values_preserved", 0))

                            if clean_rep.get("operations_performed"):
                                with st.expander("📝 Cleaning Operations Log", expanded=False):
                                    for op in clean_rep["operations_performed"]:
                                        st.markdown(f"- {op}")

                            # 4. Explicit Confirmation & Import Section
                            st.markdown("""
                                <div style="background: rgba(34, 197, 94, 0.08); border: 1px solid rgba(34, 197, 94, 0.3); border-radius: 10px; padding: 14px; margin-top: 14px;">
                                    <div style="font-size: 0.95rem; font-weight: 700; color: #4ade80; margin-bottom: 4px;">🚀 Ready for PostgreSQL Import</div>
                                    <div style="font-size: 0.8rem; color: #cbd5e1;">Review the destination table name below and click to create table and bulk import.</div>
                                </div>
                            """, unsafe_allow_html=True)

                            imp_c1, imp_c2, imp_c3 = st.columns([2, 1.2, 1])
                            with imp_c1:
                                target_tbl = st.text_input(
                                    "Destination PostgreSQL Table Name",
                                    value=proc_info.get("suggested_table_name", "custom_table"),
                                    key=f"tbl_name_{ds_id}"
                                )
                            with imp_c2:
                                st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                                if st.button("🚀 Create Table & Import", key=f"do_import_{ds_id}", type="primary", use_container_width=True):
                                    with st.spinner("Creating PostgreSQL table and inserting records..."):
                                        imp_resp = call_backend_api(
                                            "POST",
                                            f"/api/v1/admin/datasets/{ds_id}/import",
                                            json={"custom_table_name": target_tbl}
                                        )
                                        if imp_resp.status_code == 200:
                                            st.session_state.processed_datasets.pop(ds_id, None)
                                            st.session_state.selected_dataset_id = ds_id
                                            st.cache_data.clear()
                                            st.success(f"🎉 Table '{target_tbl}' created and {prev.get('total_rows')} rows imported successfully! Set as Active Dataset.")
                                            time.sleep(1.0)
                                            st.rerun()
                                        else:
                                            st.error(f"Import Error: {imp_resp.text}")
                            with imp_c3:
                                st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                                if st.button("❌ Close Preview", key=f"close_prev_{ds_id}", use_container_width=True):
                                    st.session_state.processed_datasets.pop(ds_id, None)
                                    st.rerun()
        else:
            st.error("Unable to load datasets from backend API.")
