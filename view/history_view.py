import customtkinter as ctk
import calendar
import json
from datetime import datetime
from utils.charts import render_daily_chart, render_monthly_chart

with open('./config/history_config.json', 'r', encoding='utf-8') as file:
    config = json.load(file)

TEXTS = config["texts"]
COLORS = config["colors"]
DIMENS = config["dimens"]
FONTS = {key: tuple(value) for key, value in config["fonts"].items()}

MIESIACE = TEXTS["months"]
DNI_TYGODNIA = TEXTS["days"]

class HistoryView(ctk.CTkFrame):
    def __init__(self, master, db, **kwargs):
        super().__init__(master, **kwargs)
        self.db = db
        now = datetime.now()
        self.cal_year = now.year
        self.cal_month = now.month
        self.training_data = {}
        self.detail_animation_running = False

        self.build_ui()

    def build_ui(self):
        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.calendar_container = ctk.CTkFrame(self)
        self.calendar_container.grid(row=0, column=0, padx=(20, 10), pady=20, sticky="nsew")

        self.cal_header = ctk.CTkFrame(self.calendar_container, fg_color=COLORS["transparent"])
        self.cal_header.pack(fill="x", pady=10, padx=20)

        self.btn_prev_month = ctk.CTkButton(self.cal_header, text=TEXTS["btn_prev"], width=DIMENS["btn_arrow_width"], font=FONTS["btn_arrow"],
                                            command=lambda: self.change_month(-1))
        self.btn_prev_month.pack(side="left")

        self.lbl_month_year = ctk.CTkLabel(self.cal_header, text=TEXTS["month_year_placeholder"], font=FONTS["header"])
        self.lbl_month_year.pack(side="left", expand=True)

        self.btn_next_month = ctk.CTkButton(self.cal_header, text=TEXTS["btn_next"], width=DIMENS["btn_arrow_width"], font=FONTS["btn_arrow"],
                                            command=lambda: self.change_month(1))
        self.btn_next_month.pack(side="right")

        self.cal_days_header = ctk.CTkFrame(self.calendar_container, fg_color=COLORS["transparent"])
        self.cal_days_header.pack(fill="x", padx=20)
        for i, day in enumerate(DNI_TYGODNIA):
            self.cal_days_header.grid_columnconfigure(i, weight=1)
            ctk.CTkLabel(self.cal_days_header, text=day, text_color=COLORS["text_gray"]).grid(row=0, column=i, pady=5)

        self.cal_grid = ctk.CTkFrame(self.calendar_container, fg_color=COLORS["transparent"])
        self.cal_grid.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        for i in range(7):
            self.cal_grid.grid_columnconfigure(i, weight=1)
        for i in range(6):
            self.cal_grid.grid_rowconfigure(i, weight=1)

        self.details_container = ctk.CTkFrame(self, fg_color=COLORS["transparent"])
        self.details_container.grid(row=0, column=1, padx=(10, 20), pady=20, sticky="nsew")

        self.detail_card = ctk.CTkFrame(self.details_container, height=0, corner_radius=DIMENS["card_corner_radius"], fg_color=COLORS["card_bg"])
        self.detail_card.pack_propagate(False)
        self.detail_card.pack(fill="x", pady=(0, 20), padx=10)

        self.lbl_detail_date = ctk.CTkLabel(self.detail_card, text=TEXTS["detail_default"], font=FONTS["header"],
                                            text_color=COLORS["text_white"])
        self.lbl_detail_date.pack(pady=(20, 10))

        self.lbl_detail_reps = ctk.CTkLabel(self.detail_card, text=TEXTS["reps_default"], font=FONTS["detail_text"],
                                            text_color=COLORS["success"])
        self.lbl_detail_reps.pack(pady=5)

        self.lbl_detail_errs = ctk.CTkLabel(self.detail_card, text=TEXTS["errs_default"], font=FONTS["detail_text"],
                                            text_color=COLORS["danger"])
        self.lbl_detail_errs.pack(pady=5)

        self.btn_monthly_chart = ctk.CTkButton(
            self.details_container,
            text=TEXTS["btn_monthly_chart"],
            font=FONTS["btn_chart"],
            command=self.draw_monthly_chart,
            fg_color=COLORS["btn_chart"], hover_color=COLORS["btn_chart_hover"]
        )
        self.btn_monthly_chart.pack(side="bottom", pady=20, fill="x", padx=10)

        self.chart_container = ctk.CTkFrame(self)
        self.chart_container.grid(row=1, column=0, columnspan=2, padx=20, pady=(0, 20), sticky="nsew")

    def fetch_training_data(self):
        raw_data = self.db.get_daily_summary()
        self.training_data = {}
        for row in raw_data:
            self.training_data[row["day"]] = {"reps": row["reps"], "mistakes": row["mistakes"]}

    def change_month(self, delta):
        self.cal_month += delta
        if self.cal_month > 12:
            self.cal_month = 1
            self.cal_year += 1
        elif self.cal_month < 1:
            self.cal_month = 12
            self.cal_year -= 1

        self.hide_details_card()
        self.render_calendar()
        self.draw_monthly_chart()

    def render_calendar(self):
        self.lbl_month_year.configure(text=f"{MIESIACE[self.cal_month]} {self.cal_year}")

        for widget in self.cal_grid.winfo_children():
            widget.destroy()

        cal = calendar.monthcalendar(self.cal_year, self.cal_month)
        today_str = datetime.now().strftime("%Y-%m-%d")

        for row_idx, week in enumerate(cal):
            for col_idx, day in enumerate(week):
                if day != 0:
                    date_str = f"{self.cal_year}-{self.cal_month:02d}-{day:02d}"
                    has_training = date_str in self.training_data
                    is_today = (date_str == today_str)

                    bg_color = COLORS["success"] if has_training else (COLORS["today_bg"] if is_today else COLORS["transparent"])
                    text_color = COLORS["text_white"] if has_training or is_today else COLORS["text_gray"]
                    hover = COLORS["success_hover"] if has_training else COLORS["day_hover"]

                    btn_day = ctk.CTkButton(
                        self.cal_grid,
                        text=str(day),
                        width=DIMENS["day_btn_size"], height=DIMENS["day_btn_size"],
                        corner_radius=DIMENS["day_corner_radius"],
                        fg_color=bg_color,
                        hover_color=hover,
                        text_color=text_color,
                        command=lambda d=date_str, ht=has_training: self.on_day_click(d, ht)
                    )
                    btn_day.grid(row=row_idx, column=col_idx, padx=5, pady=5)

    def on_day_click(self, date_str, has_training):
        if not has_training:
            self.hide_details_card()
            for widget in self.chart_container.winfo_children():
                widget.destroy()
            ctk.CTkLabel(self.chart_container, text=TEXTS["no_data"], font=FONTS["info_text"]).pack(fill="both", expand=True, pady=10)
            return

        data = self.training_data[date_str]

        self.lbl_detail_date.configure(text=f"{TEXTS['training_prefix']}{date_str}")
        self.lbl_detail_reps.configure(text=f"{TEXTS['reps_prefix']}{data['reps']}")
        self.lbl_detail_errs.configure(text=f"{TEXTS['errs_prefix']}{data['mistakes']}")
        self.animate_details_card()

        render_daily_chart(self.chart_container, date_str, data['reps'], data['mistakes'])

    def animate_details_card(self):
        if self.detail_animation_running: return
        self.detail_animation_running = True

        def expand(current_height, target_height):
            if current_height < target_height:
                new_h = current_height + DIMENS["anim_step"]
                self.detail_card.configure(height=new_h)
                self.after(DIMENS["anim_speed_ms"], lambda: expand(new_h, target_height))
            else:
                self.detail_card.configure(height=target_height)
                self.detail_animation_running = False

        expand(self.detail_card.winfo_height(), DIMENS["anim_max_height"])

    def hide_details_card(self):
        self.detail_card.configure(height=0)

    def draw_monthly_chart(self):
        render_monthly_chart(self.chart_container, self.training_data, self.cal_year, self.cal_month)

    def refresh_history(self):
        self.fetch_training_data()
        self.render_calendar()
        self.hide_details_card()
        self.draw_monthly_chart()