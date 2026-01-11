"""
Web UI for YouTube Scraper & Translator using Streamlit.
Connects to the local API server.
"""

import streamlit as st
import requests
import pandas as pd
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

# --- Custom CSS ---
st.markdown("""
<style>
    /* Global Theme */
    .stApp {
        background-color: #0E1117;
    }
    
    /* Card Style */
    .video-card {
        background-color: #1E2129;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 20px;
        border: 1px solid #30333D;
        transition: transform 0.2s;
    }
    .video-card:hover {
        border-color: #FF4B4B;
    }
    
    /* Queue Item */
    .queue-item {
        background-color: #262730;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 8px;
        border-left: 3px solid #FF4B4B;
    }
    
    /* Buttons */
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        font-weight: 600;
    }
    
    /* Top Bar */
    .search-container {
        padding: 20px 0;
    }
    
    /* Status indicators */
    .status-badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: bold;
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

# --- Layout ---

# 1. Top Bar: Search & Filters
with st.container():
    st.title("🎬 YouTube Scraper & Chinese Adapter")
    
    col_s1, col_s2, col_s3 = st.columns([3, 1, 1])
    with col_s1:
        query = st.text_input("Search Query", placeholder="Enter keywords...", label_visibility="collapsed")
    with col_s2:
        date_filter = st.selectbox("Upload Date", 
                                 options=["today", "now-7days", "now-30days", "now-1year", "all"],
                                 index=2,
                                 label_visibility="collapsed")
    with col_s3:
        search_btn = st.button("Search Videos", type="primary")

    with st.expander("More Filters", expanded=False):
        duration_range = st.slider("Duration (minutes)", 0, 60, (5, 20))
    
    if search_btn and query:
        with st.spinner("Searching YouTube..."):
            try:
                payload = {
                    "query": query, 
                    "max_results": 10,
                    "duration_min": duration_range[0] * 60,
                    "duration_max": duration_range[1] * 60,
                    "upload_date": date_filter if date_filter != "all" else None
                }
                # Remove None values
                payload = {k: v for k, v in payload.items() if v is not None}
                
                response = requests.post(f"{API_URL}/search", params=payload)
                if response.status_code == 200:
                    data = response.json()
                    st.session_state.search_results = data.get("items", [])
                    latency = data.get("latency", 0.0)
                    st.toast(f"Search completed in {latency:.2f}s", icon="⚡")
                else:
                    st.error("Search failed. Check API.")
            except Exception as e:
                st.error(f"Error: {e}")

st.divider()

# 2. Main Content: Left (Results) & Right (Workspace)
c_left, c_right = st.columns([1.5, 1])

# --- LEFT COLUMN: Search Results ---
with c_left:
    st.subheader(f"Search Results ({len(st.session_state.search_results)})")
    
    if not st.session_state.search_results:
        st.info("Try searching for something!")
    
    for vid in st.session_state.search_results:
        # Check if already in queue
        is_in_queue = any(v['url'] == vid['url'] for v in st.session_state.queue)
        
        # Grid layout for card
        with st.container():
            col_img, col_info, col_act = st.columns([2, 3, 1.2])
            
            with col_img:
                st.image(vid['thumbnail_url'], use_container_width=True)
            
            with col_info:
                st.markdown(f"**{vid['title']}**")
                st.caption(f"⏱️ {vid['duration']}  |  👀 {vid['views']}  |  📅 {vid['upload_date']}")
                st.markdown(f"<p style='font-size:12px; color:#aaa'>{vid['description'][:100]}...</p>", unsafe_allow_html=True)
            
            with col_act:
                st.write("") # Spacer
                if is_in_queue:
                    st.success("Added")
                else:
                    if st.button("➕ Add", key=f"add_{vid['url']}"):
                        st.session_state.queue.append(vid)
                        st.rerun()
                
                # Preview Link
                st.markdown(f"[Preview Video]({vid['url']})")
                
        st.markdown("---")

# --- RIGHT COLUMN: Workspace ---
with c_right:
    # 1. Queue Section
    with st.container():
        st.subheader("📋 Task Queue")
        
        if not st.session_state.queue:
            st.info("Empty. Add videos from search.")
        else:
            # Use form to batch delete or just list them cleaner
            for i, item in enumerate(st.session_state.queue):
                with st.container():
                    qc1, qc2 = st.columns([5, 1])
                    with qc1:
                         st.markdown(f"**{i+1}. {item['title'][:40]}...**")
                    with qc2:
                         if st.button("🗑️", key=f"del_{i}", help="Remove from queue"):
                             st.session_state.queue.pop(i)
                             st.rerun()
            
            if st.button("Clear All", type="secondary"):
                st.session_state.queue = []
                st.rerun()

    st.divider()

    # 2. Config Section
    with st.expander("⚙️ Processing Settings", expanded=True):
        sc1, sc2 = st.columns(2)
        with sc1:
            font_color = st.color_picker("Color", "#FFFFFF")
            position = st.selectbox("Pos", ["bottom", "mid", "top"], index=0)
        with sc2:
            font_size = st.number_input("Size", 20, 80, 40)
            langs = st.multiselect("Lang", ["zh", "en"], ["zh", "en"])

    st.write("")
    
    # 3. Action Section
    if st.button("🚀 Start Batch Processing", type="primary", disabled=len(st.session_state.queue) == 0):
        for vid in st.session_state.queue:
            payload = {
                "url": vid['url'],
                "style": {
                    "font_color": font_color,
                    "position": position,
                    "languages": ["zh", "en"], # Only fixed for demo, real mapping needed if multiselect changes
                    "font_size": font_size
                }
            }
            try:
                requests.post(f"{API_URL}/tasks", json=payload)
            except:
                st.error("Failed to start task")
        
        st.session_state.tasks_started = True
        st.session_state.queue = [] # Clear queue after start
        st.rerun()

    # 4. Progress Section
    st.subheader("📊 Progress")
    
    # Auto-refresh mechanism
    if st.button("🔄 Refresh"):
        st.rerun()

    # Fetch tasks
    try:
        r = requests.get(f"{API_URL}/tasks")
        if r.status_code == 200:
            tasks = r.json()
            # Show latest tasks first
            for task in reversed(tasks[-5:]): # Show last 5
                st.markdown(f"**Task: {task['task_id'][:8]}**")
                st.progress(task['progress'])
                st.caption(f"Status: {task['status']} | {task['message']}")
                if task.get("result_path"):
                    st.success(f"Output: {task['result_path']}")
                st.markdown("---")
    except:
        st.error("Cannot connect to API")

    # Shutdown Button at bottom
    st.write("")
    st.write("")
    if st.button("🛑 System Shutdown"):
         requests.post(f"{API_URL}/shutdown")
         st.stop()
