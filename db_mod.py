import sqlite3
import datetime
import os
import matplotlib.pyplot as plt
from typing import List, Dict, Any, Optional


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