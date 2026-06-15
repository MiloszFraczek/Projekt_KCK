import sqlite3
from datetime import datetime
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
        self.reps_count = reps_count =1
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

    def get_daily_summary(self, exercise_type: str = "deadlift") -> List[Dict[str, Any]]:
        query = '''
            SELECT substr(date, 1, 10) as day, SUM(reps_count), SUM(mistakes_count)
            FROM sessions
            WHERE exercise_type = ?
            GROUP BY day
            ORDER BY day DES
        '''
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute(query, (exercise_type,))
                rows = cursor.fetchall()
            return [{"day": r[0], "reps": r[1], "mistakes": r[2]} for r in rows]
        except sqlite3.Error as e:
            print(f"[DB ERROR] Błąd podczas agregacji danych: {e}")
            return []




#plik w foramacie png
class ProgressVisualizer:
    @staticmethod
    def generate_chart(data: List[Dict[str, Any]], output_filename: str = "wykres_postepow.png") -> None:
        if not data:
            print("[Wizualizacja] Brak danych do wyświetlenia.")
            return

        dates = [item["day"] for item in data]
        reps = [item["reps"] for item in data]
        mistakes = [item["mistakes"] for item in data]

        plt.figure(figsize=(10, 6))
        plt.plot(dates, reps, marker='o', linestyle='-', color='green', label='Poprawne powtórzenia')
        plt.plot(dates, mistakes, marker='x', linestyle='--', color='red', label='Błędy')

        plt.title("Analiza Postępów Treningowych")
        plt.xlabel("Data")
        plt.ylabel("Suma powtórzeń / błędów")
        plt.legend()
        plt.xticks(rotation=45)
        plt.tight_layout()

        try:
            plt.savefig(output_filename)
            plt.close()
        except Exception as e:
            print(f"[VIS ERROR] Błąd zapisu wykresu: {e}")