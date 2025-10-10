# pages/rates_analysis.py
# SIMPLIFIED VERSION - Direct API calls with view-based date splitting and parallel batch processing
# + Visualization: combined chart and per-center charts with ONLY rate curves
# + Best performing centers cards
# FIXED: All Streamlit calls now happen in main thread only
# ADD: Cleanup of worker threads after data fetching
# UPDATED: Responsive Plotly charts, legend-based curve toggle/isolate, fullscreen-friendly modebar,
#          and hover popups with From → To ranges for Weekly, 3 Days, Monthly (works for all views)

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import List, Dict, Tuple
import json
import time
import concurrent.futures
import threading

import pandas as pd
import plotly.graph_objects as go

from api_client import fetch_rates_kpis_for_centers

PAGE_TITLE = "Rates Analysis"
VIEW_TYPES = ["Daily", "3 Days", "Weekly", "Two Weeks", "Monthly"]

# Configuration constants
MAX_RETRIES = 3
RETRY_DELAY = 2
RATE_LIMIT_DELAY = 0.3  # Reduced delay for faster processing
MAX_WORKERS = 10  # Number of parallel workers
EXECUTOR_THREAD_PREFIX = "rates-worker"

try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False


def _safe_int(v, default=0):
    try:
        return int(v)
    except Exception:
        return default


def _safe_float(v, default=0.0):
    try:
        return float(v)
    except Exception:
        return default


def _parse_percent(val) -> float:
    """
    Convert to percent in 0..100 consistently.
    Handles: None, "12.3%", "0.123", 12.3, 0.123
    """
    if val is None:
        return 0.0
    try:
        if isinstance(val, str):
            v = val.strip()
            if v.endswith('%'):
                return float(v[:-1])
            fv = float(v)
        else:
            fv = float(val)
        return fv * 100.0 if fv <= 1.5 else fv
    except Exception:
        return 0.0


def split_date_range_by_view(start_date: date, end_date: date, view_type: str) -> List[Tuple[date, date, str]]:
    periods = []
    cur = start_date

    if view_type == 'Daily':
        day_num = 1
        while cur <= end_date:
            label = f"Day {day_num}"
            periods.append((cur, cur, label))
            cur += timedelta(days=1)
            day_num += 1

    elif view_type == '3 Days':
        period_num = 1
        while cur <= end_date:
            period_end = min(cur + timedelta(days=2), end_date)
            label = f"3-Day {period_num}"
            periods.append((cur, period_end, label))
            cur = period_end + timedelta(days=1)
            period_num += 1

    elif view_type == 'Weekly':
        week_num = 1
        while cur <= end_date:
            period_end = min(cur + timedelta(days=6), end_date)
            label = f"Week {week_num}"
            periods.append((cur, period_end, label))
            cur = period_end + timedelta(days=1)
            week_num += 1

    elif view_type == 'Two Weeks':
        period_num = 1
        while cur <= end_date:
            period_end = min(cur + timedelta(days=13), end_date)
            label = f"2W {period_num}"
            periods.append((cur, period_end, label))
            cur = period_end + timedelta(days=1)
            period_num += 1

    elif view_type == 'Monthly':
        while cur <= end_date:
            if cur.month == 12:
                next_month_start = date(cur.year + 1, 1, 1)
            else:
                next_month_start = date(cur.year, cur.month + 1, 1)
            month_end = next_month_start - timedelta(days=1)
            period_end = min(month_end, end_date)
            label = _month_label(cur)
            periods.append((cur, period_end, label))
            cur = next_month_start

    return periods


def _month_label(d: date) -> str:
    return datetime(d.year, d.month, 1).strftime("%b %Y")


def fetch_with_retry(start_date: date, end_date: date, centers: List[str], label: str) -> Tuple[Dict, List[str]]:
    """Worker function - NO Streamlit calls here"""
    errors = []
    s_str = start_date.strftime('%Y-%m-%d')
    e_str = end_date.strftime('%Y-%m-%d')
    
    for attempt in range(MAX_RETRIES):
        try:
            time.sleep(RATE_LIMIT_DELAY)
            results = fetch_rates_kpis_for_centers(s_str, e_str, centers)
            return {
                'period': label,
                'start_date': s_str,
                'end_date': e_str,
                'data': results
            }, errors
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "Too Many Requests" in error_str:
                retry_delay = RETRY_DELAY * (2 ** attempt)
                if attempt < MAX_RETRIES - 1:
                    errors.append(f"Rate limit hit for {label} (attempt {attempt + 1}/{MAX_RETRIES}). Retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                else:
                    errors.append(f"Failed to fetch {label} after {MAX_RETRIES} attempts: {error_str}")
                    return {
                        'period': label,
                        'start_date': s_str,
                        'end_date': e_str,
                        'data': None,
                        'error': error_str
                    }, errors
            else:
                errors.append(f"Error fetching {label} (attempt {attempt + 1}/{MAX_RETRIES}): {error_str}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
                else:
                    return {
                        'period': label,
                        'start_date': s_str,
                        'end_date': e_str,
                        'data': None,
                        'error': error_str
                    }, errors

    return {
        'period': label,
        'start_date': s_str,
        'end_date': e_str,
        'data': None,
        'error': 'Unknown error'
    }, errors


def fetch_period_wrapper(args):
    """Wrapper for parallel execution - NO Streamlit calls"""
    period_start, period_end, label, centers = args
    return fetch_with_retry(period_start, period_end, centers, label)


def cleanup_threads(prefix: str = EXECUTOR_THREAD_PREFIX) -> int:
    """
    Best-effort cleanup: mark any lingering worker threads with a given prefix as daemon
    so they cannot keep the app alive. Returns the number of threads touched.
    Note: Python cannot forcibly kill threads; using ThreadPoolExecutor within a 'with'
    block ensures threads should end naturally after work completes.
    """
    touched = 0
    for t in threading.enumerate():
        if t is threading.current_thread():
            continue
        name = getattr(t, "name", "")
        if name.startswith(prefix) and not t.daemon:
            try:
                t.daemon = True
                touched += 1
            except Exception:
                pass
    return touched


def fetch_rates_data(
    selected_centers: List[str],
    start_date: date,
    end_date: date,
    view_type: str
) -> Tuple[List[Dict], List[str]]:
    """Main thread function - Streamlit calls OK here"""
    all_errors = []
    if not selected_centers:
        all_errors.append("No centers selected.")
        return [], all_errors
    
    periods = split_date_range_by_view(start_date, end_date, view_type)
    if not periods:
        all_errors.append("No periods generated from date range.")
        return [], all_errors
    
    # Show warning BEFORE starting threads (main thread only)
    if STREAMLIT_AVAILABLE and len(periods) > 100:
        st.warning(f"⚠️ Warning: {len(periods)} periods will be fetched. This may take a while but uses parallel processing.")

    # Initialize progress tracking in main thread
    progress_bar = None
    status_text = None
    if STREAMLIT_AVAILABLE:
        progress_bar = st.progress(0)
        status_text = st.empty()
        status_text.info(f"⏳ Fetching data for {len(periods)} periods using {MAX_WORKERS} workers...")

    results = []
    fetch_args = [(ps, pe, label, selected_centers) for ps, pe, label in periods]

    # Run parallel fetching (workers don't call Streamlit)
    # IMPORTANT: thread_name_prefix helps us identify threads for cleanup
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=MAX_WORKERS,
        thread_name_prefix=EXECUTOR_THREAD_PREFIX
    ) as executor:
        future_to_label = {executor.submit(fetch_period_wrapper, args): args[2] for args in fetch_args}
        completed = 0
        
        for future in concurrent.futures.as_completed(future_to_label):
            label = future_to_label[future]
            try:
                result, errs = future.result()
                results.append(result)
                all_errors.extend(errs)
            except Exception as e:
                all_errors.append(f"Critical error processing {label}: {str(e)}")
                results.append({
                    'period': label,
                    'start_date': None,
                    'end_date': None,
                    'data': None,
                    'error': str(e)
                })
            
            # Update progress in main thread only
            completed += 1
            if STREAMLIT_AVAILABLE and progress_bar is not None:
                progress_bar.progress(completed / len(periods))
                if status_text is not None:
                    status_text.text(f"Fetching data... ({completed}/{len(periods)}) - {len(all_errors)} errors")

    # After executor exits, threads should be done. Best-effort cleanup:
    touched = cleanup_threads()
    if STREAMLIT_AVAILABLE and touched and status_text is not None:
        status_text.info(f"Cleaned up {touched} worker thread(s).")

    # Clean up progress indicators (main thread)
    if STREAMLIT_AVAILABLE:
        if progress_bar is not None:
            progress_bar.empty()
        if status_text is not None:
            status_text.empty()

    # Keep period order
    results = _sort_results(results)
    return results, all_errors


def _sort_results(results: List[Dict]) -> List[Dict]:
    def key_fn(r):
        label = r.get('period', '')
        try:
            if label.startswith('Day '):
                return ('D', int(label.split('Day ')[1]))
            if label.startswith('3-Day '):
                return ('T', int(label.split('3-Day ')[1]))
            if label.startswith('Week '):
                return ('W', int(label.split('Week ')[1]))
            if label.startswith('2W '):
                return ('2', int(label.split('2W ')[1]))
            # Monthly: sort by start_date
            return ('M', r.get('start_date') or '')
        except Exception:
            return ('Z', 0)
    return sorted(results, key=key_fn)


def _results_to_dataframe(periods: List[Dict]) -> pd.DataFrame:
    """
    Flatten API results into tidy rows with robust parsing.
    Handles various JSON structures and percent formats.
    """
    rows = []
    idx = 1
    for p in periods:
        label = p.get('period')
        s = p.get('start_date')
        e = p.get('end_date')
        data = p.get('data')

        if not data or (isinstance(data, dict) and data.get('error')):
            idx += 1
            continue

        # normalize container: allow list or dict with "results"/"data" list
        if isinstance(data, dict):
            if isinstance(data.get('results'), list):
                items = data['results']
            elif isinstance(data.get('data'), list):
                items = data['data']
            else:
                items = list(data.values()) if any(isinstance(v, dict) for v in data.values()) else []
        else:
            items = data  # assume list

        for item in (items or []):
            if not isinstance(item, dict):
                continue

            center = (
                item.get('centerName')
                or item.get('name')
                or item.get('center')
                or item.get('center_name')
                or "Unknown"
            )

            metrics = item.get('metrics') if isinstance(item.get('metrics'), dict) else item

            confirmed = _safe_int(
                metrics.get('num_confirmed', metrics.get('confirmed', metrics.get('confirmations', 0)))
            )
            showed = _safe_int(
                metrics.get('num_showed', metrics.get('showed', metrics.get('shows', 0)))
            )
            concretized = _safe_int(
                metrics.get('num_concretise', metrics.get('concretized', metrics.get('conversions', 0)))
            )

            rates = metrics.get('rates') if isinstance(metrics.get('rates'), dict) else {}
            confirmed_rate = _parse_percent(
                rates.get('confirmation_rate', 
                         metrics.get('confirmation_rate',
                                   metrics.get('confirmed_rate')))
            )
            showed_rate = _parse_percent(
                rates.get('show_up_rate',
                         metrics.get('show_up_rate',
                                   metrics.get('showed_rate')))
            )
            concretized_rate = _parse_percent(
                rates.get('conversion_rate',
                         metrics.get('conversion_rate',
                                   metrics.get('concretized_rate')))
            )

            rows.append({
                'bucket_idx': idx,
                'bucket_label': label,
                'bucket_start': s,
                'bucket_end': e,
                'centerName': center,
                'confirmed': confirmed,
                'showed': showed,
                'concretized': concretized,
                'confirmed_rate': confirmed_rate,
                'showed_rate': showed_rate,
                'concretized_rate': concretized_rate
            })
        idx += 1

    df = pd.DataFrame(rows)
    if not df.empty:
        for c in ['confirmed', 'showed', 'concretized',
                  'confirmed_rate', 'showed_rate', 'concretized_rate']:
            df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
        df['bucket_idx'] = pd.to_numeric(df['bucket_idx'], errors='coerce').fillna(0).astype(int)
        df = df.sort_values(['centerName', 'bucket_idx']).reset_index(drop=True)
    return df


def _combined_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()

    grp = df.groupby(['bucket_idx', 'bucket_label', 'bucket_start', 'bucket_end'], as_index=False)

    agg_counts = grp.agg(
        confirmed_sum=('confirmed', 'sum'),
        showed_sum=('showed', 'sum'),
        concretized_sum=('concretized', 'sum'),
        confirmed_rate_avg=('confirmed_rate', 'mean'),
        showed_rate_avg=('showed_rate', 'mean'),
        concretized_rate_avg=('concretized_rate', 'mean'),
    )

    return agg_counts.sort_values(['bucket_idx']).reset_index(drop=True)


def _get_best_centers(df: pd.DataFrame) -> Dict:
    if df is None or df.empty:
        return {}
    
    center_stats = df.groupby('centerName').agg(
        confirmed_rate_avg=('confirmed_rate', 'mean'),
        showed_rate_avg=('showed_rate', 'mean'),
        concretized_rate_avg=('concretized_rate', 'mean'),
        confirmed_total=('confirmed', 'sum'),
        showed_total=('showed', 'sum'),
        concretized_total=('concretized', 'sum'),
    ).reset_index()
    
    best_confirmed = center_stats.loc[center_stats['confirmed_rate_avg'].idxmax()] if not center_stats.empty else None
    best_showed = center_stats.loc[center_stats['showed_rate_avg'].idxmax()] if not center_stats.empty else None
    best_concretized = center_stats.loc[center_stats['concretized_rate_avg'].idxmax()] if not center_stats.empty else None
    
    return {
        'best_confirmed': best_confirmed,
        'best_showed': best_showed,
        'best_concretized': best_concretized,
        'all_centers': center_stats
    }


def _period_hover_labels(labels: pd.Series | list, df_like: pd.DataFrame) -> list:
    """
    Build hover labels that include period label and 'From → To' dates.
    Requires df_like to have bucket_start, bucket_end columns aligned to labels.
    """
    if isinstance(df_like, pd.DataFrame):
        starts = df_like.get('bucket_start', pd.Series([""] * len(df_like)))
        ends = df_like.get('bucket_end', pd.Series([""] * len(df_like)))
    else:
        starts = [""] * len(labels)
        ends = [""] * len(labels)

    hover = []
    for i, lab in enumerate(labels):
        s = starts.iloc[i] if isinstance(starts, pd.Series) else starts[i]
        e = ends.iloc[i] if isinstance(ends, pd.Series) else ends[i]
        if s and e:
            hover.append(f"{lab}<br><b>{s}</b> → <b>{e}</b>")
        else:
            hover.append(f"{lab}")
    return hover


def _make_combined_chart(df_combined: pd.DataFrame, view_type: str) -> go.Figure:
    title = f"All Centers - {view_type} Rates"

    fig = go.Figure()
    if df_combined is None or df_combined.empty:
        fig.update_layout(height=430, title=title)
        return fig

    x = df_combined['bucket_label']
    hover_x = _period_hover_labels(x, df_combined)

    fig.add_trace(go.Scatter(
        x=x, y=df_combined['confirmed_rate_avg'], name='Confirmed Rate',
        mode='lines+markers',
        line=dict(color='#1f77b4', width=3),
        marker=dict(size=8),
        hovertemplate='<b>%{customdata}</b><br>Confirmed Rate: <b>%{y:.2f}%</b><br>Confirmed Count: %{customdata2:,}<extra></extra>',
        customdata=hover_x,
        customdata2=df_combined['confirmed_sum'],
    ))
    fig.add_trace(go.Scatter(
        x=x, y=df_combined['showed_rate_avg'], name='Showed Rate',
        mode='lines+markers',
        line=dict(color='#2ca02c', width=3),
        marker=dict(size=8),
        hovertemplate='<b>%{customdata}</b><br>Showed Rate: <b>%{y:.2f}%</b><br>Showed Count: %{customdata2:,}<extra></extra>',
        customdata=hover_x,
        customdata2=df_combined['showed_sum'],
    ))
    fig.add_trace(go.Scatter(
        x=x, y=df_combined['concretized_rate_avg'], name='Concretized Rate',
        mode='lines+markers',
        line=dict(color='#d62728', width=3),
        marker=dict(size=8),
        hovertemplate='<b>%{customdata}</b><br>Concretized Rate: <b>%{y:.2f}%</b><br>Concretized Count: %{customdata2:,}<extra></extra>',
        customdata=hover_x,
        customdata2=df_combined['concretized_sum'],
    ))

    fig.update_layout(
        title=title,
        hovermode='x unified',
        autosize=True,   # responsive
        height=None,     # let container control height
        margin=dict(t=70, b=50, l=50, r=30),
        plot_bgcolor='#f8f9fa',
        paper_bgcolor='white',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='left', x=0),
        xaxis=dict(title='Period', showgrid=True, gridcolor='#e0e0e0', automargin=True),
        yaxis=dict(title='Rate (%)', rangemode='tozero', showgrid=True, gridcolor='#e0e0e0', automargin=True),
    )
    return fig


def _make_center_chart(center_name: str, df_center: pd.DataFrame, view_type: str) -> go.Figure:
    title = f"{center_name} - {view_type} Rates"
    fig = go.Figure()

    if df_center is None or df_center.empty:
        fig.update_layout(height=420, title=title)
        return fig

    df_center = df_center.sort_values('bucket_idx')
    x = df_center['bucket_label']
    hover_x = _period_hover_labels(x, df_center)

    fig.add_trace(go.Scatter(
        x=x, y=df_center['confirmed_rate'], name='Confirmed Rate',
        mode='lines+markers',
        line=dict(color='#1f77b4', width=3),
        marker=dict(size=8),
        hovertemplate='<b>%{customdata}</b><br>Confirmed Rate: <b>%{y:.2f}%</b><br>Count: %{customdata2:,}<extra></extra>',
        customdata=hover_x,
        customdata2=df_center['confirmed'],
    ))
    fig.add_trace(go.Scatter(
        x=x, y=df_center['showed_rate'], name='Showed Rate',
        mode='lines+markers',
        line=dict(color='#2ca02c', width=3),
        marker=dict(size=8),
        hovertemplate='<b>%{customdata}</b><br>Showed Rate: <b>%{y:.2f}%</b><br>Count: %{customdata2:,}<extra></extra>',
        customdata=hover_x,
        customdata2=df_center['showed'],
    ))
    fig.add_trace(go.Scatter(
        x=x, y=df_center['concretized_rate'], name='Concretized Rate',
        mode='lines+markers',
        line=dict(color='#d62728', width=3),
        marker=dict(size=8),
        hovertemplate='<b>%{customdata}</b><br>Concretized Rate: <b>%{y:.2f}%</b><br>Count: %{customdata2:,}<extra></extra>',
        customdata=hover_x,
        customdata2=df_center['concretized'],
    ))

    fig.update_layout(
        title=title,
        hovermode='x unified',
        autosize=True,  # responsive
        height=None,    # let container control height
        margin=dict(t=70, b=50, l=50, r=30),
        plot_bgcolor='#f8f9fa',
        paper_bgcolor='white',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='left', x=0),
        xaxis=dict(title='Period', showgrid=True, gridcolor='#e0e0e0', automargin=True),
        yaxis=dict(title='Rate (%)', rangemode='tozero', showgrid=True, gridcolor='#e0e0e0', automargin=True),
    )
    return fig


def show(
    selected_centers: List[str],
    start_date: date,
    end_date: date,
    access_token: str = None,
    view_type: str = "Weekly"
) -> Dict:
    if start_date > end_date:
        return {"error": "Start date must be before or equal to end date."}
    if view_type not in VIEW_TYPES:
        return {"error": f"Invalid view_type. Must be one of {VIEW_TYPES}"}

    start_time = time.time()
    api_results, errors = fetch_rates_data(selected_centers, start_date, end_date, view_type)
    execution_time = round(time.time() - start_time, 2)

    result = {
        "view_type": view_type,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "centers": selected_centers,
        "periods": api_results,
        "errors": errors,
        "error_count": len(errors),
        "total_periods": len(api_results),
        "successful_periods": len([r for r in api_results if r.get('data') is not None]),
        "execution_time_seconds": execution_time
    }

    if STREAMLIT_AVAILABLE:
        _display_ui(result)

    return result


def _display_ui(result: Dict):
    st.title("📊 Rates Analysis")

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("View", result["view_type"])
    with col2:
        st.metric("Total Periods", result["total_periods"])
    with col3:
        st.metric("Success", result["successful_periods"])
    with col4:
        st.metric("Errors", result["error_count"])
    with col5:
        st.metric("Time", f"{result['execution_time_seconds']}s")

    st.info(f"📅 {result['start_date']} → {result['end_date']}")
    st.info(f"🏢 Centers: {', '.join(result['centers'])}")

    if result.get("errors"):
        with st.expander(f"⚠️ Errors & Warnings ({result['error_count']})", expanded=False):
            for error in result["errors"]:
                st.error(error)

    if result.get("error"):
        st.error(result["error"])
        return

    df = _results_to_dataframe(result["periods"])
    
    if STREAMLIT_AVAILABLE:
        with st.expander("🔍 Debug Info - Data Sample", expanded=False):
            if df.empty:
                st.warning("DataFrame is empty after parsing!")
                st.write("**Sample of raw API response (first period):**")
                if result.get('periods'):
                    st.json(result['periods'][0])
            else:
                st.write(f"**Total rows parsed:** {len(df)}")
                st.write(f"**Centers found:** {sorted(df['centerName'].unique())}")
                st.dataframe(df.head(10))
                st.write("**Column sums:**")
                st.json({
                    "confirmed_sum": int(df['confirmed'].sum()),
                    "showed_sum": int(df['showed'].sum()),
                    "concretized_sum": int(df['concretized'].sum()),
                })
                st.write("**Rate ranges:**")
                st.json({
                    "confirmed_rate": f"{df['confirmed_rate'].min():.2f} - {df['confirmed_rate'].max():.2f}",
                    "showed_rate": f"{df['showed_rate'].min():.2f} - {df['showed_rate'].max():.2f}",
                    "concretized_rate": f"{df['concretized_rate'].min():.2f} - {df['concretized_rate'].max():.2f}",
                })
    
    if df.empty:
        st.warning("No data returned after parsing. Check the debug info above and raw JSON below.")
        with st.expander("📄 Complete JSON"):
            st.code(json.dumps(result, indent=2, default=str), language="json")
        return

    best_centers = _get_best_centers(df)
    if best_centers:
        st.subheader("🏆 Best Performing Centers")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if best_centers.get('best_confirmed') is not None:
                bc = best_centers['best_confirmed']
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                            padding: 20px; border-radius: 10px; color: white;">
                    <h4 style="margin: 0; color: white;">🥇 Best Confirmed Rate</h4>
                    <h2 style="margin: 10px 0; color: white;">{bc['centerName']}</h2>
                    <p style="font-size: 24px; margin: 5px 0; color: white;"><b>{bc['confirmed_rate_avg']:.2f}%</b></p>
                    <p style="margin: 0; opacity: 0.9; color: white;">Total Confirmed: {int(bc['confirmed_total']):,}</p>
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            if best_centers.get('best_showed') is not None:
                bs = best_centers['best_showed']
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                            padding: 20px; border-radius: 10px; color: white;">
                    <h4 style="margin: 0; color: white;">🥇 Best Showed Rate</h4>
                    <h2 style="margin: 10px 0; color: white;">{bs['centerName']}</h2>
                    <p style="font-size: 24px; margin: 5px 0; color: white;"><b>{bs['showed_rate_avg']:.2f}%</b></p>
                    <p style="margin: 0; opacity: 0.9; color: white;">Total Showed: {int(bs['showed_total']):,}</p>
                </div>
                """, unsafe_allow_html=True)
        
        with col3:
            if best_centers.get('best_concretized') is not None:
                bcon = best_centers['best_concretized']
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); 
                            padding: 20px; border-radius: 10px; color: white;">
                    <h4 style="margin: 0; color: white;">🥇 Best Concretized Rate</h4>
                    <h2 style="margin: 10px 0; color: white;">{bcon['centerName']}</h2>
                    <p style="font-size: 24px; margin: 5px 0; color: white;"><b>{bcon['concretized_rate_avg']:.2f}%</b></p>
                    <p style="margin: 0; opacity: 0.9; color: white;">Total Concretized: {int(bcon['concretized_total']):,}</p>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("")

    df_combined = _combined_dataframe(df)

    st.subheader("Overall Performance")
    st.plotly_chart(
        _make_combined_chart(df_combined, result["view_type"]),
        use_container_width=True,
        config={
            "displayModeBar": True,
            "displaylogo": False,
            "scrollZoom": True,
            "responsive": True,
            "modeBarButtonsToAdd": ["toImage", "zoom2d", "pan2d", "autoScale2d", "resetScale2d", "select2d", "lasso2d"],
            "modeBarButtonsToRemove": [],
            "showTips": False
        }
    )

    if not df_combined.empty:
        avg_conf_rate = df_combined['confirmed_rate_avg'].mean()
        avg_show_rate = df_combined['showed_rate_avg'].mean()
        avg_conc_rate = df_combined['concretized_rate_avg'].mean()
        total_confirmed = int(df_combined['confirmed_sum'].sum())
        total_showed = int(df_combined['showed_sum'].sum())
        total_concretized = int(df_combined['concretized_sum'].sum())
        st.markdown(
            f"• **Avg Confirmed Rate:** {avg_conf_rate:.2f}% | "
            f"**Avg Showed Rate:** {avg_show_rate:.2f}% | "
            f"**Avg Concretized Rate:** {avg_conc_rate:.2f}%  \n"
            f"• **Totals** — Confirmed: {total_confirmed:,}, Showed: {total_showed:,}, Concretized: {total_concretized:,}"
        )

    st.markdown("")

    st.subheader("By Center")
    centers = sorted(df['centerName'].unique())
    cols = st.columns(2)
    for i, center in enumerate(centers):
        df_c = df[df['centerName'] == center].copy()
        with cols[i % 2]:
            st.plotly_chart(
                _make_center_chart(center, df_c, result["view_type"]),
                use_container_width=True,
                config={
                    "displayModeBar": True,
                    "displaylogo": False,
                    "scrollZoom": True,
                    "responsive": True,
                    "modeBarButtonsToAdd": ["toImage", "zoom2d", "pan2d", "autoScale2d", "resetScale2d", "select2d", "lasso2d"],
                    "modeBarButtonsToRemove": [],
                    "showTips": False
                }
            )
            if not df_c.empty:
                s_conf = int(df_c['confirmed'].sum())
                s_show = int(df_c['showed'].sum())
                s_conc = int(df_c['concretized'].sum())
                avg_conf = df_c['confirmed_rate'].mean()
                avg_show = df_c['showed_rate'].mean()
                avg_conc = df_c['concretized_rate'].mean()
                st.markdown(
                    f"**{center}** — Confirmed: {s_conf:,} ({avg_conf:.2f}%) | "
                    f"Showed: {s_show:,} ({avg_show:.2f}%) | "
                    f"Concretized: {s_conc:,} ({avg_conc:.2f}%)"
                )

    with st.expander("📄 Complete JSON"):
        st.code(json.dumps(result, indent=2, default=str), language="json")