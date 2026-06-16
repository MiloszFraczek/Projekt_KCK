import numpy as np
from scipy.interpolate import make_interp_spline
import matplotlib
import customtkinter as ctk

matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.ticker as ticker

MIESIACE = ["", "Styczeń", "Luty", "Marzec", "Kwiecień", "Maj", "Czerwiec",
            "Lipiec", "Sierpień", "Wrzesień", "Październik", "Listopad", "Grudzień"]


def render_daily_chart(container, date_str, reps, mistakes):
    for widget in container.winfo_children():
        widget.destroy()

    bg_color = "#2b2b2b"
    fig = Figure(figsize=(8, 3.5), dpi=100, facecolor=bg_color)
    ax = fig.add_subplot(111)
    ax.set_facecolor(bg_color)

    labels = ['Poprawne powtórzenia', 'Zarejestrowane błędy']
    values = [reps, mistakes]
    colors = ['#00f2fe', '#fe0979']

    bars = ax.bar(labels, values, color=colors, width=0.4)

    ax.tick_params(colors='white', labelsize=12)
    for spine in ax.spines.values():
        spine.set_visible(False)

    ax.grid(axis='y', color='white', alpha=0.1, linestyle='--')
    ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))

    max_val = max(values) if max(values) > 0 else 1
    for bar in bars:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width() / 2, yval + (0.05 * max_val), int(yval),
                ha='center', va='bottom', color='white', fontsize=14, fontweight='bold')

    fig.tight_layout()
    canvas = FigureCanvasTkAgg(fig, master=container)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=10)


def render_monthly_chart(container, training_data, year, month):
    # Używamy zmiennej 'container', a nie 'self.chart_container'
    for widget in container.winfo_children():
        widget.destroy()

    prefix = f"{year}-{month:02d}"
    month_dates = sorted([d for d in training_data.keys() if d.startswith(prefix)])

    if not month_dates:
        ctk.CTkLabel(container,
                     text=f"Brak treningów w {MIESIACE[month].lower()} {year}.",
                     font=("Arial", 14)).pack(fill="both", expand=True, pady=10)
        return
    reps = np.array([training_data[d]['reps'] for d in month_dates])
    mistakes = np.array([training_data[d]['mistakes'] for d in month_dates])
    days_numeric = np.array([int(d[-2:]) for d in month_dates])

    bg_color = "#2b2b2b"
    fig = Figure(figsize=(8, 3.5), dpi=100, facecolor=bg_color)
    ax = fig.add_subplot(111)
    ax.set_facecolor(bg_color)

    color_reps = '#00f2fe'
    color_errs = '#fe0979'

    if len(days_numeric) >= 3:
        x_smooth = np.linspace(days_numeric.min(), days_numeric.max(), 300)
        spline_reps = make_interp_spline(days_numeric, reps, k=2 if len(days_numeric) == 3 else 3)
        spline_errs = make_interp_spline(days_numeric, mistakes, k=2 if len(days_numeric) == 3 else 3)

        y_reps_smooth = np.clip(spline_reps(x_smooth), 0, None)
        y_errs_smooth = np.clip(spline_errs(x_smooth), 0, None)
    else:
        x_smooth = days_numeric
        y_reps_smooth = reps
        y_errs_smooth = mistakes

    ax.fill_between(x_smooth, y_reps_smooth, color=color_reps, alpha=0.3, zorder=1)
    ax.fill_between(x_smooth, y_errs_smooth, color=color_errs, alpha=0.2, zorder=1)

    ax.plot(x_smooth, y_reps_smooth, color=color_reps, linewidth=3, zorder=2, label='Poprawne powtórzenia')
    ax.plot(x_smooth, y_errs_smooth, color=color_errs, linewidth=3, zorder=2, label='Zarejestrowane błędy')

    ax.scatter(days_numeric, reps, color=color_reps, edgecolor='white', linewidth=2, s=60, zorder=3)
    ax.scatter(days_numeric, mistakes, color=color_errs, edgecolor='white', linewidth=2, s=60, zorder=3)

    for d, r, m in zip(days_numeric, reps, mistakes):
        ax.text(d, r + 0.3, str(r), color='white', fontsize=9, ha='center', va='bottom', weight='bold')
        if m > 0:
            ax.text(d, m + 0.3, str(m), color='white', fontsize=9, ha='center', va='bottom', weight='bold')

    ax.tick_params(colors='white', labelsize=10)
    for spine in ax.spines.values():
        spine.set_visible(False)

    ax.grid(axis='y', color='white', alpha=0.1, linestyle='--')

    ax.set_ylabel("Suma", color='gray', fontsize=10)
    ax.set_xlabel(f"Dzień ({MIESIACE[month]})", color='gray', fontsize=10)
    ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
    ax.set_xticks(days_numeric)

    ax.legend(facecolor='#1a1a1a', edgecolor='#2b2b2b', labelcolor='white', loc='upper left')
    fig.tight_layout()

    canvas = FigureCanvasTkAgg(fig, master=container)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=10)