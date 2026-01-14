"""
Web UI for YouTube Scraper & Translator using Streamlit.
Light and airy design with modern aesthetics.
"""

import streamlit as st
import requests
import time
from typing import List, Dict

# Configuration
API_URL = "http://127.0.0.1:8000/api"

st.set_page_config(
    page_title="YouTube Scraper & Translator",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- High-End Minimalist Architectural Design ---
# Palette: Matte Cloud White (#FAFBFC) + Micro-cement Grey (#E8EAED)
# Style: High-key, low-contrast, calm, restrained, modern, breathable
st.markdown("""
<style>
    /* === BASE: Matte Cloud White Background === */
    .stApp {
        background-color: #FAFBFC;
        background-image: linear-gradient(180deg, #FAFBFC 0%, #F5F6F8 100%);
    }
    
    /* === FLOATING CARDS: Frosted Glass Effect === */
    [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlock"] {
        background: rgba(255, 255, 255, 0.85);
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 12px;
        border: 0.5px solid rgba(0, 0, 0, 0.04);
        box-shadow: 
            0 1px 3px rgba(0, 0, 0, 0.02),
            0 8px 32px rgba(0, 0, 0, 0.03);
        transition: all 0.4s cubic-bezier(0.23, 1, 0.32, 1);
    }
    
    [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlock"]:hover {
        transform: translateY(-2px);
        box-shadow: 
            0 2px 6px rgba(0, 0, 0, 0.03),
            0 16px 48px rgba(0, 0, 0, 0.06);
        border-color: rgba(0, 0, 0, 0.06);
    }
    
    /* === IMAGES: Soft Ambient Shadow === */
    [data-testid="stImage"] {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06);
    }
    
    [data-testid="stImage"] img {
        border-radius: 12px;
    }
    
    /* === BUTTONS: Minimal Ghost Style === */
    .stButton>button {
        background: transparent;
        color: #3C4043;
        border: 0.5px solid rgba(0, 0, 0, 0.08);
        border-radius: 24px;
        padding: 10px 24px;
        font-size: 13px;
        font-weight: 500;
        letter-spacing: 0.3px;
        transition: all 0.3s ease;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.02);
    }
    
    .stButton>button:hover {
        background: rgba(0, 0, 0, 0.02);
        border-color: rgba(0, 0, 0, 0.12);
        transform: translateY(-1px);
    }
    
    .stButton>button[kind="primary"] {
        background: #3C4043;
        color: #FFFFFF;
        border: none;
        box-shadow: 0 2px 8px rgba(60, 64, 67, 0.15);
    }
    
    .stButton>button[kind="primary"]:hover {
        background: #2D3033;
        box-shadow: 0 4px 16px rgba(60, 64, 67, 0.2);
    }
    
    /* === LINK BUTTONS: Subtle === */
    .stLinkButton>a {
        background: rgba(0, 0, 0, 0.03);
        color: #5F6368 !important;
        border-radius: 20px;
        padding: 8px 20px;
        font-size: 12px;
        font-weight: 500;
        text-decoration: none;
        letter-spacing: 0.2px;
        transition: all 0.3s ease;
    }
    
    .stLinkButton>a:hover {
        background: rgba(0, 0, 0, 0.06);
        color: #3C4043 !important;
    }
    
    /* === SUCCESS: Soft Mint === */
    .stSuccess {
        background: rgba(52, 168, 83, 0.08);
        color: #1E8E3E;
        border-radius: 20px;
        padding: 6px 14px;
        font-size: 12px;
        border: 0.5px solid rgba(52, 168, 83, 0.15);
    }
    
    /* === PROGRESS BAR: Hairline === */
    .stProgress {
        height: 3px;
    }
    
    .stProgress > div {
        background: rgba(0, 0, 0, 0.04);
        border-radius: 2px;
    }
    
    .stProgress > div > div {
        background: linear-gradient(90deg, #5F6368 0%, #3C4043 100%);
        border-radius: 2px;
    }
    
    /* === TYPOGRAPHY: Light & Airy === */
    h1 {
        font-size: 28px;
        font-weight: 300;
        letter-spacing: -0.5px;
        color: #202124;
        margin-bottom: 8px;
    }
    
    h2 {
        font-size: 18px;
        font-weight: 400;
        letter-spacing: -0.2px;
        color: #3C4043;
        margin-bottom: 16px;
    }
    
    h3 {
        font-size: 14px;
        font-weight: 500;
        letter-spacing: 0.1px;
        color: #5F6368;
        margin-bottom: 12px;
    }
    
    p, span {
        font-size: 13px;
        color: #5F6368;
        line-height: 1.6;
    }
    
    /* === CAPTION: Whisper Grey === */
    .stCaption {
        font-size: 11px !important;
        color: #9AA0A6 !important;
        letter-spacing: 0.3px;
    }
    
    /* === INPUT: Minimal Hairline === */
    .stTextInput>div>div>input {
        background: rgba(255, 255, 255, 0.8);
        border: 0.5px solid rgba(0, 0, 0, 0.06);
        border-radius: 12px;
        padding: 14px 18px;
        font-size: 14px;
        color: #3C4043;
        transition: all 0.3s ease;
    }
    
    .stTextInput>div>div>input:focus {
        border-color: rgba(0, 0, 0, 0.12);
        box-shadow: 0 0 0 4px rgba(0, 0, 0, 0.02);
    }
    
    .stTextInput>div>div>input::placeholder {
        color: #BDC1C6;
    }
    
    /* === SELECTBOX: Clean === */
    .stSelectbox>div>div {
        background: rgba(255, 255, 255, 0.8);
        border: 0.5px solid rgba(0, 0, 0, 0.06);
        border-radius: 12px;
        font-size: 13px;
    }
    
    /* === EXPANDER: Weightless === */
    .streamlit-expanderHeader {
        background: transparent;
        border: none;
        font-size: 13px;
        font-weight: 500;
        color: #5F6368;
        padding: 12px 0;
    }
    
    /* === DIVIDER: Hairline === */
    hr {
        margin: 24px 0;
        border: none;
        height: 0.5px;
        background: rgba(0, 0, 0, 0.04);
    }
    
    /* === SPACING: Expansive Negative Space === */
    .element-container {
        margin-bottom: 8px;
    }
    
    [data-testid="column"] {
        padding: 0 12px;
    }
    
    /* === SCROLLBAR: Invisible === */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    
    ::-webkit-scrollbar-track {
        background: transparent;
    }
    
    ::-webkit-scrollbar-thumb {
        background: rgba(0, 0, 0, 0.1);
        border-radius: 3px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(0, 0, 0, 0.15);
    }
    
    /* === VIDEO PLAYER === */
    video {
        border-radius: 12px;
        box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08);
    }
    
    /* === INFO/WARNING: Soft === */
    .stInfo {
        background: rgba(66, 133, 244, 0.06);
        border: 0.5px solid rgba(66, 133, 244, 0.12);
        border-radius: 12px;
        color: #1A73E8;
    }
    
    .stWarning {
        background: rgba(251, 188, 4, 0.06);
        border: 0.5px solid rgba(251, 188, 4, 0.15);
        border-radius: 12px;
        color: #E37400;
    }
</style>
""", unsafe_allow_html=True)

# --- Session State ---
if 'queue' not in st.session_state:
    st.session_state.queue = [] 
if 'tasks' not in st.session_state:
    st.session_state.tasks = []
if 'search_results' not in st.session_state:
    st.session_state.search_results = []
if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = True  # Default ON for real-time progress

# --- Header ---
st.title("🎬 YouTube Scraper & Translator")
st.caption("✨ Light & Modern Design")

st.divider()

# --- Search Bar ---
with st.container():
    col_s1, col_s2, col_s3 = st.columns([3, 1, 1])
    with col_s1:
        query = st.text_input("🔍 Search YouTube", placeholder="Enter keywords...", label_visibility="collapsed")
    with col_s2:
        date_filter = st.selectbox("📅 Upload Date", 
                                 options=["today", "now-7days", "now-30days", "now-1year", "all"],
                                 index=2,
                                 label_visibility="collapsed")
    with col_s3:
        search_btn = st.button("🔎 Search", type="primary", use_container_width=True)

    with st.expander("⚙️ Advanced Filters", expanded=False):
        duration_range = st.slider("⏱️ Duration (minutes)", 0, 60, (1, 60))
    
    if search_btn and query:
        with st.spinner("🔍 Searching YouTube..."):
            try:
                payload = {
                    "query": query, 
                    "max_results": 20,
                    "duration_min": duration_range[0] * 60,
                    "duration_max": duration_range[1] * 60,
                    "upload_date": date_filter if date_filter != "all" else None
                }
                payload = {k: v for k, v in payload.items() if v is not None}
                
                response = requests.post(f"{API_URL}/search", params=payload)
                if response.status_code == 200:
                    data = response.json()
                    st.session_state.search_results = data.get("items", [])
                    latency = data.get("latency", 0.0)
                    st.toast(f"✅ Found {len(st.session_state.search_results)} videos in {latency:.2f}s", icon="⚡")
                else:
                    st.error("❌ Search failed. Check API.")
            except Exception as e:
                st.error(f"❌ Error: {e}")

st.divider()

# --- Main Layout ---
c_left, c_right = st.columns([2, 1])

# --- LEFT: Search Results ---
with c_left:
    st.subheader(f"🎥 Results ({len(st.session_state.search_results)})")
    
    if not st.session_state.search_results:
        st.info("🎬 Search for YouTube videos to get started!")
    else:
        # Grid: 2 videos per row
        for i in range(0, len(st.session_state.search_results), 2):
            cols = st.columns(2, gap="medium")
            
            for col_idx, col in enumerate(cols):
                vid_idx = i + col_idx
                if vid_idx >= len(st.session_state.search_results):
                    break
                    
                vid = st.session_state.search_results[vid_idx]
                is_in_queue = any(v['url'] == vid['url'] for v in st.session_state.queue)
                
                with col:
                    with st.container():
                        # Thumbnail
                        st.image(vid['thumbnail_url'], use_container_width=True)
                        
                        # Title
                        title = vid['title']
                        if len(title) > 50:
                            title = title[:47] + "..."
                        st.markdown(f"**{title}**")
                        
                        # Metadata
                        st.caption(f"⏱️ {vid['duration']} · 👁️ {vid['views']}")
                        
                        # Buttons
                        btn_col1, btn_col2 = st.columns([1, 1])
                        with btn_col1:
                            if is_in_queue:
                                st.success("✅ In Queue", icon="✅")
                            else:
                                if st.button("➕ Add", key=f"add_{vid['url']}", use_container_width=True):
                                    st.session_state.queue.append(vid)
                                    st.rerun()
                        with btn_col2:
                            st.link_button("🔗 View", vid['url'], use_container_width=True)

# --- RIGHT: Workspace ---
with c_right:
    # Queue
    st.subheader(f"📋 Queue ({len(st.session_state.queue)})")
    
    if not st.session_state.queue:
        st.info("📭 Queue is empty")
    else:
        for i, item in enumerate(st.session_state.queue):
            with st.container():
                qc1, qc2 = st.columns([5, 1])
                with qc1:
                    title = item['title']
                    if len(title) > 30:
                        title = title[:27] + "..."
                    st.markdown(f"**{i+1}.** {title}")
                with qc2:
                    if st.button("🗑️", key=f"del_{i}", help="Remove"):
                        st.session_state.queue.pop(i)
                        st.rerun()
        
        if st.button("🧹 Clear All", use_container_width=True):
            st.session_state.queue = []
            st.rerun()

    st.divider()

    # Settings
    with st.expander("⚙️ Settings", expanded=True):
        font_size = st.slider("📏 Font Size", 20, 80, 40)
        position = st.selectbox("📍 Position", ["bottom", "mid", "top"], index=0)

    st.write("")
    
    # Start Processing
    if st.button("🚀 Start Processing", type="primary", disabled=len(st.session_state.queue) == 0, use_container_width=True):
        for vid in st.session_state.queue:
            payload = {
                "url": vid['url'],
                "style": {
                    "font_size": font_size,
                    "position": position,
                }
            }
            try:
                requests.post(f"{API_URL}/tasks", json=payload)
            except:
                st.error("❌ Failed to start task")
        
        st.session_state.queue = []
        st.toast("✅ Tasks started!", icon="🚀")
        st.rerun()

    st.divider()

    # Progress
    st.subheader("📊 Progress")
    
    col_r1, col_r2 = st.columns([1, 1])
    with col_r1:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()
    with col_r2:
        auto_refresh = st.checkbox("Auto", value=st.session_state.auto_refresh)
        st.session_state.auto_refresh = auto_refresh

    # Fetch tasks
    try:
        r = requests.get(f"{API_URL}/tasks")
        if r.status_code == 200:
            tasks = r.json()
            if not tasks:
                st.info("🎯 No active tasks")
            else:
                # Show progress for running tasks
                running_tasks = [t for t in tasks if t['status'] in ['pending', 'running']]
                for task in reversed(running_tasks[-3:]):
                    with st.container():
                        # Task header with stage indicator
                        stage = task.get('stage', 'unknown')
                        stage_emoji = {
                            'download': '📥',
                            'subtitle': '📝',
                            'translation': '🌐',
                            'burning': '🔥',
                            'completed': '✅',
                            'failed': '❌'
                        }.get(stage, '⚙️')
                        
                        st.caption(f"{stage_emoji} **{task.get('message', 'Processing...')}**")
                        
                        # Progress bar with percentage
                        progress = task.get('progress', 0)
                        st.progress(progress, text=f"{int(progress*100)}%")
                        
                        # Stage breakdown
                        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
                        with col_s1:
                            st.caption("📥" if progress >= 0.3 else "⬜")
                        with col_s2:
                            st.caption("📝" if progress >= 0.4 else "⬜")
                        with col_s3:
                            st.caption("🌐" if progress >= 0.5 else "⬜")
                        with col_s4:
                            st.caption("🔥" if progress >= 0.5 else "⬜")
                        
                        st.markdown("---")
                
                # Show completed videos
                completed_tasks = [t for t in tasks if t['status'] == 'completed' and 'video_filename' in t]
                if completed_tasks:
                    st.divider()
                    st.subheader("🎬 Completed Videos")
                    
                    for task in reversed(completed_tasks[-3:]):  # Show last 3 completed
                        with st.expander(f"📹 {task.get('video_filename', 'Video')[:40]}...", expanded=False):
                            video_url = f"http://127.0.0.1:8000/output/{task['video_filename']}"
                            st.video(video_url)
                            st.caption(f"✅ Completed: {task.get('message', 'Done')}")
                            
                            # Download button
                            col_d1, col_d2 = st.columns([1, 1])
                            with col_d1:
                                st.link_button("📥 Download", video_url, use_container_width=True)
                            with col_d2:
                                if st.button("🗑️ Remove", key=f"remove_{task['task_id']}", use_container_width=True):
                                    st.toast("⚠️ Delete feature coming soon")
    except:
        st.warning("⚠️ Cannot connect to API")

# Auto-refresh
if st.session_state.auto_refresh:
    time.sleep(1)  # Fast refresh for real-time progress
    st.rerun()
