import yt_dlp
import json

def analyze_playlist():
    # A small playlist example (YouTube)
    url = "https://www.youtube.com/playlist?list=PLzMcBGfZo4-mP7qA9cagfTq4k2t7B5N_E"
    
    ydl_opts = {
        'quiet': True,
        'extract_flat': 'in_playlist', # Just get video titles/ids, don't fetch deep info for every single one yet
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        print(f"Type: {info.get('_type')}")
        print(f"Title: {info.get('title')}")
        print(f"Entry Count: {len(info.get('entries', []))}")
        
        # Check first entry
        if info.get('entries'):
            print("First Entry Sample:", info['entries'][0])

if __name__ == "__main__":
    analyze_playlist()
