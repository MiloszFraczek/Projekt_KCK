import customtkinter as ctk
import threading
import json
from db_mod import SessionRepository
from voice_mod import VoiceMod
from view.home_view import HomeView
from view.history_view import HistoryView

with open('config/main_config.json', 'r', encoding='utf-8') as file:
    config = json.load(file)

APP = config["app"]
COLORS = config["colors"]
FONTS = config["fonts"]
DIMENS = config["dimens"]
TEXTS = config["texts"]

ctk.set_appearance_mode(APP["appearance_mode"])
ctk.set_default_color_theme(APP["color_theme"])

class ModernApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(APP["title"])
        self.geometry(APP["geometry"])
        self.minsize(APP["min_width"], APP["min_height"])

        self.db = SessionRepository()
        self.voice = VoiceMod()

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.setup_sidebar()

        self.frames = {}
        self.frames["home"] = HomeView(self, self.db, self.voice, corner_radius=DIMENS["frame_corner_radius"], fg_color=COLORS["transparent"])
        self.frames["history"] = HistoryView(self, self.db, corner_radius=DIMENS["frame_corner_radius"], fg_color=COLORS["transparent"])

        self.show_frame("home")

    def setup_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=DIMENS["sidebar_width"], corner_radius=DIMENS["sidebar_corner_radius"])
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(4, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar, text=TEXTS["logo"], font=ctk.CTkFont(size=FONTS["logo_size"], weight=FONTS["logo_weight"]))
        self.logo_label.grid(row=0, column=0, padx=DIMENS["pad_x"], pady=tuple(DIMENS["pad_y_logo"]))

        self.btn_home = ctk.CTkButton(self.sidebar, text=TEXTS["btn_home"], command=lambda: self.show_frame("home"))
        self.btn_home.grid(row=1, column=0, padx=DIMENS["pad_x"], pady=DIMENS["pad_y_normal"])

        self.btn_history = ctk.CTkButton(self.sidebar, text=TEXTS["btn_history"], command=lambda: self.show_frame("history"))
        self.btn_history.grid(row=2, column=0, padx=DIMENS["pad_x"], pady=DIMENS["pad_y_normal"])

        self.voice_status = ctk.CTkLabel(self.sidebar, text=TEXTS["status_ready"], text_color=COLORS["status_ready"])
        self.voice_status.grid(row=5, column=0, padx=DIMENS["pad_x"], pady=DIMENS["pad_y_normal"])

        self.btn_voice = ctk.CTkButton(self.sidebar, text=TEXTS["voice_btn"], fg_color=COLORS["voice_btn_fg"],
                                       hover_color=COLORS["voice_btn_hover"], command=self.listen_for_command)
        self.btn_voice.grid(row=6, column=0, padx=DIMENS["pad_x"], pady=DIMENS["pad_y_large"])

    def show_frame(self, frame_name):
        for frame in self.frames.values():
            frame.grid_forget()
        self.frames[frame_name].grid(row=0, column=1, sticky="nsew")
        if frame_name == "history":
            self.frames["history"].refresh_history()

    def listen_for_command(self):
        self.voice_status.configure(text=TEXTS["status_listen"], text_color=COLORS["status_listen"])
        self.btn_voice.configure(state="disabled")

        def listener():
            voice_text = self.voice.get_voice()
            if voice_text and TEXTS["voice_trigger"] in voice_text.lower():
                self.after(0, self.frames["home"].start_training)
            self.after(0, lambda: self.voice_status.configure(text=TEXTS["status_ready"], text_color=COLORS["status_ready"]))
            self.after(0, lambda: self.btn_voice.configure(state="normal"))

        threading.Thread(target=listener, daemon=True).start()

if __name__ == "__main__":
    app = ModernApp()
    app.mainloop()