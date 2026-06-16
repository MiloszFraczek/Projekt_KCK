import customtkinter as ctk
from tkinter import messagebox
from PIL import Image
import cv2
import threading
import time
from db_mod import TrainingSession
from cam_mod import DeadliftScannerApp


class HomeView(ctk.CTkFrame):
    def __init__(self, master, db, voice, **kwargs):
        super().__init__(master, **kwargs)
        self.db = db
        self.voice = voice
        self.scanner = None
        self.scanner_thread = None

        self.is_training = False
        self.start_time = None
        self.timer_running = False

        self.build_ui()

    def build_ui(self):
        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.cam_container = ctk.CTkFrame(self)
        self.cam_container.grid(row=0, column=0, columnspan=2, padx=20, pady=20, sticky="nsew")
        self.cam_container.grid_columnconfigure((0, 1), weight=1, uniform="cam")
        self.cam_container.grid_rowconfigure(0, weight=1)

        self.cam_left = ctk.CTkLabel(self.cam_container, text="[ KAMERA 1 - PRZÓD ]", fg_color="#1a1a1a",
                                     corner_radius=10)
        self.cam_left.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.cam_right = ctk.CTkLabel(self.cam_container, text="[ KAMERA 2 - BOK ]", fg_color="#1a1a1a",
                                      corner_radius=10)
        self.cam_right.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        self.stats_container = ctk.CTkFrame(self, height=150)
        self.stats_container.grid(row=1, column=0, columnspan=2, padx=20, pady=(0, 20), sticky="ew")
        self.stats_container.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.lbl_reps = self._create_stat_card("POWTÓRZENIA", "0", "#2ecc71", 0)
        self.lbl_errs = self._create_stat_card("BŁĘDY", "0", "#e74c3c", 1)
        self.lbl_time = self._create_stat_card("CZAS SESJI", "00:00", "#3498db", 2)

        self.controls = ctk.CTkFrame(self.stats_container, fg_color="transparent")
        self.controls.grid(row=0, column=3, padx=20, pady=20, sticky="nsew")

        self.btn_start = ctk.CTkButton(self.controls, text="START TRENINGU", fg_color="#27ae60", hover_color="#2ecc71",
                                       font=("Arial", 14, "bold"), command=self.start_training)
        self.btn_start.pack(fill="x", pady=(0, 10))

        self.btn_stop = ctk.CTkButton(self.controls, text="ZAKOŃCZ I ZAPISZ", fg_color="#c0392b", hover_color="#e74c3c",
                                      font=("Arial", 14, "bold"), state="disabled", command=self.stop_training)
        self.btn_stop.pack(fill="x")

    def _create_stat_card(self, title, value, color, col):
        card = ctk.CTkFrame(self.stats_container)
        card.grid(row=0, column=col, padx=10, pady=20, sticky="nsew")
        ctk.CTkLabel(card, text=title, font=("Arial", 12)).pack(pady=(15, 5))
        val_label = ctk.CTkLabel(card, text=value, font=("Arial", 28, "bold"), text_color=color)
        val_label.pack(pady=(0, 15))
        return val_label