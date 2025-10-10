# pages/lp_conversion_analysis.py
# LP Conversion Analysis page with bucketed views (Daily/3 Days/Weekly/Two Weeks/Monthly)
# For each bucket:
#   - per-center LP Conv (%) = leads / landing_page_views * 100
#   - combined (All Centers) = sum(leads) / sum(landing_page_views) * 100 (only centers with lp_views > 0)
# Hover shows bucket, date range, Leads, LP Views, and LP Conv %.
# Summary metrics (Total Leads, Avg LP Conv) displayed under each chart.
# + Best performing centers cards (Top 3)

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import List, Dict

import pandas as pd
import streamlit as st
import plotly.graph_objects as go

from api_client import fetch_meta_metrics_for_centers

PAGE_TITLE = "LP Conversion Analysis"
VIEW_TYPES = ["Daily", "3 Days", "Weekly", "Two Weeks", "Monthly"]


def _today():
    return date.today()


def _ensure_datetime(d: date | datetime) -> datetime:
    if isinstance(d, datetime):
        return d
    return datetime(d.year, d.month, d.day)


def _safe_float(v, default=0.0) -> float:
    try:
        return float(v)
    except Exception:
        return default


def _safe_int(v, default=0) -> int:
    try:
        return int(v)
    except Exception:
        return default


def get_buckets_labeled(start_date: date, end_date: date, view_type: str) -> List[Dict]:
    """
    Produce labeled buckets anchored to the selected start_date (except Monthly which follows calendar month ends).
    Returns list of dicts: {'bucket_idx', 'label', 'start', 'end'}
    """
    buckets = []
    idx = 1
    cur = start_date

    def add_bucket(s: date, e: date, label: str):
        buckets.append({
            'bucket_idx': idx,
            'label': label,
            'start': _ensure_datetime(s),
            'end': _ensure_datetime(e),
        })

    if view_type == 'Daily':
        while cur <= end_date:
            s, e = cur, cur
            add_bucket(s, e, f'Day {idx}')
            idx += 1
            cur = cur + timedelta(days=1)

    elif view_type == '3 Days':
        while cur <= end_date:
            s = cur
            e = min(cur + timedelta(days=2), end_date)  # 3-day window inclusive
            add_bucket(s, e, f'3-Day {idx}')
            idx += 1
            cur = e + timedelta(days=1)

    elif view_type == 'Weekly':
        while cur <= end_date:
            s = cur
            e = min(cur + timedelta(days=6), end_date)
            add_bucket(s, e, f'Week {idx}')
            idx += 1
            cur = e + timedelta(days=1)

    elif view_type == 'Two Weeks':
        while cur <= end_date:
            s = cur
            e = min(cur + timedelta(days=13), end_date)
            add_bucket(s, e, f'2W {idx}')
            idx += 1
            cur = e + timedelta(days=1)

    elif view_type == 'Monthly':
        # Month windows intersecting the range (calendar months)
        cur = start_date
        while cur <= end_date:
            next_month = (cur.replace(day=28) + timedelta(days=4))
            month_end = next_month - timedelta(days=next_month.day)
            s = cur
            e = min(month_end, end_date)
            label = _ensure_datetime(s).strftime("%b %Y")
            add_bucket(s, e, label)
            idx += 1
            cur = month_end + timedelta(days=1)

    return buckets


@st.cache_data(ttl=300, show_spinner=False)
def fetch_and_process_lpconv_data(
    selected_centers_config: List[Dict],
    start_date: date,
    end_date: date,
    access_token: str,
    view_type: str
):
    """
    For each bucket, fetch Meta metrics for each center and compute LP Conversion (%).
    Returns:
    - df_points: per-center per-bucket rows
    - df_combined: per-bucket combined weighted LP Conv (sum(leads)/sum(lp_views)*100) only for centers with lp_views > 0
    - buckets: list of bucket dicts used
    """
    buckets = get_buckets_labeled(start_date, end_date, view_type)

    # Valid centers with businessId
    center_names = []
    for c in selected_centers_config:
        cname = c.get('centerName') or c.get('name')
        business_id = c.get('businessId') or c.get('business_id') or c.get('businessID')
        if cname and business_id and str(business_id).lower() != 'none':
            center_names.append(cname)

    per_center_rows = []
    for b in buckets:
        s_str = b['start'].strftime('%Y-%m-%d')
        e_str = b['end'].strftime('%Y-%m-%d')

        if center_names:
            results = fetch_meta_metrics_for_centers(s_str, e_str, center_names, access_token)
        else:
            results = []

        res_map = {r.get('centerName'): r for r in results} if isinstance(results, list) else {}

        for c in selected_centers_config:
            center_name = c.get('centerName') or c.get('name')
            business_id = c.get('businessId') or c.get('business_id') or c.get('businessID')
            if not center_name or not business_id or str(business_id).lower() == 'none':
                continue

            r = res_map.get(center_name)
            if not r or 'metrics' not in r or (isinstance(r['metrics'], dict) and 'error' in r['metrics']):
                leads = 0
                lp_rate = 0.0
                lp_views = 0
            else:
                leads = _safe_int(r['metrics'].get('leads', 0))
                lp_rate = _safe_float(r['metrics'].get('lp_conversion_rate', 0.0))
                # Approximate lp_views from leads and lp_rate when possible
                if lp_rate > 0:
                    lp_views = int(round(leads * 100.0 / lp_rate))
                else:
                    lp_views = 0

            per_center_rows.append({
                'centerName': center_name,
                'bucket_idx': b['bucket_idx'],
                'bucket_label': b['label'],
                'bucket_start': b['start'],
                'bucket_end': b['end'],
                'leads': leads,
                'lp_views': lp_views,
                'lp_conversion': lp_rate  # percent
            })

    df = pd.DataFrame(per_center_rows)
    if df.empty:
        return df, pd.DataFrame(), buckets

    # Combined weighted LP Conv per bucket: sum(leads)/sum(lp_views) * 100
    # Only include centers with lp_views > 0
    df_with_views = df[df['lp_views'] > 0].copy()
    
    agg = df_with_views.groupby(['bucket_idx', 'bucket_label', 'bucket_start', 'bucket_end'], as_index=False).agg(
        leads_sum=('leads', 'sum'),
        lp_views_sum=('lp_views', 'sum')
    )
    agg['weighted_lpconv'] = agg.apply(
        lambda r: (r.leads_sum / r.lp_views_sum * 100.0) if r.lp_views_sum > 0 else 0.0, axis=1
    )

    df = df.sort_values(['centerName', 'bucket_idx']).reset_index(drop=True)
    agg = agg.sort_values(['bucket_idx']).reset_index(drop=True)

    return df, agg, buckets


def _rank_best_centers(df_points: pd.DataFrame):
    """
    Calculate average LP conversion per center and return top performers.
    """
    if df_points is None or df_points.empty:
        return pd.DataFrame(), pd.DataFrame()

    stats = df_points.groupby('centerName', as_index=False).agg(
        avg_lpconv=('lp_conversion', 'mean'),
        total_leads=('leads', 'sum'),
        total_views=('lp_views', 'sum')
    )
    stats['avg_lpconv'] = stats['avg_lpconv'].fillna(0.0)
    stats = stats.sort_values(['avg_lpconv', 'total_leads'], ascending=[False, False]).reset_index(drop=True)
    top3 = stats.head(3).copy()
    return top3, stats


def create_combined_chart(df_combined: pd.DataFrame, view_type: str) -> go.Figure:
    fig = go.Figure()
    title = f"All Centers - {view_type} LP Conversion (%)"

    if df_combined is None or df_combined.empty:
        fig.update_layout(height=420, title=title, xaxis_title="Bucket", yaxis_title="LP Conv (%)")
        return fig

    fig.add_trace(go.Scatter(
        x=df_combined['bucket_label'],
        y=df_combined['weighted_lpconv'],
        mode='lines+markers',
        name='Avg LP Conv (All Centers)',
        line=dict(color='#005bbb', width=3),
        marker=dict(size=8),
        hovertemplate=(
            '<b>%{x}</b><br>'
            '<b>Range:</b> %{customdata[0]} → %{customdata[1]}<br>'
            '<b>LP Conv:</b> %{y:.2f}%<br>'
            '<b>Leads (sum):</b> %{customdata[2]:,}<br>'
            '<b>LP Views (sum est.):</b> %{customdata[3]:,}<extra></extra>'
        ),
        customdata=list(zip(
            pd.to_datetime(df_combined['bucket_start']).dt.strftime('%Y-%m-%d'),
            pd.to_datetime(df_combined['bucket_end']).dt.strftime('%Y-%m-%d'),
            df_combined['leads_sum'],
            df_combined['lp_views_sum']
        ))
    ))

    avg_line = df_combined['weighted_lpconv'].mean()
    fig.add_hline(y=avg_line, line_dash='dot', line_color='#dc3545',
                  annotation_text=f'Overall Avg: {avg_line:.2f}%',
                  annotation_position='top right')

    fig.update_layout(
        title=title,
        xaxis_title="Bucket",
        yaxis_title="LP Conv (%)",
        height=430,
        hovermode='x',
        plot_bgcolor='#f8f9fa',
        paper_bgcolor='white',
        margin=dict(t=70, b=30, l=20, r=20),
        showlegend=True
    )
    return fig


def create_lpconv_chart(center_name: str, df_center: pd.DataFrame, view_type: str, show_rolling_avg: bool = False) -> go.Figure:
    fig = go.Figure()
    title = f"{center_name} - {view_type} LP Conversion (%)"

    if df_center is None or df_center.empty:
        fig.update_layout(height=360, title=title, xaxis_title="Bucket", yaxis_title="LP Conv (%)")
        return fig

    df_center = df_center.sort_values('bucket_idx')

    fig.add_trace(go.Scatter(
        x=df_center['bucket_label'],
        y=df_center['lp_conversion'],
        mode='lines+markers',
        name='LP Conv (%)',
        line=dict(color='#28a745', width=3),
        marker=dict(size=8),
        hovertemplate=(
            '<b>%{x}</b><br>'
            '<b>Range:</b> %{customdata[0]} → %{customdata[1]}<br>'
            '<b>LP Conv:</b> %{y:.2f}%<br>'
            '<b>Leads:</b> %{customdata[2]:,}<br>'
            '<b>LP Views (est.):</b> %{customdata[3]:,}<extra></extra>'
        ),
        customdata=list(zip(
            pd.to_datetime(df_center['bucket_start']).dt.strftime('%Y-%m-%d'),
            pd.to_datetime(df_center['bucket_end']).dt.strftime('%Y-%m-%d'),
            df_center['leads'],
            df_center['lp_views']
        ))
    ))

    # Optional rolling avg for Daily only
    if show_rolling_avg and view_type == 'Daily':
        rolling = df_center['lp_conversion'].rolling(window=7, min_periods=1).mean()
        fig.add_trace(go.Scatter(
            x=df_center['bucket_label'],
            y=rolling,
            mode='lines',
            name='7-Day Avg',
            line=dict(color='#ffc107', width=2, dash='dash')
        ))

    avg_val = df_center['lp_conversion'].mean()
    fig.add_hline(y=avg_val, line_dash='dot', line_color='#dc3545',
                  annotation_text=f'Avg: {avg_val:.2f}%',
                  annotation_position='top right')

    fig.update_layout(
        title=title,
        xaxis_title="Bucket",
        yaxis_title="LP Conv (%)",
        height=400,
        hovermode='x',
        plot_bgcolor='#f8f9fa',
        paper_bgcolor='white',
        margin=dict(t=70, b=30, l=20, r=20),
        showlegend=True
    )
    return fig


def show(selected_centers, start_date, end_date, access_token, view_type: str = "Weekly"):
    """
    Main entry point called from main.py routing.
    - view_type now comes from the sidebar (main router) and is not selected on this page.
    """
    st.title(PAGE_TITLE)

    from config import CENTERS
    centers_config = [c for c in CENTERS if c['centerName'] in selected_centers]

    # Sidebar controls provide start_date, end_date, and view_type.
    filter_start = start_date
    filter_end = end_date

    # Display-only toggle (kept on page)
    show_rolling = st.checkbox("7-day rolling (Daily only)", value=False, key="lpconv_rolling_avg")

    if filter_start > filter_end:
        st.warning("Start date must be before or equal to end date.")
        return

    buckets_preview = get_buckets_labeled(filter_start, filter_end, view_type)
    est_calls = len(buckets_preview) * len(centers_config)
    if est_calls > 160:
        st.caption(f"Note: This request may trigger ~{est_calls} center-bucket calculations. Caching is enabled.")

    with st.spinner("Fetching and aggregating LP Conversion data..."):
        df_points, df_combined, buckets = fetch_and_process_lpconv_data(
            centers_config, filter_start, filter_end, access_token, view_type
        )

    # Rank best performing centers (Top 3 by avg LP Conv)
    top3, all_stats = _rank_best_centers(df_points)

# ...existing code...

    st.subheader("🏆 Top LP Conversion Performers")
    if top3.empty:
        st.info("No center performance available for the selected range/view.")
    else:
        # Responsive cards with margin-bottom
        cols = st.columns(3) if len(top3) >= 3 else st.columns(len(top3))
        gradients = [
            "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
            "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
            "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
        ]
        medals = ["🥇", "🥈", "🥉"]

        card_css = """
        <style>
        .lpconv-card {
            background: VAR_BG;
            padding: 18px;
            border-radius: 12px;
            color: white;
            box-shadow: 0 6px 14px rgba(0,0,0,0.12);
            margin-bottom: 18px;
            min-height: 140px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        @media (max-width: 900px) {
            .lpconv-card { min-height: 120px; font-size: 15px; }
        }
        </style>
        """
        st.markdown(card_css, unsafe_allow_html=True)

        for i, (_, row) in enumerate(top3.iterrows()):
            bg = gradients[i % len(gradients)]
            medal = medals[i] if i < len(medals) else "🏅"
            with cols[i]:
                st.markdown(
                    f"""
                    <div class="lpconv-card" style="background: {bg};">
                        <div style="font-size: 22px; margin-bottom: 6px;">{medal} {row['centerName']}</div>
                        <div style="font-size: 28px; font-weight: 700; margin-bottom: 8px;">
                            {row['avg_lpconv']:.2f}% LP Conv
                        </div>
                        <div style="opacity: 0.95;">
                            Leads: {int(row['total_leads']):,} • LP Views (est.): {int(row['total_views']):,}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

    # Add margin below the cards and above the expander
    st.markdown('<div style="margin-bottom: 8px;"></div>', unsafe_allow_html=True)

    # Optional: full stats table for transparency
    with st.expander("All centers ranking (Avg LP Conv)", expanded=False):
        if not all_stats.empty:
            st.dataframe(
                all_stats.rename(columns={
                    'centerName': 'Center',
                    'avg_lpconv': 'Avg LP Conv (%)',
                    'total_leads': 'Leads (sum)',
                    'total_views': 'LP Views (sum est.)'
                }),
                use_container_width=True
            )

# ...existing code...

    st.markdown("")

    st.subheader("Overall Performance")
    st.plotly_chart(
        create_combined_chart(df_combined, view_type), 
        use_container_width=True,
        config={"displayModeBar": False}
    )
    
    # Summary metrics for combined chart
    if not df_combined.empty:
        overall_avg_lpconv = df_combined['weighted_lpconv'].mean()
        overall_total_leads = df_combined['leads_sum'].sum()
        st.markdown(f"**Summary (All Centers):** Total Leads: {int(overall_total_leads):,} | Avg LP Conversion: {overall_avg_lpconv:.2f}%")

    st.markdown("")

    if df_points is None or df_points.empty:
        st.info("No data available for the selected range/view.")
        return

    center_list = sorted(df_points['centerName'].unique())
    st.subheader("By Center")

    cols = st.columns(2)
    for i, center in enumerate(center_list):
        df_c = df_points[df_points['centerName'] == center].copy()
        with cols[i % 2]:
            st.plotly_chart(
                create_lpconv_chart(center, df_c, view_type, show_rolling_avg=show_rolling),
                use_container_width=True,
                config={"displayModeBar": False}
            )
            # Summary metrics for this center
            if not df_c.empty:
                center_total_leads = df_c['leads'].sum()
                center_avg_lp = df_c['lp_conversion'].mean()
                st.markdown(f"**{center} Summary:** Leads: {int(center_total_leads):,} | Avg LP Conversion: {center_avg_lp:.2f}%")