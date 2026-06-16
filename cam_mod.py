import cv2
import numpy as np
import threading
import time
import ssl
import json
import mediapipe as mp
from voice_mod import VoiceMod

# Wyłączenie weryfikacji SSL
ssl._create_default_https_context = ssl._create_unverified_context

mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose


class BackgroundCameraStream:
    def __init__(self, camera_source, target_width, target_height):
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


class DeadliftScannerApp:
    def __init__(self):
        with open('config/cam_config.json', 'r') as config_file:
            config = json.load(config_file)
        self.config = config
        self.target_width = self.config['camera']['width']
        self.target_height = self.config['camera']['height']

        self.color_green = tuple(self.config['ui']['colors']['green'])
        self.color_red = tuple(self.config['ui']['colors']['red'])
        self.color_white = tuple(self.config['ui']['colors']['white'])
        self.color_cyan = tuple(self.config['ui']['colors']['cyan'])

        self.front_camera = BackgroundCameraStream(
            camera_source=self.config['camera']['front_index'],
            target_width=self.target_width,
            target_height=self.target_height
        ).start_stream()

        self.side_camera = BackgroundCameraStream(
            camera_source=self.config['camera']['side_index'],
            target_width=self.target_width,
            target_height=self.target_height
        ).start_stream()

        self.voice_coach = VoiceMod()
        self.last_warning_times = {}
        self.last_critical_error = None
        self.is_coach_speaking = False

        self.total_reps_counter = 0
        self.current_movement_state = "START"
        self.max_score = self.config['logic']['max_score']
        self.lowest_form_score_in_rep = self.max_score
        self.last_rep_message = ""
        self.last_rep_text_color = self.color_white

        self.is_running = False

    @staticmethod
    def calculate_angle(point_a, point_b, point_c):
        point_a = np.array(point_a)
        point_b = np.array(point_b)
        point_c = np.array(point_c)

        radians = np.arctan2(point_c[1] - point_b[1], point_c[0] - point_b[0]) - \
                  np.arctan2(point_a[1] - point_b[1], point_a[0] - point_b[0])
        angle = np.abs(radians * 180.0 / np.pi)

        result = 360 - angle if angle > 180.0 else angle

        return result

    def trigger_voice_warning(self, error_name):
        if self.is_coach_speaking:
            return

        current_time = time.time()
        is_new_error = (error_name != self.last_critical_error)
        has_enough_time_passed = (current_time - self.last_warning_times.get(error_name, 0) > self.config['logic'][
            'voice_warning_cooldown'])

        if is_new_error or has_enough_time_passed:
            self.last_critical_error = error_name
            self.last_warning_times[error_name] = current_time

            def speak_action():
                self.is_coach_speaking = True
                self.voice_coach.mistake_tell(error_name)
                self.is_coach_speaking = False

            threading.Thread(target=speak_action, daemon=True).start()

    def reset_coach_memory(self):
        if not self.is_coach_speaking:
            self.last_critical_error = None

    def stop(self):
        self.is_running = False

    def run(self):
        self.is_running = True

        mp_conf = self.config['mediapipe']
        with mp_pose.Pose(min_detection_confidence=mp_conf['min_detection_confidence'],
                          min_tracking_confidence=mp_conf['min_tracking_confidence'],
                          model_complexity=mp_conf['model_complexity']) as front_pose_ai, \
                mp_pose.Pose(min_detection_confidence=mp_conf['min_detection_confidence'],
                             min_tracking_confidence=mp_conf['min_tracking_confidence'],
                             model_complexity=mp_conf['model_complexity']) as side_pose_ai:

            while self.is_running:
                front_frame = self.front_camera.get_current_frame()
                side_frame = self.side_camera.get_current_frame()

                if front_frame is None or side_frame is None:
                    front_status = "ok" if front_frame is not None else "brak"
                    side_status = "ok" if side_frame is not None else "brak"
                    print(f"czekam na kamery... przod: {front_status} | bok: {side_status}")
                    time.sleep(self.config['logic']['sleep_time_on_wait'])
                    continue

                front_frame = cv2.resize(front_frame, (self.target_width, self.target_height))
                side_frame = cv2.resize(side_frame, (self.target_width, self.target_height))

                front_image_rgb = cv2.cvtColor(front_frame, cv2.COLOR_BGR2RGB)
                side_image_rgb = cv2.cvtColor(side_frame, cv2.COLOR_BGR2RGB)

                front_ai_results = front_pose_ai.process(front_image_rgb)
                side_ai_results = side_pose_ai.process(side_image_rgb)

                front_errors_list = []
                side_errors_list = []
                critical_error_to_say = None
                current_frame_score = self.max_score

                logic_cfg = self.config['logic']
                ui_cfg = self.config['ui']

                # 1. Analiza przód
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

                    if abs(left_shoulder[0] - right_shoulder[0]) > logic_cfg['front']['shoulder_asymmetry_threshold']:
                        penalty = logic_cfg['front']['shoulder_asymmetry_penalty']
                        front_errors_list.append(f"ASYMETRIA BARKOW! (-{penalty}%)")
                        current_frame_score -= penalty
                        critical_error_to_say = "delts_asymetry"

                    distance_between_knees = abs(left_knee_x - right_knee_x)
                    distance_between_hips = abs(left_hip_x - right_hip_x)
                    if distance_between_knees < distance_between_hips * logic_cfg['front']['knees_hips_ratio']:
                        penalty = logic_cfg['front']['knees_inward_penalty']
                        front_errors_list.append(f"KOLANA DO SRODKA! (-{penalty}%)")
                        current_frame_score -= penalty
                        critical_error_to_say = "legs_width"

                    front_skeleton_color = self.color_green if current_frame_score >= logic_cfg[
                        'good_form_threshold'] else self.color_red

                    mp_drawing.draw_landmarks(
                        front_frame, front_ai_results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                        landmark_drawing_spec=mp_drawing.DrawingSpec(color=front_skeleton_color,
                                                                     thickness=ui_cfg['skeleton_thickness'],
                                                                     circle_radius=ui_cfg['skeleton_circle_radius']),
                        connection_drawing_spec=mp_drawing.DrawingSpec(color=self.color_white,
                                                                       thickness=ui_cfg['connection_thickness'])
                    )

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

                    angle_of_hip = self.calculate_angle(side_shoulder, side_hip, side_knee)
                    angle_of_knee = self.calculate_angle(side_hip, side_knee, side_ankle)
                    angle_of_arm = self.calculate_angle(side_shoulder, side_elbow, side_wrist)

                    side_cfg = logic_cfg['side']

                    if angle_of_arm < side_cfg['arm_angle_threshold']:
                        penalty = side_cfg['arm_bent_penalty']
                        side_errors_list.append(f"UGIETE RECE! (-{penalty}%)")
                        current_frame_score -= penalty
                        critical_error_to_say = "bent_arms"

                    if angle_of_knee > side_cfg['knee_garb_threshold'] and angle_of_hip < side_cfg[
                        'hip_garb_threshold']:
                        penalty = side_cfg['garb_penalty']
                        side_errors_list.append(f"STRZAL Z BIODRA (GARB)! (-{penalty}%)")
                        current_frame_score -= penalty
                        critical_error_to_say = "straight_back"

                    if self.current_movement_state == "DOWN":
                        if side_hip[1] > side_knee[1] - side_cfg['hips_too_low_offset']:
                            penalty = side_cfg['hips_too_low_penalty']
                            side_errors_list.append(f"BIODRA ZA NISKO (PRZYSIAD)! (-{penalty}%)")
                            current_frame_score -= penalty
                            critical_error_to_say = "hips_too_low"
                        elif side_hip[1] < side_shoulder[1] + side_cfg['hips_too_high_offset']:
                            penalty = side_cfg['hips_too_high_penalty']
                            side_errors_list.append(f"BIODRA ZA WYSOKO! (-{penalty}%)")
                            current_frame_score -= penalty
                            critical_error_to_say = "hips_too_high"

                    if critical_error_to_say:
                        self.trigger_voice_warning(critical_error_to_say)
                    else:
                        self.reset_coach_memory()

                    current_frame_score = max(0, current_frame_score)
                    if self.current_movement_state == "DOWN":
                        self.lowest_form_score_in_rep = min(self.lowest_form_score_in_rep, current_frame_score)

                    side_skeleton_color = self.color_green if current_frame_score >= logic_cfg[
                        'good_form_threshold'] else self.color_red
                    mp_drawing.draw_landmarks(
                        side_frame, side_ai_results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                        landmark_drawing_spec=mp_drawing.DrawingSpec(color=side_skeleton_color,
                                                                     thickness=ui_cfg['skeleton_thickness'],
                                                                     circle_radius=ui_cfg['skeleton_circle_radius']),
                        connection_drawing_spec=mp_drawing.DrawingSpec(color=self.color_white,
                                                                       thickness=ui_cfg['connection_thickness'])
                    )

                    if angle_of_hip < side_cfg['state_down_hip_angle'] and angle_of_knee < side_cfg[
                        'state_down_knee_angle']:
                        if self.current_movement_state in ["UP", "START"]:
                            self.current_movement_state = "DOWN"
                            self.lowest_form_score_in_rep = self.max_score

                    if angle_of_hip > side_cfg['state_up_hip_angle'] and angle_of_knee > side_cfg[
                        'state_up_knee_angle']:
                        if self.current_movement_state == "DOWN":
                            if self.lowest_form_score_in_rep >= logic_cfg['good_form_threshold']:
                                self.total_reps_counter += 1
                                self.last_rep_message = f"ZALICZONO ({self.lowest_form_score_in_rep}%)"
                                self.last_rep_text_color = self.color_green
                            else:
                                self.last_rep_message = f"BLEDNA FORMA ({self.lowest_form_score_in_rep}%)"
                                self.last_rep_text_color = self.color_red
                            self.current_movement_state = "UP"

                cv2.putText(front_frame, f"Powtorzenia: {self.total_reps_counter}",
                            (ui_cfg['text_x'], ui_cfg['text_y_line1']),
                            cv2.FONT_HERSHEY_SIMPLEX, ui_cfg['font_scale_large'], self.color_green,
                            ui_cfg['thickness_large'])

                ui_score_color = self.color_green if current_frame_score >= logic_cfg[
                    'good_form_threshold'] else self.color_red
                cv2.putText(front_frame, f"Obecna forma: {current_frame_score}%",
                            (ui_cfg['text_x'], ui_cfg['text_y_line2']),
                            cv2.FONT_HERSHEY_SIMPLEX, ui_cfg['font_scale_medium'], ui_score_color,
                            ui_cfg['thickness_medium'])

                y_text_offset = ui_cfg['text_y_errors_start']
                for error_text in front_errors_list:
                    cv2.putText(front_frame, error_text, (ui_cfg['text_x'], y_text_offset),
                                cv2.FONT_HERSHEY_SIMPLEX, ui_cfg['font_scale_small'], self.color_red,
                                ui_cfg['thickness_medium'])
                    y_text_offset += ui_cfg['text_y_step']

                cv2.putText(side_frame, f"Stan: {self.current_movement_state}",
                            (ui_cfg['text_x'], ui_cfg['text_y_line1']),
                            cv2.FONT_HERSHEY_SIMPLEX, ui_cfg['font_scale_large'], self.color_cyan,
                            ui_cfg['thickness_large'])

                if self.last_rep_message:
                    cv2.putText(side_frame, f"Ostatnie: {self.last_rep_message}",
                                (ui_cfg['text_x'], ui_cfg['text_y_line2']),
                                cv2.FONT_HERSHEY_SIMPLEX, ui_cfg['font_scale_medium'], self.last_rep_text_color,
                                ui_cfg['thickness_medium'])

                y_text_offset = ui_cfg['text_y_errors_start']
                for error_text in side_errors_list:
                    cv2.putText(side_frame, error_text, (ui_cfg['text_x'], y_text_offset),
                                cv2.FONT_HERSHEY_SIMPLEX, ui_cfg['font_scale_small'], self.color_red,
                                ui_cfg['thickness_medium'])
                    y_text_offset += ui_cfg['text_y_step']

                combined_camera_view = np.hstack((front_frame, side_frame))
                cv2.imshow('Skaner Deadlift Pro', combined_camera_view)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    self.stop()

        self.cleanup()

    def cleanup(self):
        self.front_camera.stop_stream()
        self.side_camera.stop_stream()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    app = DeadliftScannerApp()
    app.run()