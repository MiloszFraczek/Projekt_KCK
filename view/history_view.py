import customtkinter as ctk
import calendar
from datetime import datetime
from utils.charts import render_daily_chart, render_monthly_chart

MIESIACE = ["", "Styczeń", "Luty", "Marzec", "Kwiecień", "Maj", "Czerwiec",
            "Lipiec", "Sierpień", "Wrzesień", "Październik", "Listopad", "Grudzień"]
DNI_TYGODNIA = ["Pon", "Wto", "Śro", "Czw", "Pią", "Sob", "Nie"]

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

        self.cal_header = ctk.CTkFrame(self.calendar_container, fg_color="transparent")
        self.cal_header.pack(fill="x", pady=10, padx=20)

        self.btn_prev_month = ctk.CTkButton(self.cal_header, text="<", width=40, font=("Arial", 16, "bold"),
                                            command=lambda: self.change_month(-1))
        self.btn_prev_month.pack(side="left")

        self.lbl_month_year = ctk.CTkLabel(self.cal_header, text="Miesiąc Rok", font=("Arial", 18, "bold"))
        self.lbl_month_year.pack(side="left", expand=True)

        self.btn_next_month = ctk.CTkButton(self.cal_header, text=">", width=40, font=("Arial", 16, "bold"),
                                            command=lambda: self.change_month(1))
        self.btn_next_month.pack(side="right")

        self.cal_days_header = ctk.CTkFrame(self.calendar_container, fg_color="transparent")
        self.cal_days_header.pack(fill="x", padx=20)
        for i, day in enumerate(DNI_TYGODNIA):
            self.cal_days_header.grid_columnconfigure(i, weight=1)
            ctk.CTkLabel(self.cal_days_header, text=day, text_color="gray").grid(row=0, column=i, pady=5)

        self.cal_grid = ctk.CTkFrame(self.calendar_container, fg_color="transparent")
        self.cal_grid.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        for i in range(7):
            self.cal_grid.grid_columnconfigure(i, weight=1)
        for i in range(6):
            self.cal_grid.grid_rowconfigure(i, weight=1)

        self.details_container = ctk.CTkFrame(self, fg_color="transparent")
        self.details_container.grid(row=0, column=1, padx=(10, 20), pady=20, sticky="nsew")

        self.detail_card = ctk.CTkFrame(self.details_container, height=0, corner_radius=15, fg_color="#1f538d")
        self.detail_card.pack_propagate(False)
        self.detail_card.pack(fill="x", pady=(0, 20), padx=10)

        self.lbl_detail_date = ctk.CTkLabel(self.detail_card, text="Wybierz trening", font=("Arial", 18, "bold"),
                                            text_color="white")
        self.lbl_detail_date.pack(pady=(20, 10))

        self.lbl_detail_reps = ctk.CTkLabel(self.detail_card, text="Powtórzenia: --", font=("Arial", 16),
                                            text_color="#2ecc71")
        self.lbl_detail_reps.pack(pady=5)

        self.lbl_detail_errs = ctk.CTkLabel(self.detail_card, text="Błędy: --", font=("Arial", 16),
                                            text_color="#e74c3c")
        self.lbl_detail_errs.pack(pady=5)

        self.btn_monthly_chart = ctk.CTkButton(
            self.details_container,
            text="📊 Wykres całego miesiąca",
            font=("Arial", 14, "bold"),
            command=self.draw_monthly_chart,
            fg_color="#8e44ad", hover_color="#9b59b6"
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

        for row_idx, week in enumerate(cal):
            for col_idx, day in enumerate(week):
                if day != 0:
                    date_str = f"{self.cal_year}-{self.cal_month:02d}-{day:02d}"
                    has_training = date_str in self.training_data

                    bg_color = "#2ecc71" if has_training else (
                        "#3498db" if date_str == datetime.now().strftime("%Y-%m-%d") else "transparent")
                    text_color = "white" if has_training or date_str == datetime.now().strftime("%Y-%m-%d") else "gray"
                    hover = "#27ae60" if has_training else "#2b2b2b"

                    btn_day = ctk.CTkButton(
                        self.cal_grid,
                        text=str(day),
                        width=40, height=40,
                        corner_radius=20,
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
            ctk.CTkLabel(self.chart_container, text="Brak danych dla tego dnia. Wybierz zielony punkt na kalendarzu.",
                         font=("Arial", 14)).pack(fill="both", expand=True, pady=10)
            return

        data = self.training_data[date_str]

        self.lbl_detail_date.configure(text=f"Trening: {date_str}")
        self.lbl_detail_reps.configure(text=f"Poprawne powtórzenia: {data['reps']}")
        self.lbl_detail_errs.configure(text=f"Zarejestrowane błędy: {data['mistakes']}")
        self.animate_details_card()

        render_daily_chart(self.chart_container, date_str, data['reps'], data['mistakes'])

    def animate_details_card(self):
        if self.detail_animation_running: return
        self.detail_animation_running = True

        def expand(current_height, target_height):
            if current_height < target_height:
                new_h = current_height + 15
                self.detail_card.configure(height=new_h)
                self.after(15, lambda: expand(new_h, target_height))
            else:
                self.detail_card.configure(height=target_height)
                self.detail_animation_running = False

        expand(self.detail_card.winfo_height(), 150)

    def hide_details_card(self):
        self.detail_card.configure(height=0)

    def draw_monthly_chart(self):
        render_monthly_chart(self.chart_container, self.training_data, self.cal_year, self.cal_month)

    def refresh_history(self):
        self.fetch_training_data()
        self.render_calendar()
        self.hide_details_card()
        self.draw_monthly_chart()