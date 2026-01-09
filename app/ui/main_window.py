import customtkinter as ctk
import threading
from PIL import Image
import requests
from io import BytesIO
from app.core.downloader import VideoAnalyzer, VideoDownloader
from app.ui.history_panel import HistoryPanel
from app.ui.theme import COLORS, FONTS

class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Any Video Downloader")
        self.geometry("900x700")
        self.configure(fg_color=COLORS["bg"])
        
        # Core Components
        self.analyzer = VideoAnalyzer()
        self.downloader = VideoDownloader(callback=self.update_progress)
        self.current_formats = []
        
        # UI Setup
        self._setup_layout()
        
        # History Panel (Hidden by default)
        self.history_panel = HistoryPanel(self, 
                                          resume_callback=self.resume_download_from_history,
                                          back_callback=self.show_downloader)
        # We don't pack/place it yet. We will swap it in when needed.

    def _setup_layout(self):
        # 1. Main Container (Centers content)
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(expand=True, fill="both", padx=40, pady=40)
        
        # 2. Header Section
        self.header_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.header_frame.pack(fill="x", pady=(0, 30))
        
        title = ctk.CTkLabel(self.header_frame, text="Any Video Downloader", font=FONTS["h1"], text_color=COLORS["text"])
        title.pack(anchor="center")

        history_btn = ctk.CTkButton(self.header_frame, text="History", width=80, height=28,
                                    fg_color=COLORS["input"], hover_color=COLORS["card"],
                                    font=FONTS["small"], command=self.open_history)
        history_btn.place(relx=0.95, rely=0.5, anchor="e")
        
        subtitle = ctk.CTkLabel(self.header_frame, text="Download videos and playlists from YouTube, Vimeo, and more.", 
                                font=FONTS["body"], text_color=COLORS["subtext"])
        subtitle.pack(anchor="center", pady=(5, 0))

        # 3. Input Section (Floating Search Bar look)
        self.input_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.input_frame.pack(fill="x", pady=(0, 20))
        
        # Use a frame to wrap entry+button for rounded pill look
        self.search_bar_frame = ctk.CTkFrame(self.input_frame, fg_color=COLORS["input"], corner_radius=25, height=50)
        self.search_bar_frame.pack(fill="x", padx=50) # Indent from sides
        self.search_bar_frame.pack_propagate(False) # Force height

        self.analyze_btn = ctk.CTkButton(self.search_bar_frame, text="Analyze", command=self.start_analysis, 
                                         font=FONTS["btn"], height=34, width=100, corner_radius=20,
                                         fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"])
        self.analyze_btn.pack(side="right", padx=8, pady=8)

        self.url_entry = ctk.CTkEntry(self.search_bar_frame, placeholder_text="Paste your video link here...", 
                                      font=FONTS["body"], border_width=0, fg_color="transparent", height=40)
        self.url_entry.pack(side="left", expand=True, fill="x", padx=(20, 10), pady=5)
        self.url_entry.bind("<Return>", lambda e: self.start_analysis())

        # 4. Status Indicator
        self.status_label = ctk.CTkLabel(self.main_container, text="Ready", font=FONTS["small"], text_color=COLORS["subtext"])
        self.status_label.pack(pady=(0, 20))

        # 5. Results Area (Card) - Initially Hidden or Empty
        self.results_card = ctk.CTkFrame(self.main_container, fg_color=COLORS["card"], corner_radius=15)
        # We don't pack it yet until we have results

    def start_analysis(self):
        url = self.url_entry.get()
        if not url.strip():
            self.status_label.configure(text="Please enter a valid URL.", text_color=COLORS["error"])
            return

        self.analyze_btn.configure(state="disabled", text="Working...")
        self.status_label.configure(text="Fetching video metadata...", text_color=COLORS["text"])
        self.url_entry.configure(state="disabled")
        
        threading.Thread(target=self._analyze_thread, args=(url,), daemon=True).start()

    def _analyze_thread(self, url):
        try:
            data = self.analyzer.extract_info(url)
            # Check if window still exists before scheduling update
            if self.winfo_exists():
                self.after(0, lambda: self._on_analysis_complete(data))
        except Exception as e:
            print(f"Thread Error: {e}")

    def _on_analysis_complete(self, data):
        try:
            self.analyze_btn.configure(state="normal", text="Analyze")
            self.url_entry.configure(state="normal")
            
            if 'error' in data:
                self.status_label.configure(text=f"Error: {data['error']}", text_color=COLORS["error"])
                self.results_card.pack_forget() # Hide card on error
                return

            self.status_label.configure(text="Metadata loaded successfully.", text_color=COLORS["success"])
            self._build_results_ui(data)
        except Exception:
            pass # Window likely destroyed

    def _build_results_ui(self, data):
        # Clear previous results
        for widget in self.results_card.winfo_children():
            widget.destroy()
            
        self.results_card.pack(fill="both", expand=True, padx=20, pady=10)
        
        # --- Left Col: Thumbnail ---
        # Using Grid inside the card for layout
        self.results_card.grid_columnconfigure(0, weight=0) # Image fixed
        self.results_card.grid_columnconfigure(1, weight=1) # Info expands
        self.results_card.grid_rowconfigure(0, weight=1)

        # 1. Thumbnail
        try:
            response = requests.get(data['thumbnail'])
            img_data = BytesIO(response.content)
            pil_img = Image.open(img_data)
            pil_img.thumbnail((360, 240)) # Slightly larger
            ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=pil_img.size)
            
            thumb_label = ctk.CTkLabel(self.results_card, image=ctk_img, text="")
            thumb_label.image = ctk_img
            thumb_label.grid(row=0, column=0, rowspan=4, padx=20, pady=20, sticky="n")
        except:
            thumb_label = ctk.CTkLabel(self.results_card, text="[No Image]", width=300, height=200, fg_color="black")
            thumb_label.grid(row=0, column=0, rowspan=4, padx=20, pady=20, sticky="n")

        # --- Right Col: Info ---
        
        # 2. Title
        title_text = data['title']
        if data.get('is_playlist'):
            count = data.get('playlist_count', 0)
            title_text = f"PLAYLIST • {count} Videos\n{data['title']}"
            
        title_label = ctk.CTkLabel(self.results_card, text=title_text, font=FONTS["h2"], 
                                   wraplength=350, justify="left", text_color=COLORS["text"])
        title_label.grid(row=0, column=1, padx=(0, 20), pady=(25, 5), sticky="nw")

        # 3. Meta (Duration / Provider)
        dur_val = data.get('duration', 0)
        dur_str = f"{dur_val//60}:{dur_val%60:02d}" if dur_val else "Unknown"
        if data.get('is_playlist'): dur_str = "Varies by video"
            
        meta_label = ctk.CTkLabel(self.results_card, text=f"Duration: {dur_str}  •  Source: {data.get('webpage_url', '').split('/')[2]}", 
                                  font=FONTS["small"], text_color=COLORS["subtext"])
        meta_label.grid(row=1, column=1, padx=(0, 20), pady=0, sticky="nw")

        # 4. Controls Frame (Format + Download)
        controls_frame = ctk.CTkFrame(self.results_card, fg_color="transparent")
        controls_frame.grid(row=2, column=1, padx=(0, 20), pady=20, sticky="ew")
        
        self.current_formats = data['formats']
        format_options = [f['label'] for f in self.current_formats]
        
        self.format_menu = ctk.CTkOptionMenu(controls_frame, values=format_options, width=180, 
                                             font=FONTS["body"], fg_color=COLORS["input"], button_color=COLORS["input"],
                                             button_hover_color=COLORS["card"], text_color=COLORS["text"])
        self.format_menu.pack(side="left", padx=(0, 10))
        if format_options: self.format_menu.set(format_options[0])

        self.download_btn = ctk.CTkButton(controls_frame, text="Download Now", command=self.start_download,
                                          font=FONTS["btn"], height=32, corner_radius=8,
                                          fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"])
        self.download_btn.pack(side="left", fill="x", expand=True)

        self.cancel_btn = ctk.CTkButton(controls_frame, text="Cancel", command=self.cancel_download,
                                        font=FONTS["btn"], height=32, corner_radius=8,
                                        fg_color=COLORS["error"], hover_color="#B00020")
        
        self.pause_btn = ctk.CTkButton(controls_frame, text="Pause", command=self.pause_download,
                                       font=FONTS["btn"], height=32, corner_radius=8,
                                       fg_color="#E0B0FF", hover_color="#D190E8", text_color="black")

        # 5. Progress Bar (Bottom of card)
        self.progress_bar = ctk.CTkProgressBar(self.results_card, height=12, corner_radius=0, 
                                               fg_color=COLORS["input"], progress_color=COLORS["accent"])
        self.progress_bar.set(0)
        self.progress_bar.grid(row=3, column=0, columnspan=2, sticky="ews") # Attach to bottom edge?
        # Actually proper rounded corners and bottom edge is tricky with grid. 
        # Let's put it inside the card with padding.
        self.progress_bar.grid(row=3, column=0, columnspan=2, padx=20, pady=(10, 20), sticky="ew")
        
        self.progress_text_label = ctk.CTkLabel(self.results_card, text="", font=FONTS["small"], text_color=COLORS["subtext"])
        self.progress_text_label.grid(row=4, column=0, columnspan=2, pady=(0, 15))


    def open_history(self):
        self.history_panel.load_history() # Refresh data
        
        # Swap Views
        self.main_container.pack_forget()
        self.history_panel.pack(fill="both", expand=True)
        
    def show_downloader(self):
        # Swap Views
        self.history_panel.pack_forget()
        self.main_container.pack(expand=True, fill="both", padx=40, pady=40)

    def resume_download_from_history(self, entry):
        self.show_downloader()
        # Restore UI state for a resume
        self.url_entry.delete(0, 'end')
        self.url_entry.insert(0, entry['url'])
        self.start_analysis() # Re-analyze

    def start_download(self):
        selected_label = self.format_menu.get()
        format_data = next((f for f in self.current_formats if f['label'] == selected_label), None)
        if not format_data: return

        # UI Toggle
        self.download_btn.pack_forget()
        self.cancel_btn.pack(side="right", padx=(5, 0), fill="x", expand=True)
        self.pause_btn.pack(side="right", padx=(5, 0), fill="x", expand=True)
        
        self.url_entry.configure(state="disabled")
        self.format_menu.configure(state="disabled")
        
        url = self.url_entry.get()
        # Pass title hint for history
        try:
            title_hint = self.results_card.winfo_children()[1].cget("text").split('\n')[-1] # Hacky: grab from label
        except:
            title_hint = "Unknown Video"

        threading.Thread(target=self._download_thread, args=(url, format_data, title_hint), daemon=True).start()

    def cancel_download(self):
        self.downloader.cancel()

    def pause_download(self):
        self.downloader.pause()

    def _download_thread(self, url, format_data, title_hint="Unknown"):
        try:
            self.downloader.download_video(url, format_data, title_hint=title_hint)
            if self.winfo_exists():
                self.after(0, self._on_download_complete)
        except Exception:
            pass

    def update_progress(self, status, percent):
        if self.winfo_exists():
            self.after(0, lambda: self._update_progress_ui(status, percent))

    def _update_progress_ui(self, status, percent):
        try:
            self.progress_bar.set(percent)
            self.progress_text_label.configure(text=status)
        except: pass

    def _on_download_complete(self):
        try:
            # Restore UI
            self.cancel_btn.pack_forget()
            self.pause_btn.pack_forget()
            self.download_btn.pack(side="left", fill="x", expand=True)
            self.download_btn.configure(state="normal", text="Download Again")
            
            self.url_entry.configure(state="normal")
            self.format_menu.configure(state="normal")
            
            # Reset Bar only if 100% or just leave it
            # self.progress_bar.set(0) 
        except: pass
