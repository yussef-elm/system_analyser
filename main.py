import streamlit as st
from datetime import datetime, timedelta
from config import CENTERS, CUSTOM_CSS, ACCESS_TOKEN

# Import only required page modules
from pages import (
    cpr_analysis,
    lp_conversion_analysis,
    rates_analysis
)

# Set page config
st.set_page_config(page_title="System Data Analyser", page_icon="🧠", layout="wide")

# Apply CSS
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Header
st.title("🧠 System Data Analyser")
# ...existing code...

# Hide Streamlit menu, footer, header, and sidebar navigation
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    section[data-testid="stSidebarNav"] {display: none;}
    </style>
""", unsafe_allow_html=True)

# ...existing code...
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
    # Pass the selected view_type to the Rates Analysis page
    rates_analysis.show(selected_centers, start_date, end_date, access_token, view_type=view_type)

st.markdown("---")
st.markdown("© Sbitis Acquisition 2025")