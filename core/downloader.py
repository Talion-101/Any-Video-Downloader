import yt_dlp
import threading
import os
from .history import HistoryManager

class VideoAnalyzer:
    def extract_info(self, url):
        """
        Fetches metadata and available formats for the given URL.
        Handles both single videos and playlists.
        """
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': 'in_playlist', # Efficiently check if it's a playlist
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
            
            is_playlist = info.get('_type') == 'playlist'
            
            if is_playlist:
                entries = list(info.get('entries', []))
                count = len(entries)
                title = info.get('title', 'Unknown Playlist')
                
                # Analyze the first video to get format options
                if count > 0:
                    first_video_url = entries[0]['url']
                    with yt_dlp.YoutubeDL({'quiet': True}) as ydl2:
                        first_video_info = ydl2.extract_info(first_video_url, download=False)
                    
                    formats = self._parse_formats(first_video_info)
                    thumbnail = first_video_info.get('thumbnail', '')
                else:
                    formats = []
                    thumbnail = ''
                    
                metadata = {
                    'title': title, # Playlist title
                    'thumbnail': thumbnail, # Thumbnail of first video
                    'duration': 0, # Total duration calculation is expensive
                    'webpage_url': url,
                    'formats': formats,
                    'is_playlist': True,
                    'playlist_count': count
                }
            else:
                # Single Video
                metadata = {
                    'title': info.get('title', 'Unknown Title'),
                    'thumbnail': info.get('thumbnail', ''),
                    'duration': info.get('duration', 0),
                    'webpage_url': info.get('webpage_url', url),
                    'formats': self._parse_formats(info),
                    'is_playlist': False
                }
            return metadata
        except Exception as e:
            return {'error': str(e)}

    def _parse_formats(self, info):
        """
        Parses raw format data into user-friendly options.
        """
        formats_list = []
        
        # Video Formats (Filter for mp4/best video)
        seen_resolutions = set()
        raw_formats = info.get('formats', [])
        
        # Sort by resolution (height) descending
        raw_formats.sort(key=lambda x: x.get('height') or 0, reverse=True)
        
        for f in raw_formats:
            height = f.get('height')
            if not height or height < 144: continue
            
            # Create a unique key for resolution
            res_key = f"{height}p"
            if res_key in seen_resolutions:
                continue
                
            seen_resolutions.add(res_key)
            
            formats_list.append({
                'id': f"video-{height}",
                'label': f"{height}p (MP4)",
                'type': 'video',
                'height': height
            })

        if not formats_list:
            # Fallback for Direct Links / Generic Files
            ext = info.get('ext', '').lower()
            is_audio = ext in ['mp3', 'wav', 'aac', 'flac', 'm4a', 'ogg', 'opus']
            
            type_label = "Audio" if is_audio else "Video"
            formats_list.append({
                'id': 'original',
                'label': f'Original {type_label} (Best Quality)',
                'type': 'original',
                'is_audio_only': is_audio
            })

            if not is_audio:
                 formats_list.append({'id': 'audio-mp3-320', 'label': 'Convert to MP3 (320kbps)', 'type': 'audio', 'abr': 320})
        
        elif len(formats_list) > 0:
            formats_list.append({'id': 'audio-mp3-320', 'label': 'MP3 High (320kbps)', 'type': 'audio', 'abr': 320})
            formats_list.append({'id': 'audio-mp3-192', 'label': 'MP3 Medium (192kbps)', 'type': 'audio', 'abr': 192})
            formats_list.append({'id': 'audio-mp3-128', 'label': 'MP3 Low (128kbps)', 'type': 'audio', 'abr': 128})
        
        return formats_list

class VideoDownloader:
    def __init__(self, callback=None):
        self.progress_callback = callback
        self.is_cancelled = False
        self.is_paused = False
        self.current_playlist_index = 0
        self.total_playlist_items = 0
        self.history_manager = HistoryManager()

    def cancel(self):
        self.is_cancelled = True
        
    def pause(self):
        self.is_paused = True # Effectively cancels current run but logs as paused

    def download_video(self, url, format_data, output_path="downloads", title_hint="Unknown"):
        """
        Downloads the video or playlist based on user selection.
        """
        self.is_cancelled = False
        self.is_paused = False
        
        if not os.path.exists(output_path):
            os.makedirs(output_path)
            
        # Log Start in History
        history_entry = self.history_manager.add_entry({
            'title': title_hint,
            'url': url,
            'format_label': format_data['label'],
            'status': 'Downloading',
            'output_path': output_path,
            'thumbnail': '' # Could be passed if we refactor to accept full metadata
        })
            
        ydl_opts = {
            'outtmpl': os.path.join(output_path, '%(playlist_index)s - %(title)s.%(ext)s') if 'playlist' in url or 'list=' in url else os.path.join(output_path, '%(title)s.%(ext)s'),
            'progress_hooks': [self._progress_hook],
            'quiet': True,
            'no_warnings': True,
            # Add User-Agent to try to evade 403 blocks
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        }

        if format_data['type'] == 'audio':
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': str(format_data['abr']),
                }],
            })
        elif format_data['type'] == 'original':
            pass 
        else:
            target_height = format_data['height']
            ydl_opts.update({
                'format': f'bestvideo[height<={target_height}]+bestaudio/best[height<={target_height}]/best',
                'merge_output_format': 'mp4',
            })

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            # If we reached here without exception, success
            self.history_manager.update_status(history_entry['id'], 'Finished')
            if self.progress_callback:
                self.progress_callback("All downloads finished!", 1.0)
            return True # <--- Return Success
                
        except Exception as e:
            if self.is_paused:
                 self.history_manager.update_status(history_entry['id'], 'Paused')
                 msg = "Download Paused."
            elif self.is_cancelled:
                 self.history_manager.update_status(history_entry['id'], 'Cancelled')
                 msg = "Download Cancelled."
            else:
                 self.history_manager.update_status(history_entry['id'], 'Error')
                 msg = f"Error: {str(e)}"

            if self.progress_callback:
                self.progress_callback(msg, 0.0)
            return False # <--- Return Failure

    def _progress_hook(self, d):
        # Check Cancellation Status
        if self.is_cancelled:
            raise Exception("Cancelled by user")
        if self.is_paused:
            raise Exception("Paused by user")

        if d['status'] == 'downloading':
            try:
                # 1. Calculate Percentage safely
                total = d.get('total_bytes') or d.get('total_bytes_estimate')
                downloaded = d.get('downloaded_bytes', 0)
                
                if total:
                    percent = downloaded / total
                else:
                    # Fallback to string parsing if total is unknown
                    p = d.get('_percent_str', '0%').replace('%','').strip()
                    percent = float(p) / 100

                # 2. Format Status Message
                # Speed
                speed = d.get('speed', 0)
                if speed:
                    speed_str = f"{speed/1024/1024:.1f} MB/s"
                else:
                    speed_str = d.get('_speed_str', 'N/A')
                
                # ETA
                eta = d.get('eta')
                if eta is not None:
                    eta_str = f"{int(eta)}s"
                else:
                    eta_str = d.get('_eta_str', 'N/A')
                
                # Playlist Info
                playlist_index = d.get('info_dict', {}).get('playlist_index')
                playlist_count = d.get('info_dict', {}).get('n_entries')
                
                prefix = ""
                if playlist_index and playlist_count:
                    prefix = f"[{playlist_index}/{playlist_count}] "

                status_msg = f"{prefix}Downloading: {percent*100:.1f}% | Speed: {speed_str} | ETA: {eta_str}"
                
                if self.progress_callback:
                    self.progress_callback(status_msg, percent)
            except Exception as e:
                pass
                
        elif d['status'] == 'finished':
            if self.progress_callback:
                self.progress_callback("Processing/Converting...", 0.99)
