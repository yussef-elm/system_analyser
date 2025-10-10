# pages/cpr_analysis.py
# CPR Analysis page with bucketed views:
# - Daily: Day 1, Day 2, ...
# - 3 Days: 3-Day 1, 3-Day 2, ... (3-day buckets anchored to selected start date)
# - Weekly: Week 1, Week 2, ... (7-day buckets anchored to selected start date)
# - Two Weeks: 2W 1, 2W 2, ... (14-day buckets anchored to selected start date)
# - Monthly: labeled as Month-Year (e.g., "Jan 2025") for calendar months intersecting the date range
#
# For each bucket the CPR point = sum(spend)/sum(leads) within that bucket.
# X-axis shows categorical bucket labels (not dates).
# Hover shows bucket label, date range, CPR, Spend, Leads.
# A big combined chart at the top shows weighted average CPR per bucket across all selected centers.
# Combined average excludes centers with zero leads in that bucket.
# Summary metrics (Avg CPR, Total Leads, Avg LP Conv) displayed under each chart.
# + Best performing centers cards (Top 3 - lowest CPR)

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import List, Dict

import pandas as pd
import streamlit as st
import plotly.graph_objects as go

from api_client import fetch_meta_metrics_for_centers

PAGE_TITLE = "CPR Analysis"
VIEW_TYPES = ["Daily", "3 Days", "Weekly", "Two Weeks", "Monthly"]


def _today():
    return date.today()


def _default_start():
    return _today() - timedelta(days=29)


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
            e = min(cur + timedelta(days=2), end_date)  # inclusive 3-day window
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
            # Label as Month-Year like "Jan 2025"
            label = _ensure_datetime(s).strftime("%b %Y")
            add_bucket(s, e, label)
            idx += 1
            cur = month_end + timedelta(days=1)

    return buckets


@st.cache_data(ttl=300, show_spinner=False)
def fetch_and_process_cpr_data(
    selected_centers_config: List[Dict],
    start_date: date,
    end_date: date,
    access_token: str,
    view_type: str
):
    """
    For each bucket, fetch Meta metrics for each center and compute CPR.
    Returns:
      - df_points: per-center per-bucket rows
      - df_combined: per-bucket combined weighted CPR (sum(spend)/sum(leads) across centers with leads > 0)
      - buckets: list of bucket dicts used
    """
    buckets = get_buckets_labeled(start_date, end_date, view_type)

    # Extract center names from config; skip ones without a valid business_id
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

        # Normalize results per center
        res_map = {r.get('centerName'): r for r in results} if isinstance(results, list) else {}

        for c in selected_centers_config:
            center_name = c.get('centerName') or c.get('name')
            business_id = c.get('businessId') or c.get('business_id') or c.get('businessID')
            if not center_name or not business_id or str(business_id).lower() == 'none':
                continue

            r = res_map.get(center_name)
            if not r or 'metrics' not in r or (isinstance(r['metrics'], dict) and 'error' in r['metrics']):
                spend = 0.0
                leads = 0
                lp_rate = 0.0
            else:
                spend = _safe_float(r['metrics'].get('spend', 0.0))
                leads = _safe_int(r['metrics'].get('leads', 0))
                lp_rate = _safe_float(r['metrics'].get('lp_conversion_rate', 0.0))

            cpr = (spend / leads) if leads > 0 else 0.0

            per_center_rows.append({
                'centerName': center_name,
                'bucket_idx': b['bucket_idx'],
                'bucket_label': b['label'],
                'bucket_start': b['start'],
                'bucket_end': b['end'],
                'spend': spend,
                'leads': leads,
                'cpr': cpr,
                'lp_conversion': lp_rate
            })

    df = pd.DataFrame(per_center_rows)
    if df.empty:
        return df, pd.DataFrame(), buckets

    # Combined weighted CPR per bucket across centers with leads > 0 only
    # Filter out rows with zero leads before aggregating
    df_with_leads = df[df['leads'] > 0].copy()
    
    agg = df_with_leads.groupby(['bucket_idx', 'bucket_label', 'bucket_start', 'bucket_end'], as_index=False).agg(
        spend_sum=('spend', 'sum'),
        leads_sum=('leads', 'sum')
    )
    agg['weighted_cpr'] = agg.apply(lambda r: (r.spend_sum / r.leads_sum) if r.leads_sum > 0 else 0.0, axis=1)

    # Ensure ordered by bucket index
    df = df.sort_values(['centerName', 'bucket_idx']).reset_index(drop=True)
    agg = agg.sort_values(['bucket_idx']).reset_index(drop=True)

    return df, agg, buckets


def _rank_best_centers(df_points: pd.DataFrame):
    """
    Calculate average CPR per center and return top performers (lowest CPR = best).
    Only include centers with leads > 0.
    """
    if df_points is None or df_points.empty:
        return pd.DataFrame(), pd.DataFrame()

    # Filter to only rows with leads
    df_with_leads = df_points[df_points['leads'] > 0].copy()
    
    if df_with_leads.empty:
        return pd.DataFrame(), pd.DataFrame()

    stats = df_with_leads.groupby('centerName', as_index=False).agg(
        avg_cpr=('cpr', 'mean'),
        total_spend=('spend', 'sum'),
        total_leads=('leads', 'sum'),
        avg_lpconv=('lp_conversion', 'mean')
    )
    stats['avg_cpr'] = stats['avg_cpr'].fillna(0.0)
    # Sort by lowest CPR (best) first, then by highest leads as tiebreaker
    stats = stats.sort_values(['avg_cpr', 'total_leads'], ascending=[True, False]).reset_index(drop=True)
    top3 = stats.head(3).copy()
    return top3, stats


def create_combined_chart(df_combined: pd.DataFrame, view_type: str) -> go.Figure:
    fig = go.Figure()
    title = f"All Centers - {view_type} Average CPR"

    if df_combined is None or df_combined.empty:
        fig.update_layout(height=420, title=title, xaxis_title="Bucket", yaxis_title="CPR (€)")
        return fig

    fig.add_trace(go.Scatter(
        x=df_combined['bucket_label'],
        y=df_combined['weighted_cpr'],
        mode='lines+markers',
        name='Avg CPR (All Centers)',
        line=dict(color='#005bbb', width=3),
        marker=dict(size=8),
        hovertemplate=(
            '<b>%{x}</b><br>'
            '<b>Range:</b> %{customdata[0]} → %{customdata[1]}<br>'
            '<b>CPR:</b> €%{y:.2f}<br>'
            '<b>Spend (sum):</b> €%{customdata[2]:,.2f}<br>'
            '<b>Leads (sum):</b> %{customdata[3]:,}<extra></extra>'
        ),
        customdata=list(zip(
            pd.to_datetime(df_combined['bucket_start']).dt.strftime('%Y-%m-%d'),
            pd.to_datetime(df_combined['bucket_end']).dt.strftime('%Y-%m-%d'),
            df_combined['spend_sum'],
            df_combined['leads_sum']
        ))
    ))

    avg_line = df_combined['weighted_cpr'].mean()
    fig.add_hline(y=avg_line, line_dash='dot', line_color='#dc3545',
                  annotation_text=f'Overall Avg: €{avg_line:.2f}',
                  annotation_position='top right')

    fig.update_layout(
        title=title,
        xaxis_title="Bucket",
        yaxis_title="CPR (€)",
        height=430,
        hovermode='x',
        plot_bgcolor='#f8f9fa',
        paper_bgcolor='white',
        margin=dict(t=70, b=30, l=20, r=20),
        showlegend=True
    )
    return fig


def create_cpr_chart(center_name: str, df_center: pd.DataFrame, view_type: str, show_rolling_avg: bool = False) -> go.Figure:
    fig = go.Figure()
    title = f"{center_name} - {view_type} CPR"

    if df_center is None or df_center.empty:
        fig.update_layout(height=360, title=title, xaxis_title="Bucket", yaxis_title="CPR (€)")
        return fig

    # Ensure categorical order by bucket_idx
    df_center = df_center.sort_values('bucket_idx')

    fig.add_trace(go.Scatter(
        x=df_center['bucket_label'],
        y=df_center['cpr'],
        mode='lines+markers',
        name='CPR',
        line=dict(color='#28a745', width=3),
        marker=dict(size=8),
        hovertemplate=(
            '<b>%{x}</b><br>'
            '<b>Range:</b> %{customdata[0]} → %{customdata[1]}<br>'
            '<b>CPR:</b> €%{y:.2f}<br>'
            '<b>Spend:</b> €%{customdata[2]:,.2f}<br>'
            '<b>Leads:</b> %{customdata[3]:,}<extra></extra>'
        ),
        customdata=list(zip(
            pd.to_datetime(df_center['bucket_start']).dt.strftime('%Y-%m-%d'),
            pd.to_datetime(df_center['bucket_end']).dt.strftime('%Y-%m-%d'),
            df_center['spend'],
            df_center['leads']
        ))
    ))

    # Optional rolling avg for Daily only
    if show_rolling_avg and view_type == 'Daily':
        rolling = df_center['cpr'].rolling(window=7, min_periods=1).mean()
        fig.add_trace(go.Scatter(
            x=df_center['bucket_label'],
            y=rolling,
            mode='lines',
            name='7-Day Avg',
            line=dict(color='#ffc107', width=2, dash='dash')
        ))

    avg_cpr = df_center['cpr'].mean()
    fig.add_hline(y=avg_cpr, line_dash='dot', line_color='#dc3545',
                  annotation_text=f'Avg: €{avg_cpr:.2f}',
                  annotation_position='top right')

    fig.update_layout(
        title=title,
        xaxis_title="Bucket",
        yaxis_title="CPR (€)",
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
    - view_type now comes from the sidebar/router; no date/view controls on this page.
    """
    st.title(PAGE_TITLE)

    # Build centers_config from selected_centers and CENTERS
    from config import CENTERS
    centers_config = [c for c in CENTERS if c['centerName'] in selected_centers]

    # Use dates and view_type provided by sidebar/router
    filter_start = start_date
    filter_end = end_date

    # Display-only toggle (kept on page)
    show_rolling = st.checkbox("7-day rolling (Daily only)", value=False, key="cpr_rolling_avg")

    if filter_start > filter_end:
        st.warning("Start date must be before or equal to end date.")
        return

    # Compute bucket count and estimate calls
    buckets_preview = get_buckets_labeled(filter_start, filter_end, view_type)
    est_calls = len(buckets_preview) * len(centers_config)
    if est_calls > 160:
        st.caption(f"Note: This request may trigger ~{est_calls} center-bucket calculations. Caching is enabled.")

    # Fetch data
    with st.spinner("Fetching and aggregating CPR data..."):
        df_points, df_combined, buckets = fetch_and_process_cpr_data(
            centers_config, filter_start, filter_end, access_token, view_type
        )

    # Rank best performing centers (Top 3 by lowest CPR)
    top3, all_stats = _rank_best_centers(df_points)

    st.subheader("🏆 Best CPR Performers (Lowest Cost)")
    if top3.empty:
        st.info("No center performance available for the selected range/view.")
    else:
        cols = st.columns(3) if len(top3) >= 3 else st.columns(len(top3))
        gradients = [
            "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
            "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
            "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
        ]
        medals = ["🥇", "🥈", "🥉"]

        for i, (_, row) in enumerate(top3.iterrows()):
            bg = gradients[i % len(gradients)]
            medal = medals[i] if i < len(medals) else "🏅"
            with cols[i]:
                st.markdown(
                    f"""
                    <div style="
                        background: {bg};
                        padding: 18px;
                        border-radius: 12px;
                        color: white;
                        box-shadow: 0 6px 14px rgba(0,0,0,0.12);
                    ">
                        <div style="font-size: 22px; margin-bottom: 6px;">{medal} {row['centerName']}</div>
                        <div style="font-size: 28px; font-weight: 700; margin-bottom: 8px;">
                            €{row['avg_cpr']:.2f} CPR
                        </div>
                        <div style="opacity: 0.95;">
                            Leads: {int(row['total_leads']):,} • Spend: €{row['total_spend']:,.2f}
                        </div>
                        <div style="opacity: 0.9; font-size: 14px; margin-top: 4px;">
                            Avg LP Conv: {row['avg_lpconv']:.2f}%
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

    # Optional: full stats table for transparency
    with st.expander("All centers ranking (Avg CPR)", expanded=False):
        if not all_stats.empty:
            st.dataframe(
                all_stats.rename(columns={
                    'centerName': 'Center',
                    'avg_cpr': 'Avg CPR (€)',
                    'total_spend': 'Total Spend (€)',
                    'total_leads': 'Leads (sum)',
                    'avg_lpconv': 'Avg LP Conv (%)'
                }),
                use_container_width=True
            )

    st.markdown("")

    # Combined (All Centers) chart
    st.subheader("Overall Performance")
    st.plotly_chart(
        create_combined_chart(df_combined, view_type), 
        use_container_width=True,
        config={"displayModeBar": False}
    )
    
    # Summary metrics for combined chart
    if not df_combined.empty:
        overall_avg_cpr = df_combined['weighted_cpr'].mean()
        overall_total_leads = df_combined['leads_sum'].sum()
        # Calculate overall LP conversion from all data points with leads > 0
        df_with_leads = df_points[df_points['leads'] > 0].copy()
        if not df_with_leads.empty:
            avg_lp_conv = df_with_leads['lp_conversion'].mean()
            st.markdown(f"**Summary (All Centers):** Avg CPR: €{overall_avg_cpr:.2f} | Total Leads: {int(overall_total_leads):,} | Avg LP Conversion: {avg_lp_conv:.2f}%")
        else:
            st.markdown(f"**Summary (All Centers):** Avg CPR: €{overall_avg_cpr:.2f} | Total Leads: {int(overall_total_leads):,} | Avg LP Conversion: N/A")
    
    st.markdown("")

    # Per-center charts
    if df_points is None or df_points.empty:
        st.info("No data available for the selected range/view.")
        return

    center_list = sorted(df_points['centerName'].unique())
    st.subheader("By Center")

    # Render charts in a responsive grid: 2 columns
    cols = st.columns(2)
    for i, center in enumerate(center_list):
        df_c = df_points[df_points['centerName'] == center].copy()
        with cols[i % 2]:
            st.plotly_chart(
                create_cpr_chart(center, df_c, view_type, show_rolling_avg=show_rolling),
                use_container_width=True,
                config={"displayModeBar": False}
            )
            # Summary metrics for this center
            if not df_c.empty:
                center_avg_cpr = df_c['cpr'].mean()
                center_total_leads = df_c['leads'].sum()
                center_avg_lp = df_c['lp_conversion'].mean()
                st.markdown(f"**{center} Summary:** Avg CPR: €{center_avg_cpr:.2f} | Total Leads: {int(center_total_leads):,} | Avg LP Conversion: {center_avg_lp:.2f}%")