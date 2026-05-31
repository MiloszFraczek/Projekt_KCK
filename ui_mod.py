import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import Calendar
from datetime import datetime
import time


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
        self.pages = {}
        self.pages["home"] = self.HOME()
        self.pages["calendar"] = self.CALENDAR()
        self.pages["history"] = self.HISTORY()
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

    # STRONA GŁÓWNA
    def HOME(self):
        page = tk.Frame(self.container, bg=self.colors["bg"])

        header = tk.Frame(page, bg=self.colors["white"], height=50)
        header.pack(fill="x", padx=20, pady=10)
        tk.Label(header, text="PANEL TRENINGU LIVE", font=("Helvetica", 14, "bold"), bg=self.colors["white"],
                 fg=self.colors["primary"]).pack(side="left", padx=15)
        main_content = tk.Frame(page, bg=self.colors["bg"])
        main_content.pack(fill="both", expand=True, padx=20)

        self.cam_frame = tk.Frame(main_content, bg="black", bd=2)
        self.cam_frame.pack(side="left", fill="both", expand=True, pady=(0, 20))
        self.cam_canvas = tk.Canvas(self.cam_frame, bg="#1a1a1a", highlightthickness=0)
        self.cam_canvas.pack(fill="both", expand=True)
        self.cam_canvas.create_text(300, 250, text="[ KAMERA GOTOWA ]", fill="#444", font=("Arial", 14, "bold"))

        sidebar = tk.Frame(main_content, width=280, bg=self.colors["white"], padx=20)
        sidebar.pack(side="right", fill="y", padx=(20, 0), pady=(0, 20))
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="WYNIKI SESJI", font=("Arial", 11, "bold"), bg=self.colors["white"]).pack(pady=20)
        self.stat_reps = self.DATA(sidebar, "POWTÓRZENIA", "0", self.colors["success"])
        self.stat_errors = self.DATA(sidebar, "BŁĘDY", "0", self.colors["danger"])
        self.stat_timer = self.DATA(sidebar, "CZAS SESJI", "00:00", self.colors["accent"])

        tk.Button(sidebar, text="START TRENINGU", bg=self.colors["success"], fg="white", font=("Arial", 10, "bold"),
                  height=2, bd=0, command=self.START).pack(fill="x", pady=(30, 5))
        tk.Button(sidebar, text="ZAKOŃCZ I ZAPISZ", bg=self.colors["danger"], fg="white", font=("Arial", 10, "bold"),
                  height=2, bd=0, command=self.STOP).pack(fill="x", pady=5)
        return page

    # KARTY ZE STATYSTYKAMI
    def DATA(self, parent, label, value, color):
        card = tk.Frame(parent, bg="#f8f9fa", bd=1, relief="solid")
        card.pack(fill="x", pady=5)
        tk.Label(card, text=label, bg="#f8f9fa", font=("Arial", 8)).pack(pady=(5, 0))
        val_lbl = tk.Label(card, text=value, bg="#f8f9fa", font=("Arial", 16, "bold"), fg=color)
        val_lbl.pack(pady=(0, 5))
        return val_lbl

    # KALENDARZ
    def CALENDAR(self):
        page = tk.Frame(self.container, bg=self.colors["bg"])
        content = tk.Frame(page, bg=self.colors["white"], padx=30, pady=30)
        content.pack(pady=40, padx=40, fill="both", expand=True)
        # TYTUŁ STRONY KALENDARZA
        tk.Label(content, text="HISTORIA TWOICH TRENINGÓW", font=("Helvetica", 16, "bold"),
                 bg=self.colors["white"]).pack(pady=(0, 20))
        self.cal = Calendar(content, selectmode='day', background=self.colors["primary"], foreground='white',
                            headersbackground=self.colors["accent"])
        self.cal.pack(fill="both", expand=True)
        # PRZYCISK SZCZEGÓŁY DNIA
        btn_check = tk.Button(content, text="POKAŻ SZCZEGÓŁY DNIA", bg=self.colors["primary"], fg="white", pady=10,
                              command=self.DAYS)
        btn_check.pack(fill="x", pady=20)
        return page

    # SEKCJA HISTORII
    def HISTORY(self):
        page = tk.Frame(self.container, bg=self.colors["bg"])
        content = tk.Frame(page, bg=self.colors["white"], padx=30, pady=30)
        content.pack(pady=20, padx=20, fill="both", expand=True)

        tk.Label(content, text="ZESTAWIENIE TRENINGÓW", font=("Helvetica", 16, "bold"),
                 bg=self.colors["white"], fg=self.colors["primary"]).pack(pady=(0, 20))

        columns = ("data", "powt", "bledy", "czas")
        self.tree = ttk.Treeview(content, columns=columns, show="headings")

        self.tree.heading("data", text="Data")
        self.tree.heading("powt", text="Powtórzenia")
        self.tree.heading("bledy", text="Błędy")
        self.tree.heading("czas", text="Czas trwania")

        self.tree.column("data", anchor="center", width=150)
        self.tree.column("powt", anchor="center", width=100)
        self.tree.column("bledy", anchor="center", width=100)
        self.tree.column("czas", anchor="center", width=100)

        scrollbar = ttk.Scrollbar(content, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        return page

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
        messagebox.showinfo("Start programu", "Uruchamianie kamery.")
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

        self.stat_timer.config(text="00:00")  # Reset zegara po decyzji

    # SZCZEGÓŁY WYBRANEGO DNIA
    def DAYS(self):
        selected_date = self.cal.get_date()
        messagebox.showinfo("Historia", f"Dnia {selected_date} wykonałeś: \n- 45 powtórzeń\n- 3 błędy")


# START
if __name__ == "__main__":
    app = AppGUI()
    app.mainloop()