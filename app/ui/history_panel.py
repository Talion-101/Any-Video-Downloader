import customtkinter as ctk
from app.ui.theme import COLORS, FONTS
from app.core.history import HistoryManager

class HistoryPanel(ctk.CTkFrame):
    def __init__(self, parent, resume_callback=None, back_callback=None):
        super().__init__(parent, fg_color=COLORS["bg"])
        
        self.resume_callback = resume_callback
        self.back_callback = back_callback
        self.history_manager = HistoryManager()
        
        self._setup_ui()
        self.load_history()

    def _setup_ui(self):
        # Header
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.pack(fill="x", padx=20, pady=20)
        
        # Back Button
        if self.back_callback:
            back_btn = ctk.CTkButton(self.header, text="← Back", width=60, height=28,
                                     fg_color=COLORS["input"], hover_color=COLORS["card"],
                                     font=FONTS["small"], command=self.back_callback)
            back_btn.pack(side="left", padx=(0, 10))

        title = ctk.CTkLabel(self.header, text="History", font=FONTS["h2"], text_color=COLORS["text"])
        title.pack(side="left")
        
        refresh_btn = ctk.CTkButton(self.header, text="Refresh", width=80, height=30,
                                    fg_color=COLORS["input"], hover_color=COLORS["card"],
                                    command=self.load_history)
        refresh_btn.pack(side="right")

        # Scrollable List
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

    def load_history(self):
        # Clear existing
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()
            
        history = self.history_manager.get_history()
        
        if not history:
            lbl = ctk.CTkLabel(self.scroll_frame, text="No history yet.", text_color=COLORS["subtext"])
            lbl.pack(pady=20)
            return

        for entry in history:
            self._create_history_item(entry)

    def _create_history_item(self, entry):
        card = ctk.CTkFrame(self.scroll_frame, fg_color=COLORS["card"], corner_radius=10)
        card.pack(fill="x", pady=5)
        
        # Info
        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True, padx=15, pady=10)
        
        title_lbl = ctk.CTkLabel(info_frame, text=entry['title'], font=("Inter", 14, "bold"), 
                                 text_color=COLORS["text"], anchor="w")
        title_lbl.pack(fill="x")
        
        meta_text = f"{entry['date']} • {entry['format_label']}"
        meta_lbl = ctk.CTkLabel(info_frame, text=meta_text, font=FONTS["small"], 
                                text_color=COLORS["subtext"], anchor="w")
        meta_lbl.pack(fill="x")

        # Status & Action
        action_frame = ctk.CTkFrame(card, fg_color="transparent")
        action_frame.pack(side="right", padx=15, pady=10)
        
        status = entry['status']
        status_color = COLORS["text"]
        if status == 'Finished': status_color = COLORS["success"]
        elif status == 'Error': status_color = COLORS["error"]
        elif status == 'Cancelled': status_color = COLORS["error"]
        elif status == 'Paused': status_color = "#E0B0FF"
        
        status_lbl = ctk.CTkLabel(action_frame, text=status, font=("Inter", 12, "bold"), text_color=status_color)
        status_lbl.pack(side="top", anchor="e", pady=(0, 5))
        
        if status in ['Cancelled', 'Paused', 'Error']:
            resume_btn = ctk.CTkButton(action_frame, text="Resume", width=70, height=24,
                                       fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
                                       font=("Inter", 11),
                                       command=lambda e=entry: self.on_resume(e))
            resume_btn.pack(side="bottom", anchor="e")

    def on_resume(self, entry):
        if self.resume_callback:
            self.resume_callback(entry)
