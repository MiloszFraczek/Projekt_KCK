import unittest
from unittest.mock import patch
from cam_mod import DeadliftScannerApp


class TestDeadliftScanner(unittest.TestCase):

    def test_calculate_angle_90_degrees(self):
        #Przygotowanie danych: kąt prosty
        point_a = [0, 1]  # ramię
        point_b = [0, 0]  # łokieć
        point_c = [1, 0]  # nadgarstek

        #Wykonanie logiki
        angle = DeadliftScannerApp.calculate_angle(point_a, point_b, point_c)

        #Sprawdzenie wyniku
        self.assertAlmostEqual(angle, 90.0, places=1, msg="Kąt prosty powinien wynosić 90 stopni")

    def test_calculate_angle_180_degrees(self):
        #Przygotowanie danych: prosta linia
        point_a = [0, 1]
        point_b = [0, 0]
        point_c = [0, -1]

        angle = DeadliftScannerApp.calculate_angle(point_a, point_b, point_c)

        self.assertAlmostEqual(angle, 180.0, places=1, msg="Wyprostowana ręka powinna mieć 180 stopni")

    # --- TESTY ZARZĄDZANIA STANEM APLIKACJI ---

    # Używamy @patch, aby zablokować uruchamianie prawdziwych kamer i głosu
    @patch('cam_mod.BackgroundCameraStream')
    @patch('cam_mod.VoiceMod')
    def test_initial_app_state(self, MockVoice, MockCamera):
        app = DeadliftScannerApp()

        self.assertEqual(app.total_reps_counter, 0, "Licznik powtórzeń na start powinien wynosić 0")
        self.assertEqual(app.current_movement_state, "START", "Początkowy stan ruchu to START")
        self.assertFalse(app.is_coach_speaking, "Trener nie powinien mówić na starcie")

    @patch('cam_mod.BackgroundCameraStream')
    @patch('cam_mod.VoiceMod')
    def test_reset_coach_memory_when_not_speaking(self, MockVoice, MockCamera):
        app = DeadliftScannerApp()
        app.last_critical_error = "hips_too_low"
        app.is_coach_speaking = False

        app.reset_coach_memory()

        self.assertIsNone(app.last_critical_error, "Pamięć błędów powinna zostać wyczyszczona")

    @patch('cam_mod.BackgroundCameraStream')
    @patch('cam_mod.VoiceMod')
    def test_do_not_reset_memory_when_speaking(self, MockVoice, MockCamera):
        app = DeadliftScannerApp()
        app.last_critical_error = "straight_back"
        app.is_coach_speaking = True  # Symulujemy, że trener właśnie mówi

        app.reset_coach_memory()

        self.assertEqual(app.last_critical_error, "straight_back",
                         "Błąd nie powinien być czyszczony w trakcie mówienia")


if __name__ == '__main__':
    unittest.main()