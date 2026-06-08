import sqlite3
import datetime
import os
import matplotlib.pyplot as plt
from typing import List, Dict, Any, Optional




class TrainingSession:
    def __init__(self, reps_count: int, mistakes_count: int,
                 video_path_front: str, video_path_side: str,
                 exercise_type: str = "deadlift",
                 session_id: Optional[int] = None,
                 date_str: Optional[str] = None):
        self.id = session_id
        self.exercise_type = exercise_type
        self.date = date_str or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.reps_count = reps_count
        self.mistakes_count = mistakes_count
        self.video_path_front = video_path_front
        self.video_path_side = video_path_side


#tworzenie bazy danych
class SessionRepository:
    def __init__(self, db_name: str = "cyber_trener.db"):
        self.db_name = db_name
        self._init_db()

    def _init_db(self) -> None:
        query = '''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                exercise_type TEXT,
                date TEXT,
                reps_count INTEGER,
                mistakes_count INTEGER,
                video_path_front TEXT,
                video_path_side TEXT
            )
        '''
        try:
            with sqlite3.connect(self.db_name) as conn:
                conn.execute(query)
        except sqlite3.Error as e:
            print(f"[DB ERROR] Błąd podczas tworzenia tabeli: {e}")

    # zapis sesji do bazy danych
    def save(self, session: TrainingSession) -> bool:
        query = '''
            INSERT INTO sessions (exercise_type, date, reps_count, mistakes_count, video_path_front, video_path_side)
            VALUES (?, ?, ?, ?, ?, ?)
        '''
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute(query, (
                    session.exercise_type, session.date, session.reps_count,
                    session.mistakes_count, session.video_path_front, session.video_path_side
                ))
                session.id = cursor.lastrowid
            return True
        except sqlite3.Error as e:
            print(f"[DB ERROR] Nie udało się zapisać obiektu sesji: {e}")
            return False




#plik w foramacie png
def generate_progress_chart(output_filename="wykres_postepow.png"): #tworzenie wykresu postepow
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    #pobranie danych z bazy danych
    cursor.execute("SELECT date, reps_count, mistakes_count FROM sessions ORDER BY date ASC")
    rows = cursor.fetchall()
    conn.close()

    #zabezpiecznie przed brakiem danych
    if not rows:
        print("Brak danych w bazie. Wykonaj najpierw trening!")
        return

    dates = [row[0][:10] for row in rows]
    reps = [row[1] for row in rows]
    mistakes = [row[2] for row in rows]

    #tworzenie wykresu
    plt.figure(figsize=(10,6))

    plt.plot(dates, reps, marker='o', linestyle='-', color='green', label='Poprawne powtorzenia')
    plt.plot(dates, mistakes, marker='x', linestyle='--', color='red', label='Bledy')

    #zapisanie wykresu
    plt.savefig(output_filename)
    plt.close()

    print(f"Wygenerowano i zapisano wykres:{output_filename}")

if __name__ == "__main__":
    init_db() #test dzialania tworzenia i zapisu sesji
    generate_progress_chart()  #test funkcji