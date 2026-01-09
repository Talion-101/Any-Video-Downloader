import streamlit as st
import os
import time
from core.downloader import VideoAnalyzer, VideoDownloader
from core.history import HistoryManager

# --- Config ---
st.set_page_config(page_title="Any Video Downloader", page_icon="🎬", layout="centered")

# --- Styles ---
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3em;
    }
    .thumb-img {
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# --- State Management ---
if 'analyzed_data' not in st.session_state:
    st.session_state.analyzed_data = None
if 'download_done' not in st.session_state:
    st.session_state.download_done = None

# --- Logic ---
analyzer = VideoAnalyzer()

def on_progress(status, percent):
    # Update progress bar
    progress_bar.progress(percent)
    status_text.text(status)

downloader = VideoDownloader(callback=on_progress)

# --- UI ---
st.title("🎬 Any Video Downloader")
st.write("Download videos and playlists from YouTube, Vimeo, and more.")

# Input
url = st.text_input("Video URL", placeholder="Paste link here...")

if st.button("Analyze Link", type="primary"):
    if not url:
        st.error("Please enter a URL.")
    else:
        with st.spinner("Fetching metadata..."):
            data = analyzer.extract_info(url)
            if 'error' in data:
                st.error(f"Error: {data['error']}")
            else:
                st.session_state.analyzed_data = data
                st.session_state.download_done = None # Reset
                st.success("Metadata loaded!")

# Results
if st.session_state.analyzed_data:
    data = st.session_state.analyzed_data
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        if data.get('thumbnail'):
            st.image(data['thumbnail'], use_container_width=True)
        else:
            st.warning("No Thumbnail")
            
    with col2:
        st.subheader(data.get('title', 'Unknown Title'))
        st.caption(f"Source: {data.get('webpage_url', '')}")
        
        # Formats
        formats = data.get('formats', [])
        format_labels = [f['label'] for f in formats]
        selected_label = st.selectbox("Select Format", format_labels)
        
        selected_format = next((f for f in formats if f['label'] == selected_label), None)
        
        # Download Action
        if st.button("Download Now"):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            output_path = "downloads"
            # In Streamlit Cloud, we might want to use a tmp dir, but locally 'downloads' is fine.
            
            try:
                # We need to capture the filename to serve it back
                # This is tricky with yt-dlp's dynamic naming.
                # For this MVP, we will rely on yt-dlp returning status or scanning the dir.
                # Actually, let's assume single file for now or zip for playlists (future).
                
                # Simplified: Run download
                # Note: This runs in main thread, blocking UI, but updating progress via placeholder works.
                downloader.download_video(data['webpage_url'], selected_format, output_path)
                
                st.session_state.download_done = True
                st.success("Download Finished!")
                
                # Find the latest file in downloads folder to offer
                # (A simple heuristic for MVP)
                list_of_files = os.listdir(output_path)
                full_path = max([os.path.join(output_path, f) for f in list_of_files], key=os.path.getctime)
                
                with open(full_path, "rb") as file:
                   btn = st.download_button(
                        label="Save File",
                        data=file,
                        file_name=os.path.basename(full_path),
                        mime="application/octet-stream"
                    )
            except Exception as e:
                st.error(f"Download Error: {e}")

# History Sidebar
with st.sidebar:
    st.header("History")
    mgr = HistoryManager(filepath="history.json") # Saves to root of app dir
    history = mgr.get_history()
    
    if st.button("Refresh History"):
        pass 
        
    for item in history:
        st.markdown(f"**{item['title']}**")
        st.caption(f"{item['status']} • {item['format_label']}")
        st.divider()
