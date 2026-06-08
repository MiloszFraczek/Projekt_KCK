# importowanie narzędzi
import cv2
import numpy as np
import threading
import time
import ssl
import mediapipe as mp

# IMPORT TWOJEGO MODUŁU GŁOSOWEGO
from voice_mod import VoiceMod

ssl._create_default_https_context = ssl._create_unverified_context

mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

# ustawienia kamer
INDEKS_FRONT = 0
INDEKS_BOK = 1

TARGET_WIDTH = 960
TARGET_HEIGHT = 720


# klasa do pobierania wideo
class RTSPVideoStream:
    def __init__(self, src=0, width=960, height=720):
        self.stream = cv2.VideoCapture(src)
        self.stream.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.stream.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.grabbed, self.frame = self.stream.read()
        self.stopped = False

    def start(self):
        threading.Thread(target=self.update, args=(), daemon=True).start()
        return self

    def update(self):
        while not self.stopped:
            try:
                if not self.grabbed:
                    self.stop()
                else:
                    self.grabbed, self.frame = self.stream.read()
            except Exception:
                self.stopped = True
                break

    def read(self):
        return self.frame

    def stop(self):
        self.stopped = True
        self.stream.release()


# funkcja do obliczania kątów
def calculate_angle(a, b, c):
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)
    radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - np.arctan2(a[1] - b[1], a[0] - b[0])
    angle = np.abs(radians * 180.0 / np.pi)
    return 360 - angle if angle > 180.0 else angle


# start programu
cam_front = RTSPVideoStream(src=INDEKS_FRONT, width=TARGET_WIDTH, height=TARGET_HEIGHT).start()
cam_side = RTSPVideoStream(src=INDEKS_BOK, width=TARGET_WIDTH, height=TARGET_HEIGHT).start()

# inicjalizacja trenera głosowego
trener = VoiceMod()

rep_counter = 0
deadlift_state = "START"
rep_min_score = 100
last_rep_status = ""
last_rep_color = (255, 255, 255)

with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5, model_complexity=1) as pose_front, \
        mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5, model_complexity=1) as pose_side:
    while True:
        frame_f = cam_front.read()
        frame_s = cam_side.read()

        if frame_f is None or frame_s is None:
            stan_p = "ok" if frame_f is not None else "brak"
            stan_b = "ok" if frame_s is not None else "brak"
            print(f"czekam na kamery... przod: {stan_p} | bok: {stan_b}")
            time.sleep(1)
            continue

        frame_f = cv2.resize(frame_f, (TARGET_WIDTH, TARGET_HEIGHT))
        frame_s = cv2.resize(frame_s, (TARGET_WIDTH, TARGET_HEIGHT))

        img_f = cv2.cvtColor(frame_f, cv2.COLOR_BGR2RGB)
        img_s = cv2.cvtColor(frame_s, cv2.COLOR_BGR2RGB)

        results_f = pose_front.process(img_f)
        results_s = pose_side.process(img_s)

        errors_front = []
        errors_side = []
        krytyczny_blad_glosowy = None
        current_score = 100

        # 1. analiza przód
        if results_f.pose_landmarks:
            landmarks = results_f.pose_landmarks.landmark

            l_shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y,
                          landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x]
            r_shoulder = [landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y,
                          landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x]
            l_knee_x = landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x
            r_knee_x = landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].x
            l_hip_x = landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x
            r_hip_x = landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].x

            if abs(l_shoulder[0] - r_shoulder[0]) > 0.04:
                errors_front.append("ASYMETRIA BARKOW! (-10%)")
                current_score -= 10
                krytyczny_blad_glosowy = "delts_asymetry"

            knee_dist = abs(l_knee_x - r_knee_x)
            hip_dist = abs(l_hip_x - r_hip_x)
            if knee_dist < hip_dist * 0.85:
                errors_front.append("KOLANA DO SRODKA! (-15%)")
                current_score -= 15
                krytyczny_blad_glosowy = "legs_width"

            skel_color_f = (0, 255, 0) if current_score >= 80 else (0, 0, 255)
            mp_drawing.draw_landmarks(
                frame_f, results_f.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=mp_drawing.DrawingSpec(color=skel_color_f, thickness=6, circle_radius=5),
                connection_drawing_spec=mp_drawing.DrawingSpec(color=(255, 255, 255), thickness=3)
            )

        # 2. analiza bok
        if results_s.pose_landmarks:
            landmarks_s = results_s.pose_landmarks.landmark

            shoulder = [landmarks_s[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,
                        landmarks_s[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
            hip = [landmarks_s[mp_pose.PoseLandmark.LEFT_HIP.value].x,
                   landmarks_s[mp_pose.PoseLandmark.LEFT_HIP.value].y]
            knee = [landmarks_s[mp_pose.PoseLandmark.LEFT_KNEE.value].x,
                    landmarks_s[mp_pose.PoseLandmark.LEFT_KNEE.value].y]
            ankle = [landmarks_s[mp_pose.PoseLandmark.LEFT_ANKLE.value].x,
                     landmarks_s[mp_pose.PoseLandmark.LEFT_ANKLE.value].y]
            elbow = [landmarks_s[mp_pose.PoseLandmark.LEFT_ELBOW.value].x,
                     landmarks_s[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
            wrist = [landmarks_s[mp_pose.PoseLandmark.LEFT_WRIST.value].x,
                     landmarks_s[mp_pose.PoseLandmark.LEFT_WRIST.value].y]

            hip_angle = calculate_angle(shoulder, hip, knee)
            knee_angle = calculate_angle(hip, knee, ankle)
            arm_angle = calculate_angle(shoulder, elbow, wrist)

            if arm_angle < 150:
                errors_side.append("UGIETE RECE! (-10%)")
                current_score -= 10
                krytyczny_blad_glosowy = "bent_arms"

            if knee_angle > 140 and hip_angle < 115:
                errors_side.append("STRZAL Z BIODRA (GARB)! (-20%)")
                current_score -= 20
                krytyczny_blad_glosowy = "straight_back"

            if deadlift_state == "DOWN":
                if hip[1] > knee[1] - 0.05:
                    errors_side.append("BIODRA ZA NISKO (PRZYSIAD)! (-20%)")
                    current_score -= 20
                    krytyczny_blad_glosowy = "hips_too_low"
                elif hip[1] < shoulder[1] + 0.1:
                    errors_side.append("BIODRA ZA WYSOKO! (-10%)")
                    current_score -= 10
                    krytyczny_blad_glosowy = "hips_too_high"

            # wysłanie błędu do zewnętrznego modułu głosowego
            if krytyczny_blad_glosowy:
                trener.mistake_tell(krytyczny_blad_glosowy)
            else:
                trener.brak_bledow()

            current_score = max(0, current_score)
            if deadlift_state == "DOWN":
                rep_min_score = min(rep_min_score, current_score)

            skel_color_s = (0, 255, 0) if current_score >= 80 else (0, 0, 255)
            mp_drawing.draw_landmarks(
                frame_s, results_s.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=mp_drawing.DrawingSpec(color=skel_color_s, thickness=6, circle_radius=5),
                connection_drawing_spec=mp_drawing.DrawingSpec(color=(255, 255, 255), thickness=3)
            )

            if hip_angle < 110 and knee_angle < 120:
                if deadlift_state == "UP" or deadlift_state == "START":
                    deadlift_state = "DOWN"
                    rep_min_score = 100

            if hip_angle > 165 and knee_angle > 165:
                if deadlift_state == "DOWN":
                    if rep_min_score >= 80:
                        rep_counter += 1
                        last_rep_status = f"ZALICZONO ({rep_min_score}%)"
                        last_rep_color = (0, 255, 0)
                    else:
                        last_rep_status = f"BLEDNA FORMA ({rep_min_score}%)"
                        last_rep_color = (0, 0, 255)
                    deadlift_state = "UP"

        # 3. interfejs
        cv2.putText(frame_f, f"Powtorzenia: {rep_counter}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
        score_color = (0, 255, 0) if current_score >= 80 else (0, 0, 255)
        cv2.putText(frame_f, f"Obecna forma: {current_score}%", (20, 90), cv2.FONT_HERSHEY_SIMPLEX, 1.0, score_color, 2)

        y_offset = 140
        for err in errors_front:
            cv2.putText(frame_f, err, (20, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
            y_offset += 35

        cv2.putText(frame_s, f"Stan: {deadlift_state}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 0), 3)
        if last_rep_status:
            cv2.putText(frame_s, f"Ostatnie: {last_rep_status}", (20, 90), cv2.FONT_HERSHEY_SIMPLEX, 1.0,
                        last_rep_color, 2)

        y_offset = 140
        for err in errors_side:
            cv2.putText(frame_s, err, (20, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
            y_offset += 35

        combined_view = np.hstack((frame_f, frame_s))
        cv2.imshow('Skaner Deadlift Pro', combined_view)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cam_front.stop()
cam_side.stop()
cv2.destroyAllWindows()