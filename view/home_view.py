import customtkinter as ctk
from tkinter import messagebox
from PIL import Image
import cv2
import threading
import time
import json
from db_mod import TrainingSession
from cam_mod import DeadliftScannerApp

with open('./config/home_config.json', 'r', encoding='utf-8') as file:
    config = json.load(file)

TEXTS = config["texts"]
COLORS = config["colors"]
DIMENS = config["dimens"]
FONTS = {key: tuple(value) for key, value in config["fonts"].items()}

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

        self.cam_left = ctk.CTkLabel(self.cam_container, text=TEXTS["cam_left"], fg_color=COLORS["cam_bg"],
                                     corner_radius=DIMENS["cam_corner_radius"])
        self.cam_left.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        self.cam_right = ctk.CTkLabel(self.cam_container, text=TEXTS["cam_right"], fg_color=COLORS["cam_bg"],
                                      corner_radius=DIMENS["cam_corner_radius"])
        self.cam_right.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        self.stats_container = ctk.CTkFrame(self, height=DIMENS["stats_height"])
        self.stats_container.grid(row=1, column=0, columnspan=2, padx=20, pady=(0, 20), sticky="ew")
        self.stats_container.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.lbl_reps = self._create_stat_card(TEXTS["stat_reps"], TEXTS["val_zero"], COLORS["success"], 0)
        self.lbl_errs = self._create_stat_card(TEXTS["stat_errs"], TEXTS["val_zero"], COLORS["danger"], 1)
        self.lbl_time = self._create_stat_card(TEXTS["stat_time"], TEXTS["val_time_zero"], COLORS["info"], 2)

        self.controls = ctk.CTkFrame(self.stats_container, fg_color=COLORS["transparent"])
        self.controls.grid(row=0, column=3, padx=20, pady=20, sticky="nsew")

        self.btn_start = ctk.CTkButton(self.controls, text=TEXTS["btn_start"], fg_color=COLORS["btn_start"], hover_color=COLORS["btn_start_hover"],
                                       font=FONTS["btn"], command=self.start_training)
        self.btn_start.pack(fill="x", pady=(0, 10))

        self.btn_stop = ctk.CTkButton(self.controls, text=TEXTS["btn_stop"], fg_color=COLORS["btn_stop"], hover_color=COLORS["btn_stop_hover"],
                                      font=FONTS["btn"], state="disabled", command=self.stop_training)
        self.btn_stop.pack(fill="x")

    def _create_stat_card(self, title, value, color, col):
        card = ctk.CTkFrame(self.stats_container)
        card.grid(row=0, column=col, padx=10, pady=20, sticky="nsew")
        ctk.CTkLabel(card, text=title, font=FONTS["stat_title"]).pack(pady=(15, 5))
        val_label = ctk.CTkLabel(card, text=value, font=FONTS["stat_val"], text_color=color)
        val_label.pack(pady=(0, 15))
        return val_label

    def start_training(self):
        if self.is_training: return

        self.is_training = True
        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="normal")

        self.scanner = DeadliftScannerApp()
        self.scanner_thread = threading.Thread(target=self.scanner.run, daemon=True)
        self.scanner_thread.start()

        self.start_time = time.time()
        self.timer_running = True
        self.update_timer()

        self.update_video_feed()

        try:
            self.voice.speak(TEXTS["voice_start"])
        except Exception:
            pass

    def stop_training(self):
        self.is_training = False
        self.timer_running = False
        self.btn_start.configure(state="normal")
        self.btn_stop.configure(state="disabled")

        if self.scanner:
            reps = self.scanner.total_reps_counter
            mistakes = len(self.scanner.last_warning_times)

            self.scanner.stop()
            self.scanner = None

            self.cam_left.configure(image="", text=TEXTS["cam_left"])
            self.cam_right.configure(image="", text=TEXTS["cam_right"])

            if reps > 0:
                prompt_msg = TEXTS["msg_reps"].format(reps=reps)
            else:
                prompt_msg = TEXTS["msg_no_reps"]

            if messagebox.askyesno(TEXTS["msg_title"], prompt_msg):
                session = TrainingSession(reps_count=reps, mistakes_count=mistakes, video_path_front=TEXTS["db_na"],
                                          video_path_side=TEXTS["db_na"])
                self.db.save(session)
                try:
                    self.voice.speak(TEXTS["voice_saved"])
                except Exception:
                    pass
            else:
                try:
                    self.voice.speak(TEXTS["voice_canceled"])
                except Exception:
                    pass

        self.lbl_reps.configure(text=TEXTS["val_zero"])
        self.lbl_errs.configure(text=TEXTS["val_zero"])
        self.lbl_time.configure(text=TEXTS["val_time_zero"])

    def update_timer(self):
        if self.timer_running:
            elapsed = int(time.time() - self.start_time)
            mins, secs = divmod(elapsed, 60)
            self.lbl_time.configure(text=f"{mins:02d}:{secs:02d}")
            self.after(1000, self.update_timer)

    def update_video_feed(self):
        if self.is_training and self.scanner:
            container_w = self.cam_container.winfo_width()
            container_h = self.cam_container.winfo_height()

            cam_w = max((container_w // 2) - DIMENS["cam_margin"], DIMENS["cam_min_size"])
            cam_h = max(container_h - DIMENS["cam_margin"], DIMENS["cam_min_size"])

            if hasattr(self.scanner, 'current_front_processed') and self.scanner.current_front_processed is not None:
                img_f = cv2.cvtColor(self.scanner.current_front_processed, cv2.COLOR_BGR2RGB)
                pil_f = Image.fromarray(img_f)
                ctk_img_f = ctk.CTkImage(light_image=pil_f, dark_image=pil_f, size=(cam_w, cam_h))
                self.cam_left.configure(image=ctk_img_f, text="")
                self.cam_left.image = ctk_img_f

            if hasattr(self.scanner, 'current_side_processed') and self.scanner.current_side_processed is not None:
                img_s = cv2.cvtColor(self.scanner.current_side_processed, cv2.COLOR_BGR2RGB)
                pil_s = Image.fromarray(img_s)
                ctk_img_s = ctk.CTkImage(light_image=pil_s, dark_image=pil_s, size=(cam_w, cam_h))
                self.cam_right.configure(image=ctk_img_s, text="")
                self.cam_right.image = ctk_img_s

            self.lbl_reps.configure(text=str(self.scanner.total_reps_counter))

            if hasattr(self.scanner, 'last_warning_times'):
                self.lbl_errs.configure(text=str(len(self.scanner.last_warning_times)))

            self.after(DIMENS["feed_delay_ms"], self.update_video_feed)