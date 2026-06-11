import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import Calendar
from datetime import datetime
import time


# KLASA STRONY GŁÓWNEJ (TRENING LIVE)
class HomeFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=controller.colors["bg"])
        self.controller = controller

        header = tk.Frame(self, bg=controller.colors["white"], height=50)
        header.pack(fill="x", padx=20, pady=10)
        tk.Label(header, text="PANEL TRENINGU LIVE", font=("Helvetica", 14, "bold"), bg=controller.colors["white"],
                 fg=controller.colors["primary"]).pack(side="left", padx=15)
        main_content = tk.Frame(self, bg=controller.colors["bg"])
        main_content.pack(fill="both", expand=True, padx=20)

        controller.cam_frame = tk.Frame(main_content, bg="black", bd=2)
        controller.cam_frame.pack(side="left", fill="both", expand=True, pady=(0, 20))

        # Lewy ekran kamery
        controller.cam_canvas_left = tk.Canvas(controller.cam_frame, bg="#1a1a1a", highlightthickness=0)
        controller.cam_canvas_left.pack(side="left", fill="both", expand=True, padx=(0, 2))
        controller.cam_canvas_left.create_text(150, 250, text="[ KAMERA 1 ]", fill="#444", font=("Arial", 14, "bold"))

        # Prawy ekran kamery
        controller.cam_canvas_right = tk.Canvas(controller.cam_frame, bg="#1a1a1a", highlightthickness=0)
        controller.cam_canvas_right.pack(side="right", fill="both", expand=True, padx=(2, 0))
        controller.cam_canvas_right.create_text(150, 250, text="[ KAMERA 2 ]", fill="#444", font=("Arial", 14, "bold"))

        sidebar = tk.Frame(main_content, width=280, bg=controller.colors["white"], padx=20)
        sidebar.pack(side="right", fill="y", padx=(20, 0), pady=(0, 20))
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="WYNIKI SESJI", font=("Arial", 11, "bold"), bg=controller.colors["white"]).pack(pady=20)
        controller.stat_reps = controller.DATA(sidebar, "POWTÓRZENIA", "0", controller.colors["success"])
        controller.stat_errors = controller.DATA(sidebar, "BŁĘDY", "0", controller.colors["danger"])
        controller.stat_timer = controller.DATA(sidebar, "CZAS SESJI", "00:00", controller.colors["accent"])

        tk.Button(sidebar, text="START TRENINGU", bg=controller.colors["success"], fg="white",
                  font=("Arial", 10, "bold"),
                  height=2, bd=0, command=controller.START).pack(fill="x", pady=(30, 5))
        tk.Button(sidebar, text="ZAKOŃCZ I ZAPISZ", bg=controller.colors["danger"], fg="white",
                  font=("Arial", 10, "bold"),
                  height=2, bd=0, command=controller.STOP).pack(fill="x", pady=5)


# KLASA KALENDARZA
class CalendarFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=controller.colors["bg"])
        self.controller = controller

        content = tk.Frame(self, bg=controller.colors["white"], padx=30, pady=30)
        content.pack(pady=40, padx=40, fill="both", expand=True)
        # TYTUŁ STRONY KALENDARZA
        tk.Label(content, text="HISTORIA TWOICH TRENINGÓW", font=("Helvetica", 16, "bold"),
                 bg=controller.colors["white"]).pack(pady=(0, 20))
        controller.cal = Calendar(content, selectmode='day', background=controller.colors["primary"],
                                  foreground='white',
                                  headersbackground=controller.colors["accent"])
        controller.cal.pack(fill="both", expand=True)
        # PRZYCISK SZCZEGÓŁY DNIA
        btn_check = tk.Button(content, text="POKAŻ SZCZEGÓŁY DNIA", bg=controller.colors["primary"], fg="white",
                              pady=10,
                              command=controller.DAYS)
        btn_check.pack(fill="x", pady=20)


# KLASA SEKCJI HISTORII
class HistoryFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=controller.colors["bg"])
        self.controller = controller

        content = tk.Frame(self, bg=controller.colors["white"], padx=30, pady=30)
        content.pack(pady=20, padx=20, fill="both", expand=True)

        tk.Label(content, text="ZESTAWIENIE TRENINGÓW", font=("Helvetica", 16, "bold"),
                 bg=controller.colors["white"], fg=controller.colors["primary"]).pack(pady=(0, 20))

        columns = ("data", "powt", "bledy", "czas")
        controller.tree = ttk.Treeview(content, columns=columns, show="headings")

        controller.tree.heading("data", text="Data")
        controller.tree.heading("powt", text="Powtórzenia")
        controller.tree.heading("bledy", text="Błędy")
        controller.tree.heading("czas", text="Czas trwania")

        controller.tree.column("data", anchor="center", width=150)
        controller.tree.column("powt", anchor="center", width=100)
        controller.tree.column("bledy", anchor="center", width=100)
        controller.tree.column("czas", anchor="center", width=100)

        scrollbar = ttk.Scrollbar(content, orient="vertical", command=controller.tree.yview)
        controller.tree.configure(yscrollcommand=scrollbar.set)

        controller.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")


# GŁÓWNA KLASA ZARZĄDZAJĄCA APLIKACJĄ
class AppGUI(tk.Tk):
    def __init__(self):
        super().__init__()

        # GŁÓWNE OKNO
        self.title("Wirtualny Trener")
        self.geometry("1000x750")
        self.configure(bg="#f0f2f5")
        self.colors = {"primary": "#2c3e50", "accent": "#3498db", "success": "#2ecc71", "danger": "#e74c3c",
                       "bg": "#f0f2f5", "white": "#ffffff"}

        # ZMIENNE DLA TIMERA
        self.start_time = None
        self.timer_running = False

        # PASEK NAWIGACJI
        self.nav_bar = tk.Frame(self, bg=self.colors["primary"], height=60)
        self.nav_bar.pack(side="top", fill="x")
        self.BUTTONS("TRENING", "home")
        self.BUTTONS("KALENDARZ", "calendar")
        self.BUTTONS("HISTORIA", "history")

        self.container = tk.Frame(self, bg=self.colors["bg"])
        self.container.pack(fill="both", expand=True)

        # INICJALIZACJA STRON JAKO OBIEKTÓW OSOBNYCH KLAS
        self.pages = {}
        self.pages["home"] = HomeFrame(self.container, self)
        self.pages["calendar"] = CalendarFrame(self.container, self)
        self.pages["history"] = HistoryFrame(self.container, self)
        self.SHOW("home")

    # PRZYCISKI MENU
    def BUTTONS(self, text, page_id):
        btn = tk.Button(self.nav_bar, text=text, bg=self.colors["primary"], fg="white", font=("Helvetica", 10, "bold"),
                        bd=0, padx=20, cursor="hand2", activebackground=self.colors["accent"],
                        command=lambda: self.SHOW(page_id))
        btn.pack(side="left", fill="y")

    # PRZEŁĄCZANIE STRON
    def SHOW(self, page_id):
        for page in self.pages.values():
            page.pack_forget()
        self.pages[page_id].pack(fill="both", expand=True)

    # KARTY ZE STATYSTYKAMI
    def DATA(self, parent, label, value, color):
        card = tk.Frame(parent, bg="#f8f9fa", bd=1, relief="solid")
        card.pack(fill="x", pady=5)
        tk.Label(card, text=label, bg="#f8f9fa", font=("Arial", 8)).pack(pady=(5, 0))
        val_lbl = tk.Label(card, text=value, bg="#f8f9fa", font=("Arial", 16, "bold"), fg=color)
        val_lbl.pack(pady=(0, 5))
        return val_lbl

    # FUNKCJA AKTUALIZACJI TIMERA
    def TIMER(self):
        if self.timer_running:
            elapsed_time = int(time.time() - self.start_time)
            minutes = elapsed_time // 60
            seconds = elapsed_time % 60
            self.stat_timer.config(text=f"{minutes:02d}:{seconds:02d}")
            self.after(1000, self.TIMER)

    # FUNKCJA STARTU TRENINGU
    def START(self):
        messagebox.showinfo("Start programu", "Uruchamianie kamer.")
        self.stat_reps.config(text="2")
        # Inicjalizacja timera
        self.start_time = time.time()
        self.timer_running = True
        self.TIMER()

    # ZAKOŃCZENIE TRENINGU
    def STOP(self):
        self.timer_running = False  # Zatrzymanie odliczania
        reps = self.stat_reps.cget("text")
        errs = self.stat_errors.cget("text")
        duration = self.stat_timer.cget("text")

        answer = messagebox.askyesno("Koniec", "Czy chcesz zapisać wyniki tego treningu?")
        if answer:
            # Dodanie do tabeli w zakładce HISTORIA
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            self.tree.insert("", 0, values=(timestamp, reps, errs, duration))
            print("Zapisano do bazy danych.")

        self.stat_timer.config(text="00:00")

    # SZCZEGÓŁY WYBRANEGO DNIA
    def DAYS(self):
        selected_date = self.cal.get_date()
        messagebox.showinfo("Historia", f"Dnia {selected_date} wykonałeś: \n- 45 powtórzeń\n- 3 błędy")


# START
if __name__ == "__main__":
    app = AppGUI()
    app.mainloop()