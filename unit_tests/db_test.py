import unittest
import os
import tempfile
import sqlite3
from datetime import datetime

from db_mod import TrainingSession, SessionRepository, ProgressVisualizer

class TestTrainingSession(unittest.TestCase):
    def test_session_initialization(self):
        """Testuje, czy obiekt poprawnie przypisuje wartości podczas inicjalizacji."""
        session = TrainingSession(
            reps_count=10,
            mistakes_count=2,
            video_path_front="front.mp4",
            video_path_side="side.mp4"
        )

        self.assertEqual(session.reps_count, 10)
        self.assertEqual(session.mistakes_count, 2)
        self.assertEqual(session.video_path_front, "front.mp4")
        self.assertEqual(session.exercise_type, "deadlift")
        self.assertIsInstance(datetime.strptime(session.date, "%Y-%m-%d %H:%M:%S"), datetime)


class TestSessionRepository(unittest.TestCase):
    def setUp(self):
        """Uruchamia się przed każdym testem. Tworzy tymczasową bazę danych."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()  # Zamykamy uchwyt, żeby SQLite mogło go otworzyć
        self.repo = SessionRepository(db_name=self.temp_db.name)

    def tearDown(self):
        """Uruchamia się po każdym teście. Sprząta tymczasową bazę."""
        os.remove(self.temp_db.name)

    def test_database_initialization(self):
        """Sprawdza, czy tabela 'sessions' została poprawnie utworzona."""
        with sqlite3.connect(self.temp_db.name) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sessions'")
            table_exists = cursor.fetchone()
            self.assertIsNotNone(table_exists)

    def test_save_session(self):
        """Sprawdza zapis sesji i przypisanie ID."""
        session = TrainingSession(10, 1, "f.mp4", "s.mp4")
        result = self.repo.save(session)

        self.assertTrue(result)
        self.assertIsNotNone(session.id)

        with sqlite3.connect(self.temp_db.name) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT reps_count, mistakes_count FROM sessions WHERE id = ?", (session.id,))
            row = cursor.fetchone()
            self.assertEqual(row, (10, 1))

    def test_get_daily_summary(self):
        """Sprawdza, czy agregacja danych z konkretnego dnia działa poprawnie."""
        session1 = TrainingSession(10, 2, "f1.mp4", "s1.mp4", date_str="2023-10-01 10:00:00")
        session2 = TrainingSession(15, 3, "f2.mp4", "s2.mp4", date_str="2023-10-01 18:00:00")
        session3 = TrainingSession(20, 0, "f3.mp4", "s3.mp4", date_str="2023-10-02 09:00:00")
        self.repo.save(session1)
        self.repo.save(session2)
        self.repo.save(session3)
        summary = self.repo.get_daily_summary()
        self.assertEqual(len(summary), 2)

        self.assertEqual(summary[0]["day"], "2023-10-01")
        self.assertEqual(summary[0]["reps"], 25)
        self.assertEqual(summary[0]["mistakes"], 5)

        self.assertEqual(summary[1]["day"], "2023-10-02")
        self.assertEqual(summary[1]["reps"], 20)
        self.assertEqual(summary[1]["mistakes"], 0)


class TestProgressVisualizer(unittest.TestCase):
    def setUp(self):
        """Przygotowanie ścieżki dla tymczasowego pliku wykresu."""
        self.test_img_path = "test_wykres.png"

    def tearDown(self):
        """Usunięcie pliku po teście, jeśli został stworzony."""
        if os.path.exists(self.test_img_path):
            os.remove(self.test_img_path)

    def test_generate_chart_with_data(self):
        """Testuje czy wykres jest fizycznie generowany i zapisywany na dysku."""
        test_data = [
            {"day": "2023-10-01", "reps": 25, "mistakes": 5},
            {"day": "2023-10-02", "reps": 20, "mistakes": 2}
        ]

        ProgressVisualizer.generate_chart(test_data, output_filename=self.test_img_path)
        self.assertTrue(os.path.exists(self.test_img_path))
        self.assertGreater(os.path.getsize(self.test_img_path), 0)

    def test_generate_chart_empty_data(self):
        """Testuje zachowanie, gdy przekazana jest pusta lista danych."""
        ProgressVisualizer.generate_chart([], output_filename=self.test_img_path)
        self.assertFalse(os.path.exists(self.test_img_path))

if __name__ == "__main__":
    unittest.main(verbosity=2)