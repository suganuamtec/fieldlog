"""
Shared helpers for FieldLog pages.
Provides CSS theming, login gate, and common sidebar controls.
"""

import streamlit as st

# ── CSS ────────────────────────────────────────────────────────────────────────

_BASE_CSS = """
<style>
/* ── Hide Streamlit chrome ── */
#MainMenu { display: none !important; }
footer { display: none !important; }
header[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stToolbar"] { visibility: hidden; }
[data-testid="stExpandSidebarButton"],
[data-testid="stSidebarCollapseButton"],
[data-testid="stExpandSidebarButton"] *,
[data-testid="stSidebarCollapseButton"] * {
    visibility: visible !important;
    pointer-events: auto !important;
}
/* ── Title accent bar ── */
.main h1 {
    padding-bottom: 0.5rem;
    border-bottom: 3px solid #2563eb;
    margin-bottom: 1rem;
}
/* ── Form border ── */
[data-testid="stForm"] {
    border: 1px solid rgba(128,128,128,0.25);
    border-radius: 12px;
    padding: 1.25rem 1.5rem !important;
}
/* ── Rounded buttons ── */
button[kind="primary"],
button[kind="primaryFormSubmit"],
button[kind="secondary"],
button[kind="tertiary"] {
    border-radius: 8px !important;
}
/* ── Alerts ── */
[data-testid="stAlert"] { border-radius: 8px !important; }
</style>
"""

_DARK_CSS = """
<style>
/* === FIELDLOG DARK THEME === */
html, body, .stApp { background-color: #18181b !important; color: #f4f4f5 !important; }
.main .block-container { background-color: #18181b !important; }
section[data-testid="stSidebar"] { background-color: #111113 !important; }
[data-testid="stSidebarContent"],
[data-testid="stSidebarUserContent"] { background-color: #111113 !important; }

h1, h2, h3, h4, h5, h6 { color: #f4f4f5 !important; }
p, label, small { color: #f4f4f5; }
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li { color: #f4f4f5 !important; }
.stCaption, [data-testid="stCaptionContainer"] * { color: #a1a1aa !important; }

.stTextInput input, .stTextArea textarea,
[data-testid="stNumberInput"] input,
[data-testid="stDateInput"] input,
[data-testid="stTimeInput"] input {
    background-color: #27272a !important;
    color: #f4f4f5 !important;
    border-color: #3f3f46 !important;
}
[data-baseweb="select"] > div:first-child {
    background-color: #27272a !important;
    border-color: #3f3f46 !important;
    color: #f4f4f5 !important;
}
[data-baseweb="popover"] > div,
[data-baseweb="menu"] { background-color: #27272a !important; border-color: #3f3f46 !important; }
[role="option"] { background-color: #27272a !important; color: #f4f4f5 !important; }
[role="option"]:hover,
[aria-selected="true"][role="option"] { background-color: #3f3f46 !important; }

[data-testid="stForm"] { background-color: #1e1e22 !important; border-color: #3f3f46 !important; }
hr, [data-testid="stDivider"] > div { background-color: #3f3f46 !important; }

[data-baseweb="tab-list"] { background-color: #27272a !important; }
[data-baseweb="tab"] { color: #a1a1aa !important; }
[aria-selected="true"][data-baseweb="tab"] { color: #f4f4f5 !important; }

[data-testid="stAlert"] { background-color: #1e1e22 !important; }

[data-testid="stDataFrame"] *,
.stDataFrame { background-color: #27272a !important; color: #f4f4f5 !important; }
[data-testid="stDataFrame"] th { background-color: #3f3f46 !important; }

button[kind="secondary"],
[data-testid="baseButton-secondary"],
[data-testid="stDownloadButton"] > button {
    background-color: #27272a !important;
    border-color: #3f3f46 !important;
    color: #f4f4f5 !important;
}
button[kind="secondary"]:hover,
[data-testid="baseButton-secondary"]:hover,
[data-testid="stDownloadButton"] > button:hover {
    background-color: #3f3f46 !important;
}

.stCheckbox label, .stRadio label,
[data-testid="stCheckbox"] span,
[data-testid="stRadio"] span { color: #f4f4f5 !important; }

[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p { color: #f4f4f5 !important; }

[data-testid="stInfo"] { background-color: #1e3a5f !important; }
[data-testid="stSuccess"] { background-color: #14532d !important; }
[data-testid="stWarning"] { background-color: #451a03 !important; }
[data-testid="stError"] { background-color: #450a0a !important; }

a { color: #60a5fa !important; }

::-webkit-scrollbar-track { background: #18181b; }
::-webkit-scrollbar-thumb { background: #3f3f46; border-radius: 4px; }

[data-testid="stExpandSidebarButton"],
[data-testid="stSidebarCollapseButton"],
[data-testid="stExpandSidebarButton"] *,
[data-testid="stSidebarCollapseButton"] * {
    visibility: visible !important;
    pointer-events: auto !important;
}
[data-testid="stExpandSidebarButton"] button,
[data-testid="stSidebarCollapseButton"] button {
    background-color: #3f3f46 !important;
    border: 1px solid #71717a !important;
    color: #f4f4f5 !important;
}
[data-testid="stExpandSidebarButton"] svg,
[data-testid="stSidebarCollapseButton"] svg { fill: #f4f4f5 !important; }
</style>
"""


def apply_theme():
    """Inject base CSS + dark theme if selected."""
    st.markdown(_BASE_CSS, unsafe_allow_html=True)
    if st.session_state.get("webapp_theme", "light") == "dark":
        st.markdown(_DARK_CSS, unsafe_allow_html=True)


def login_gate():
    """Redirect to login form if the user is not authenticated. Call at the top of each page."""
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if not st.session_state.logged_in:
        st.title("📋 FieldLog")
        _, _lc, _ = st.columns([1, 1, 1])
        with _lc:
            st.subheader("Sign In")
            _lu = st.text_input("Username", key="login_username")
            _lp = st.text_input("Password", type="password", key="login_password")
            if st.button("Login", use_container_width=True, type="primary"):
                if _lu == "uamtec" and _lp == "summer11":
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("Invalid username or password.")
        st.stop()


def sidebar_nav():
    """Render common sidebar controls: theme toggle and logout."""
    with st.sidebar:
        _is_dark = st.session_state.get("webapp_theme", "light") == "dark"
        if st.button(
            "☀  Light Mode" if _is_dark else "🌙  Dark Mode",
            use_container_width=True,
            key="_common_theme_btn",
        ):
            st.session_state.webapp_theme = "light" if _is_dark else "dark"
            st.rerun()
        if st.button("🔓 Logout", use_container_width=True, key="_common_logout_btn"):
            st.session_state.logged_in = False
            st.rerun()
        st.markdown("---")
