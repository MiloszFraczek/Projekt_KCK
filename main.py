import customtkinter as ctk
import threading
from db_mod import SessionRepository
from voice_mod import VoiceMod
from views.home_view import HomeView
from views.history_view import HistoryView

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class ModernApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Cyber Trener PRO")
        self.geometry("1100x800")
        self.minsize(950, 700)

        self.db = SessionRepository()
        self.voice = VoiceMod()

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.setup_sidebar()

        self.frames = {}
        self.frames["home"] = HomeView(self, self.db, self.voice, corner_radius=10, fg_color="transparent")
        self.frames["history"] = HistoryView(self, self.db, corner_radius=10, fg_color="transparent")

        self.show_frame("home")

    def setup_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(4, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar, text="CYBER TRENER", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 30))

        self.btn_home = ctk.CTkButton(self.sidebar, text="Trening Live", command=lambda: self.show_frame("home"))
        self.btn_home.grid(row=1, column=0, padx=20, pady=10)

        self.btn_history = ctk.CTkButton(self.sidebar, text="Historia i Wykresy",
                                         command=lambda: self.show_frame("history"))
        self.btn_history.grid(row=2, column=0, padx=20, pady=10)

        self.voice_status = ctk.CTkLabel(self.sidebar, text="Asystent: Gotowy", text_color="gray")
        self.voice_status.grid(row=5, column=0, padx=20, pady=10)

        self.btn_voice = ctk.CTkButton(self.sidebar, text="🎤 Nasłuchuj komendy", fg_color="#8e44ad",
                                       hover_color="#9b59b6", command=self.listen_for_command)
        self.btn_voice.grid(row=6, column=0, padx=20, pady=20)

    def show_frame(self, frame_name):
        for frame in self.frames.values():
            frame.grid_forget()
        self.frames[frame_name].grid(row=0, column=1, sticky="nsew")
        if frame_name == "history":
            self.frames["history"].refresh_history()

    def listen_for_command(self):
        self.voice_status.configure(text="Asystent: Słucham...", text_color="#f1c40f")
        self.btn_voice.configure(state="disabled")

        def listener():
            voice_text = self.voice.get_voice()
            if voice_text and "rozpocznij trening" in voice_text.lower():
                self.after(0, self.frames["home"].start_training)
            self.after(0, lambda: self.voice_status.configure(text="Asystent: Gotowy", text_color="gray"))
            self.after(0, lambda: self.btn_voice.configure(state="normal"))

        threading.Thread(target=listener, daemon=True).start()

if __name__ == "__main__":
    app = ModernApp()
    app.mainloop()