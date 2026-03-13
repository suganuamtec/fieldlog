#!/usr/bin/env python3
"""
FieldLog — Tunnel Survey
Serves tunnel_survey.html filling the full browser viewport.
No login required.
"""

import sys
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

sys.path.insert(0, str(Path(__file__).parent.parent))

st.set_page_config(
    page_title="Tunnel Survey — FieldLog",
    page_icon="🗺",
    layout="wide",
)

# ── Strip every pixel of Streamlit chrome ──────────────────────────────────────
st.markdown("""
<style>
/* Hide all Streamlit shell elements */
#MainMenu, footer,
header[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stExpandSidebarButton"],
[data-testid="stSidebarCollapseButton"],
section[data-testid="stSidebar"] { display: none !important; }

/* Zero out all padding/margin on the main container */
.main .block-container,
section[data-testid="stMain"] > div,
[data-testid="stAppViewContainer"] > section {
    padding: 0 !important;
    margin: 0 !important;
    max-width: 100% !important;
    width: 100% !important;
}
html, body, .stApp { margin: 0; padding: 0; overflow: hidden; }
iframe { display: block; border: none; width: 100% !important; }
</style>
""", unsafe_allow_html=True)

# ── Read the HTML and inject a viewport-fill script ────────────────────────────
_html = (Path(__file__).parent.parent / "tunnel_survey.html").read_text(encoding="utf-8")

# Inject a script that reads the parent window's dimensions and resizes the
# iframe + the app div to fill the exact browser viewport.
_fill_script = """
<script>
(function () {
  function fill() {
    try {
      var h = (window.parent || window).innerHeight;
      var w = (window.parent || window).innerWidth;
      // Resize the iframe element itself
      if (window.frameElement) {
        window.frameElement.style.height = h + 'px';
        window.frameElement.style.width  = w + 'px';
      }
      // Resize the app grid
      var app = document.getElementById('app');
      if (app) {
        app.style.height = h + 'px';
        app.style.width  = '100%';
      }
      document.documentElement.style.height = h + 'px';
      document.body.style.height            = h + 'px';
      document.body.style.overflow          = 'hidden';
    } catch(e) {}
  }
  fill();
  setTimeout(fill, 50);
  setTimeout(fill, 200);
  window.addEventListener('resize', fill);
  try { window.parent.addEventListener('resize', fill); } catch(e) {}
})();
</script>
"""

_html = _html.replace("</body>", _fill_script + "</body>")

# Start tall enough so the fill script can take over immediately
components.html(_html, height=1100, scrolling=False)
