import streamlit as st
from datetime import datetime, timedelta
import base64, hmac, hashlib, json
from config import CENTERS, CUSTOM_CSS, ACCESS_TOKEN

# Import only required page modules
from pages import (
    cpr_analysis,
    lp_conversion_analysis,
    rates_analysis
)

# ========== Cookie Utilities ==========
COOKIE_NAME = "sda_auth"
COOKIE_MAX_AGE_DAYS = 30

def _sign(payload: str, secret: str) -> str:
    return hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()

def _encode(obj: dict) -> str:
    raw = json.dumps(obj, separators=(",", ":"), ensure_ascii=False)
    return base64.urlsafe_b64encode(raw.encode()).decode()

def _decode(b64: str) -> dict:
    try:
        raw = base64.urlsafe_b64decode(b64.encode()).decode()
        return json.loads(raw)
    except Exception:
        return {}

def set_cookie(name: str, value: str, days: int = COOKIE_MAX_AGE_DAYS):
    max_age = days * 24 * 60 * 60
    js = f"""
    <script>
      (function() {{
        var name = "{name}";
        var value = "{value}";
        var maxAge = {max_age};
        document.cookie = name + "=" + value + "; Max-Age=" + maxAge + "; path=/; SameSite=Lax";
      }})();
    </script>
    """
    st.markdown(js, unsafe_allow_html=True)

def get_cookie(name: str) -> str | None:
    key = f"_cookie_{name}"
    js = f"""
    <script>
      (function() {{
        const name = "{name}=";
        const decodedCookie = decodeURIComponent(document.cookie);
        const ca = decodedCookie.split(';');
        let v = "";
        for (let i = 0; i < ca.length; i++) {{
          let c = ca[i];
          while (c.charAt(0) === ' ') c = c.substring(1);
          if (c.indexOf(name) === 0) v = c.substring(name.length, c.length);
        }}
        const elId = "{key}";
        let el = window.parent.document.getElementById(elId);
        if (!el) {{
          el = window.parent.document.createElement("input");
          el.type = "hidden";
          el.id = elId;
          window.parent.document.body.appendChild(el);
        }}
        el.value = v;
      }})();
    </script>
    """
    st.markdown(js, unsafe_allow_html=True)
    return st.session_state.get(key)

def sync_cookie_to_session(name: str):
    ph = st.empty()
    if name not in st.session_state:
        st.session_state[name] = None

    js = f"""
    <script>
      (function() {{
        const hiddenId = "_cookie_{name}";
        function apply() {{
          const hidden = window.parent.document.getElementById(hiddenId);
          if (!hidden) return;
          const v = hidden.value || "";
          const iframe = window.frameElement;
          if (!iframe) return;
          const txts = iframe.contentDocument.querySelectorAll('input[type="text"][data-cookie-probe="{name}"]');
          if (txts.length) {{
            const inp = txts[0];
            if (inp.value !== v) {{
              inp.value = v;
              inp.dispatchEvent(new Event('input', {{ bubbles: true }}));
            }}
          }}
        }}
        setTimeout(apply, 50);
      }})();
    </script>
    """
    with ph.container():
        _ = st.text_input("", key=f"_cookie_probe_{name}", label_visibility="collapsed", help=None)
        st.markdown(f"""<input type="text" data-cookie-probe="{name}" style="display:none" />""", unsafe_allow_html=True)
        st.markdown(js, unsafe_allow_html=True)
    val = st.session_state.get(f"_cookie_probe_{name}")
    if val:
        st.session_state[f"_cookie_{name}"] = val

def save_auth_cookie(username: str, expires_at: datetime, secret: str):
    payload = {
        "u": username,
        "exp": int(expires_at.timestamp())
    }
    b64 = _encode(payload)
    sig = _sign(b64, secret)
    token = f"{b64}.{sig}"
    set_cookie(COOKIE_NAME, token, days=COOKIE_MAX_AGE_DAYS)

def load_auth_cookie(secret: str) -> str | None:
    sync_cookie_to_session(COOKIE_NAME)
    token = get_cookie(COOKIE_NAME)
    if not token:
        return None
    parts = token.split(".")
    if len(parts) != 2:
        return None
    b64, sig = parts
    if _sign(b64, secret) != sig:
        return None
    data = _decode(b64)
    if not data or "u" not in data or "exp" not in data:
        return None
    if datetime.utcnow().timestamp() > data["exp"]:
        return None
    return data["u"]

def clear_auth_cookie():
    js = f"""
    <script>
      document.cookie = "{COOKIE_NAME}=; Max-Age=0; path=/; SameSite=Lax";
    </script>
    """
    st.markdown(js, unsafe_allow_html=True)

# ========== Auth ==========
def check_login():
    """Check if user is logged in; support 30-day remember-me cookie."""
    try:
        username = st.secrets["auth"]["username"]
        password = st.secrets["auth"]["password"]
        cookie_secret = st.secrets["auth"]["cookie_secret"]
    except KeyError:
        st.error("Authentication is not configured. Please set auth.username, auth.password, and auth.cookie_secret in st.secrets.")
        st.stop()

    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
        st.session_state["username"] = None

    # Try cookie if not logged in
    if not st.session_state["logged_in"]:
        remembered_user = load_auth_cookie(cookie_secret)
        if remembered_user:
            st.session_state["logged_in"] = True
            st.session_state["username"] = remembered_user

    if not st.session_state["logged_in"]:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("### 🔐 Login Required")
            st.markdown("Please enter your credentials to access the dashboard.")

            with st.form("login_form"):
                user = st.text_input("Username", placeholder="Enter your username")
                pwd = st.text_input("Password", type="password", placeholder="Enter your password")
                remember = st.checkbox("Remember this device for 30 days", value=True)
                login_button = st.form_submit_button("Login", use_container_width=True)

                if login_button:
                    if user == username and pwd == password:
                        st.session_state["logged_in"] = True
                        st.session_state["username"] = user
                        st.success("✅ Logged in successfully!")
                        if remember:
                            expires_at = datetime.utcnow() + timedelta(days=COOKIE_MAX_AGE_DAYS)
                            save_auth_cookie(user, expires_at, cookie_secret)
                        st.rerun()
                    else:
                        st.error("❌ Invalid username or password")
        st.stop()

def logout():
    """Logout function; clears session and cookie."""
    if st.button("🚪 Logout", key="logout_btn"):
        st.session_state["logged_in"] = False
        st.session_state["username"] = None
        clear_auth_cookie()
        st.rerun()

# ---------- Auth first ----------
check_login()

# ---------- Page config (after we know we're logged in) ----------
st.set_page_config(page_title="System Data Analyser", page_icon="🧠", layout="wide")

# Apply CSS
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Hide Streamlit menu, footer, header, sidebar navigation, and sidebar header
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    section[data-testid="stSidebarNav"] {display: none !important;}
    [data-testid="stSidebarHeader"] {display: none !important;}
    </style>
""", unsafe_allow_html=True)

# Header with logout button
col1, col2 = st.columns([4, 1])
with col1:
    st.title("🧠 System Data Analyser")
with col2:
    logout()

# --- Sidebar Filters ---
with st.sidebar:
    st.markdown('<div class="sidebar-filters">', unsafe_allow_html=True)
    st.markdown("### 🔎 Filter Data")

    # Navigation
    page = st.selectbox(
        "📄 Select Page",
        ["CPR Analysis", "LP Conversion Analysis", "Rates Analysis"],
        key="page_select"
    )

    st.markdown("#### 📅 Date Range")
    date_col1, date_col2 = st.columns(2)
    with date_col1:
        start_date = st.date_input(
            "Start",
            value=datetime.now().date() - timedelta(days=30),
            max_value=datetime.now().date(),
            key="start_date"
        )
    with date_col2:
        end_date = st.date_input(
            "End",
            value=datetime.now().date(),
            min_value=start_date,
            key="end_date"
        )

    # View filter for splitting API calls (used by Rates Analysis)
    VIEW_TYPES = ["Daily", "3 Days", "Weekly", "Two Weeks", "Monthly"]
    view_type = st.selectbox(
        "🧩 View",
        options=VIEW_TYPES,
        index=VIEW_TYPES.index("Weekly"),
        help="Split the date range into daily/3-day/weekly/two-week/monthly periods (Rates Analysis only)",
        key="view_type_select"
    )

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("#### 🏙️ Cities & Centers")
    cities = sorted(set(center['city'] for center in CENTERS))
    selected_cities = st.multiselect(
        "Select Cities",
        options=cities,
        default=cities,
        help="Filter centers by city",
        key="cities_select"
    )

    center_names = [center['centerName'] for center in CENTERS if center['city'] in selected_cities]
    selected_centers = st.multiselect(
        "Select Centers",
        options=center_names,
        default=center_names,
        help="Choose which centers to analyze",
        key="centers_select"
    )

    st.markdown(
        f"<div style='margin-top:10px; font-size:12px; color:rgba(255,255,255,0.9);'>"
        f"<b>Selected:</b> {len(selected_centers)} centers in {len(selected_cities)} cities"
        f"</div>",
        unsafe_allow_html=True
    )

    st.markdown('</div>', unsafe_allow_html=True)

access_token = ACCESS_TOKEN

if not selected_centers:
    st.warning("Please select at least one center to analyze.")
    st.stop()

# Route to pages
if page == "CPR Analysis":
    cpr_analysis.show(selected_centers, start_date, end_date, access_token, view_type=view_type)
elif page == "LP Conversion Analysis":
    lp_conversion_analysis.show(selected_centers, start_date, end_date, access_token, view_type=view_type)
elif page == "Rates Analysis":
    rates_analysis.show(selected_centers, start_date, end_date, access_token, view_type=view_type)

st.markdown("---")
st.markdown("© Sbitis Acquisition 2025")