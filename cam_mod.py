import cv2
import numpy as np
import threading
import time
import ssl
import mediapipe as mp

ssl._create_default_https_context = ssl._create_unverified_context

mp_rysuj = mp.solutions.drawing_utils
mp_poza = mp.solutions.pose

IP_KAMERY_PRZOD = "http://10.239.195.177:5001/video"
KAMERA_BOK_USB = 0

SZEROKOSC = 960
WYSOKOSC = 720


class StrumienWideo:
    def __init__(self, zrodlo=0, szer=960, wys=720):
        # Wymuszenie DirectShow dla wirtualnych kamer (Iriun)
        if isinstance(zrodlo, int):
            self.strumien = cv2.VideoCapture(zrodlo, cv2.CAP_DSHOW)
        else:
            self.strumien = cv2.VideoCapture(zrodlo)

        self.strumien.set(cv2.CAP_PROP_FRAME_WIDTH, szer)
        self.strumien.set(cv2.CAP_PROP_FRAME_HEIGHT, wys)
        self.pobrano, self.klatka = self.strumien.read()
        self.zatrzymany = False

    def start(self):
        threading.Thread(target=self.aktualizuj, args=(), daemon=True).start()
        return self

    def aktualizuj(self):
        while not self.zatrzymany:
            if not self.pobrano:
                self.stop()
            else:
                self.pobrano, self.klatka = self.strumien.read()

    def czytaj(self):
        return self.klatka

    def stop(self):
        self.zatrzymany = True
        self.strumien.release()


def oblicz_kat(a, b, c):
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)
    radiany = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
    kat = np.abs(radiany * 180.0 / np.pi)
    return 360 - kat if kat > 180.0 else kat


print("Łączenie z kamerami...")
kamera_przod = StrumienWideo(IP_KAMERY_PRZOD, SZEROKOSC, WYSOKOSC).start()
kamera_bok = StrumienWideo(KAMERA_BOK_USB, SZEROKOSC, WYSOKOSC).start()

licznik_powtorzen = 0
stan_ruchu = "GORA"

styl_punktow = mp_rysuj.DrawingSpec(color=(0, 255, 0), thickness=4, circle_radius=3)
styl_linii = mp_rysuj.DrawingSpec(color=(255, 255, 255), thickness=2)

# Zmniejszona pewność AI do 50% i model_complexity=1 (szybszy i łatwiej łapie szkielet z boku)
with mp_poza.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5, model_complexity=1) as poza_przod, \
        mp_poza.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5, model_complexity=1) as poza_bok:
    print("System gotowy! Wciśnij 'q' na podglądzie, aby wyjść.")

    while True:
        klatka_przod = kamera_przod.czytaj()
        klatka_bok = kamera_bok.czytaj()

        # Wykrywacz problemów - żeby okienko nie wieszało się bez sensu
        if klatka_przod is None or klatka_bok is None:
            stan_p = "OK" if klatka_przod is not None else "BRAK"
            stan_b = "OK" if klatka_bok is not None else "BRAK"
            print(f"Czekam na kamery... Przod (Mac): {stan_p} | Bok (Telefon): {stan_b}")
            time.sleep(1)
            continue

        klatka_przod = cv2.resize(klatka_przod, (SZEROKOSC, WYSOKOSC))
        klatka_bok = cv2.resize(klatka_bok, (SZEROKOSC, WYSOKOSC))

        obraz_przod_rgb = cv2.cvtColor(klatka_przod, cv2.COLOR_BGR2RGB)
        obraz_bok_rgb = cv2.cvtColor(klatka_bok, cv2.COLOR_BGR2RGB)

        wyniki_przod = poza_przod.process(obraz_przod_rgb)
        wyniki_bok = poza_bok.process(obraz_bok_rgb)

        # Rysowanie na kamerze z przodu (tylko wizualnie)
        if wyniki_przod.pose_landmarks:
            mp_rysuj.draw_landmarks(klatka_przod, wyniki_przod.pose_landmarks, mp_poza.POSE_CONNECTIONS, styl_punktow,
                                    styl_linii)

        # Rysowanie i liczenie na kamerze z boku
        if wyniki_bok.pose_landmarks:
            mp_rysuj.draw_landmarks(klatka_bok, wyniki_bok.pose_landmarks, mp_poza.POSE_CONNECTIONS, styl_punktow,
                                    styl_linii)
            punkty = wyniki_bok.pose_landmarks.landmark

            bark = [punkty[mp_poza.PoseLandmark.LEFT_SHOULDER.value].x,
                    punkty[mp_poza.PoseLandmark.LEFT_SHOULDER.value].y]
            biodro = [punkty[mp_poza.PoseLandmark.LEFT_HIP.value].x, punkty[mp_poza.PoseLandmark.LEFT_HIP.value].y]
            kolano = [punkty[mp_poza.PoseLandmark.LEFT_KNEE.value].x, punkty[mp_poza.PoseLandmark.LEFT_KNEE.value].y]
            kostka = [punkty[mp_poza.PoseLandmark.LEFT_ANKLE.value].x, punkty[mp_poza.PoseLandmark.LEFT_ANKLE.value].y]

            kat_biodra = oblicz_kat(bark, biodro, kolano)
            kat_kolana = oblicz_kat(biodro, kolano, kostka)

            # Zejście do pozycji martwego ciągu
            if kat_biodra < 110 and kat_kolana < 120:
                stan_ruchu = "DOL"

            # Powrót do stania
            if kat_biodra > 165 and kat_kolana > 165:
                if stan_ruchu == "DOL":
                    licznik_powtorzen += 1
                    stan_ruchu = "GORA"

        # Interfejs
        cv2.putText(klatka_przod, f"WYNIK: {licznik_powtorzen}", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0),
                    4)
        cv2.putText(klatka_bok, f"STAN: {stan_ruchu}", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 0), 4)

        # Łączenie dwóch widoków
        polaczony_ekran = np.hstack((klatka_przod, klatka_bok))
        cv2.imshow('Skaner Deadlift - Wersja Stabilna', polaczony_ekran)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

kamera_przod.stop()
kamera_bok.stop()
cv2.destroyAllWindows()