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
        pass

    def fetch_training_data(self):
        raw_data = self.db.get_daily_summary()
        self.training_data = {}
        for row in raw_data:
            self.training_data[row["day"]] = {"reps": row["reps"], "mistakes": row["mistakes"]}

    def on_day_click(self, date_str, has_training):
        if has_training:
            data = self.training_data[date_str]
            render_daily_chart(self.chart_container, date_str, data['reps'], data['mistakes'])