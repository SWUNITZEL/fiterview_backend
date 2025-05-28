import cv2
import mediapipe as mp
from app.repository import posture_repository

mp_pose = mp.solutions.pose
pose = mp_pose.Pose(min_detection_confidence=0.6, min_tracking_confidence=0.7)

screen_width = 640
screen_height = 480

cap = cv2.VideoCapture(0)
cap.set(3, screen_width)
cap.set(4, screen_height)

# 사진을 통해 기준 데이터 구하는 메서드
def calibrate_posture_points(image_path: str):
    image = cv2.imread(image_path)
    if image is None:
        print("Image not found!")
        return None, None

    with mp_pose.Pose(static_image_mode=True, model_complexity=1) as pose_static:
        results = pose_static.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        if not results.pose_landmarks:
            print("No pose landmarks found!")
            return None, None

        landmarks = results.pose_landmarks.landmark
        left_shoulder_y = landmarks[11].y
        right_shoulder_y = landmarks[12].y
        shoulder_diff = abs(left_shoulder_y - right_shoulder_y)

        nose_x = landmarks[0].x
        left_ear_x = landmarks[7].x
        right_ear_x = landmarks[8].x
        head_center_x = (left_ear_x + right_ear_x) / 2
        head_rotation = nose_x - head_center_x

        return shoulder_diff, head_rotation

# 기준값 불러오기
try:
    latest = posture_repository.get_latest_calibration_data()
    calibration_shoulder_diff = latest["shoulder_diff"]
    calibration_head_rotation = latest["head_rotation"]
except:
    calibration_shoulder_diff, calibration_head_rotation = calibrate_posture_points("calibration_image.jpg")

shoulder_tilt_count = 0
turn_left_count = 0
turn_right_count = 0
prev_label = None
same_posture_count = 0
threshold_frame = 10
sensitivity = 0.02

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose.process(rgb)

    if results.pose_landmarks:
        landmarks = results.pose_landmarks.landmark

        left_shoulder_y = landmarks[11].y
        right_shoulder_y = landmarks[12].y
        shoulder_diff = abs(left_shoulder_y - right_shoulder_y)

        nose_x = landmarks[0].x
        left_ear_x = landmarks[7].x
        right_ear_x = landmarks[8].x
        head_center_x = (left_ear_x + right_ear_x) / 2
        head_rotation = nose_x - head_center_x

        posture_label = "GOOD"
        if shoulder_diff > calibration_shoulder_diff + sensitivity:
            posture_label = "SHOULDER TILT"
        elif head_rotation > calibration_head_rotation + sensitivity:
            posture_label = "TURN RIGHT"
        elif head_rotation < calibration_head_rotation - sensitivity:
            posture_label = "TURN LEFT"

        if posture_label == prev_label:
            same_posture_count += 1
        else:
            same_posture_count = 1
            prev_label = posture_label

        if same_posture_count == threshold_frame:
            if posture_label == "SHOULDER TILT":
                shoulder_tilt_count += 1
            elif posture_label == "TURN LEFT":
                turn_left_count += 1
            elif posture_label == "TURN RIGHT":
                turn_right_count += 1
            same_posture_count = 0

        cv2.putText(frame, f"Posture: {posture_label}", (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    cv2.imshow("Posture Tracking", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# 결과 저장
posture_repository.insert_analysis_data({
    "shoulder_tilt_count": shoulder_tilt_count,
    "turn_left_count": turn_left_count,
    "turn_right_count": turn_right_count
})

print(f"저장 완료: 어깨 기울임 {shoulder_tilt_count}회, 좌회전 {turn_left_count}회, 우회전 {turn_right_count}회")

cap.release()
cv2.destroyAllWindows()







