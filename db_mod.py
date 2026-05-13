import sqlite3
import datetime
import os
import matplotlib.pyplot as plt


DB_NAME = "cyber_trener.db"

#tworzenie bazy danych
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            reps_count INTEGER,
            mistakes_count INTEGER,
            video_path_front TEXT,
            video_path_side TEXT
        )
    ''')

    conn.commit()
    conn.close()

#zapis sesji do bazy danych
def save_session(reps, mistakes, path_front, path_side):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    date_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO sessions (date, reps_count, mistakes_count, video_path_front, video_path_side)
        VALUES (?, ?, ?, ?, ?)
    ''', (date_now, reps, mistakes, path_front, path_side))
    conn.commit()
    conn.close()
    print(f"Zapisano sesję: {date_now}")


#plik w foramacie png
def generate_progress_chart(output_filename="wykres_postepow.png"): #tworzenie wykresu postepow
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    #pobranie danych z bazy danych
    cursor.execute("SELECT date, reps_count, mistakes_count FROM sessions ORDER BY date ASC")
    rows = cursor.fetchall()
    conn.close()

if __name__ == "__main__":
    init_db() #test dzialania tworzenia i zapisu sesji