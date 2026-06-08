import cv2
import numpy as np
import threading
import time
import ssl
import mediapipe as mp
from voice_mod import VoiceCoach

ssl._create_default_https_context = ssl._create_unverified_context

mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

FRONT_CAMERA_INDEX = 0
SIDE_CAMERA_INDEX = 1

TARGET_WIDTH = 960
TARGET_HEIGHT = 720


class BackgroundCameraStream:
    def __init__(self, camera_source=0, target_width=960, target_height=720):
        self.video_stream = cv2.VideoCapture(camera_source)
        self.video_stream.set(cv2.CAP_PROP_FRAME_WIDTH, target_width)
        self.video_stream.set(cv2.CAP_PROP_FRAME_HEIGHT, target_height)
        self.is_frame_grabbed, self.current_frame = self.video_stream.read()
        self.is_stopped = False

    def start_stream(self):
        threading.Thread(target=self.update_frames, args=(), daemon=True).start()
        return self

    def update_frames(self):
        while not self.is_stopped:
            try:
                if not self.is_frame_grabbed:
                    self.stop_stream()
                else:
                    self.is_frame_grabbed, self.current_frame = self.video_stream.read()
            except Exception:
                self.is_stopped = True
                break

    def get_current_frame(self):
        return self.current_frame

    def stop_stream(self):
        self.is_stopped = True
        self.video_stream.release()


def calculate_angle(point_a, point_b, point_c):
    point_a = np.array(point_a)
    point_b = np.array(point_b)
    point_c = np.array(point_c)
    radians = np.arctan2(point_c[1] - point_b[1], point_c[0] - point_b[0]) - np.arctan2(point_a[1] - point_b[1],
                                                                                        point_a[0] - point_b[0])
    angle = np.abs(radians * 180.0 / np.pi)
    return 360 - angle if angle > 180.0 else angle


front_camera = BackgroundCameraStream(camera_source=FRONT_CAMERA_INDEX, target_width=TARGET_WIDTH,
                                      target_height=TARGET_HEIGHT).start_stream()
side_camera = BackgroundCameraStream(camera_source=SIDE_CAMERA_INDEX, target_width=TARGET_WIDTH,
                                     target_height=TARGET_HEIGHT).start_stream()

voice_coach = VoiceCoach()

# zmienne do zarzadzania czasem i watkami glosu
last_warning_times = {}
last_critical_error = None
is_coach_speaking = False


def trigger_voice_warning(error_name):
    global last_critical_error, is_coach_speaking

    if is_coach_speaking:
        return

    current_time = time.time()
    is_new_error = (error_name != last_critical_error)
    has_enough_time_passed = (current_time - last_warning_times.get(error_name, 0) > 4.0)

    if is_new_error or has_enough_time_passed:
        last_critical_error = error_name
        last_warning_times[error_name] = current_time

        # funkcja pomocnicza dla watku
        def speak_action():
            global is_coach_speaking
            is_coach_speaking = True
            voice_coach.announce_error(error_name)
            is_coach_speaking = False

        # tworzymy watek po stronie kamery
        threading.Thread(target=speak_action, daemon=True).start()


def reset_coach_memory():
    global last_critical_error
    if not is_coach_speaking:
        last_critical_error = None


total_reps_counter = 0
current_movement_state = "START"
lowest_form_score_in_rep = 100
last_rep_message = ""
last_rep_text_color = (255, 255, 255)

with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5, model_complexity=1) as front_pose_ai, \
        mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5, model_complexity=1) as side_pose_ai:
    while True:
        front_frame = front_camera.get_current_frame()
        side_frame = side_camera.get_current_frame()

        if front_frame is None or side_frame is None:
            front_camera_status = "ok" if front_frame is not None else "brak"
            side_camera_status = "ok" if side_frame is not None else "brak"
            print(f"czekam na kamery... przod: {front_camera_status} | bok: {side_camera_status}")
            time.sleep(1)
            continue

        front_frame = cv2.resize(front_frame, (TARGET_WIDTH, TARGET_HEIGHT))
        side_frame = cv2.resize(side_frame, (TARGET_WIDTH, TARGET_HEIGHT))

        front_image_rgb = cv2.cvtColor(front_frame, cv2.COLOR_BGR2RGB)
        side_image_rgb = cv2.cvtColor(side_frame, cv2.COLOR_BGR2RGB)

        front_ai_results = front_pose_ai.process(front_image_rgb)
        side_ai_results = side_pose_ai.process(side_image_rgb)

        front_errors_list = []
        side_errors_list = []
        critical_error_to_say = None
        current_frame_score = 100

        # 1. analiza przod
        if front_ai_results.pose_landmarks:
            front_landmarks = front_ai_results.pose_landmarks.landmark

            left_shoulder = [front_landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y,
                             front_landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x]
            right_shoulder = [front_landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y,
                              front_landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x]
            left_knee_x = front_landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x
            right_knee_x = front_landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].x
            left_hip_x = front_landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x
            right_hip_x = front_landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].x

            if abs(left_shoulder[0] - right_shoulder[0]) > 0.04:
                front_errors_list.append("ASYMETRIA BARKOW! (-10%)")
                current_frame_score -= 10
                critical_error_to_say = "delts_asymetry"

            distance_between_knees = abs(left_knee_x - right_knee_x)
            distance_between_hips = abs(left_hip_x - right_hip_x)
            if distance_between_knees < distance_between_hips * 0.85:
                front_errors_list.append("KOLANA DO SRODKA! (-15%)")
                current_frame_score -= 15
                critical_error_to_say = "legs_width"

            front_skeleton_color = (0, 255, 0) if current_frame_score >= 80 else (0, 0, 255)
            mp_drawing.draw_landmarks(
                front_frame, front_ai_results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=mp_drawing.DrawingSpec(color=front_skeleton_color, thickness=6, circle_radius=5),
                connection_drawing_spec=mp_drawing.DrawingSpec(color=(255, 255, 255), thickness=3)
            )

        # 2. analiza bok
        if side_ai_results.pose_landmarks:
            side_landmarks = side_ai_results.pose_landmarks.landmark

            side_shoulder = [side_landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,
                             side_landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
            side_hip = [side_landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x,
                        side_landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
            side_knee = [side_landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x,
                         side_landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y]
            side_ankle = [side_landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].x,
                          side_landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].y]
            side_elbow = [side_landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x,
                          side_landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
            side_wrist = [side_landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x,
                          side_landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y]

            angle_of_hip = calculate_angle(side_shoulder, side_hip, side_knee)
            angle_of_knee = calculate_angle(side_hip, side_knee, side_ankle)
            angle_of_arm = calculate_angle(side_shoulder, side_elbow, side_wrist)

            if angle_of_arm < 150:
                side_errors_list.append("UGIETE RECE! (-10%)")
                current_frame_score -= 10
                critical_error_to_say = "bent_arms"

            if angle_of_knee > 140 and angle_of_hip < 115:
                side_errors_list.append("STRZAL Z BIODRA (GARB)! (-20%)")
                current_frame_score -= 20
                critical_error_to_say = "straight_back"

            if current_movement_state == "DOWN":
                if side_hip[1] > side_knee[1] - 0.05:
                    side_errors_list.append("BIODRA ZA NISKO (PRZYSIAD)! (-20%)")
                    current_frame_score -= 20
                    critical_error_to_say = "hips_too_low"
                elif side_hip[1] < side_shoulder[1] + 0.1:
                    side_errors_list.append("BIODRA ZA WYSOKO! (-10%)")
                    current_frame_score -= 10
                    critical_error_to_say = "hips_too_high"

            # uzycie bramkarza watkow po stronie kamery
            if critical_error_to_say:
                trigger_voice_warning(critical_error_to_say)
            else:
                reset_coach_memory()

            current_frame_score = max(0, current_frame_score)
            if current_movement_state == "DOWN":
                lowest_form_score_in_rep = min(lowest_form_score_in_rep, current_frame_score)

            side_skeleton_color = (0, 255, 0) if current_frame_score >= 80 else (0, 0, 255)
            mp_drawing.draw_landmarks(
                side_frame, side_ai_results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=mp_drawing.DrawingSpec(color=side_skeleton_color, thickness=6, circle_radius=5),
                connection_drawing_spec=mp_drawing.DrawingSpec(color=(255, 255, 255), thickness=3)
            )

            if angle_of_hip < 110 and angle_of_knee < 120:
                if current_movement_state == "UP" or current_movement_state == "START":
                    current_movement_state = "DOWN"
                    lowest_form_score_in_rep = 100

            if angle_of_hip > 165 and angle_of_knee > 165:
                if current_movement_state == "DOWN":
                    if lowest_form_score_in_rep >= 80:
                        total_reps_counter += 1
                        last_rep_message = f"ZALICZONO ({lowest_form_score_in_rep}%)"
                        last_rep_text_color = (0, 255, 0)
                    else:
                        last_rep_message = f"BLEDNA FORMA ({lowest_form_score_in_rep}%)"
                        last_rep_text_color = (0, 0, 255)
                    current_movement_state = "UP"

        # 3. interfejs
        cv2.putText(front_frame, f"Powtorzenia: {total_reps_counter}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.2,
                    (0, 255, 0), 3)
        ui_score_color = (0, 255, 0) if current_frame_score >= 80 else (0, 0, 255)
        cv2.putText(front_frame, f"Obecna forma: {current_frame_score}%", (20, 90), cv2.FONT_HERSHEY_SIMPLEX, 1.0,
                    ui_score_color, 2)

        y_text_offset = 140
        for error_text in front_errors_list:
            cv2.putText(front_frame, error_text, (20, y_text_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
            y_text_offset += 35

        cv2.putText(side_frame, f"Stan: {current_movement_state}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.2,
                    (255, 255, 0), 3)
        if last_rep_message:
            cv2.putText(side_frame, f"Ostatnie: {last_rep_message}", (20, 90), cv2.FONT_HERSHEY_SIMPLEX, 1.0,
                        last_rep_text_color, 2)

        y_text_offset = 140
        for error_text in side_errors_list:
            cv2.putText(side_frame, error_text, (20, y_text_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
            y_text_offset += 35

        combined_camera_view = np.hstack((front_frame, side_frame))
        cv2.imshow('Skaner Deadlift Pro', combined_camera_view)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

front_camera.stop_stream()
side_camera.stop_stream()
cv2.destroyAllWindows()