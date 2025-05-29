import cv2
import mediapipe as mp
import numpy as np
from app.repository import gaze_analysis_repository, calibration_data_repository

mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(max_num_faces=1,
                                  refine_landmarks=True,
                                  min_detection_confidence=0.6,
                                  min_tracking_confidence=0.7)

mp_drawing = mp.solutions.drawing_utils


screen_width = 640
screen_height = 480

cap = cv2.VideoCapture(1)
cap.set(3, screen_width)
cap.set(4, screen_height)

left_iris_indices = [468, 469, 470, 471]
right_iris_indices = [473, 474, 475, 476]

sensitivity = 0.02

gaze_points = []
gaze_down_count = 0
count = 0 # 보조카운터. 프레임 횟수 셀 때 사용

# 눈의 종횡비와 동공 위치를 비율로 계산한 값을 반환
def calculate_gaze_points(face_landmarks, img_h, img_w):
    # 랜드마크 가져오기
    left_eye_top = face_landmarks.landmark[159]
    left_eye_bottom = face_landmarks.landmark[145]
    left_eye_left = face_landmarks.landmark[33]
    left_eye_right = face_landmarks.landmark[133]

    right_eye_left = face_landmarks.landmark[362]
    right_eye_right = face_landmarks.landmark[263]

    # 눈의 세로 및 가로 위치 계산
    top_y = int(left_eye_top.y * img_h)
    bottom_y = int(left_eye_bottom.y * img_h)
    left_x = int(left_eye_left.x * img_w)
    right_x = int(left_eye_right.x * img_w)

    # ear 계산
    eye_height = abs(top_y - bottom_y)
    eye_width = abs(right_x - left_x)
    ear = eye_height / eye_width

    # 왼쪽 홍채의 중심 x 좌표 평균값 계산
    left_iris_x = int(np.mean([face_landmarks.landmark[i].x for i in left_iris_indices]) * img_w)

    # 오른쪽 홍채의 중심 x 좌표 평균값 계산
    right_iris_x = int(np.mean([face_landmarks.landmark[i].x for i in right_iris_indices]) * img_w)

    # 오른쪽 눈의 눈꼬리 좌표 계산
    right_eye_left_x = int(right_eye_left.x * img_w)
    right_eye_right_x = int(right_eye_right.x * img_w)

    # 각각의 눈에 대한 iris ratio 계산
    left_iris_ratio = (left_iris_x - left_x) / (right_x - left_x + 1e-6)
    right_iris_ratio = (right_iris_x - right_eye_left_x) / (right_eye_right_x - right_eye_left_x + 1e-6)
    avg_iris_ratio = (left_iris_ratio + right_iris_ratio) / 2

    return ear, avg_iris_ratio



datas = calibration_data_repository.get_all_calibration_data()
calibration_ear, calibration_iris_ratio = datas[0]["ear"], datas[0]["avg_iris_ratio"]

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    face_results = face_mesh.process(rgb_frame)

    if face_results.multi_face_landmarks:
        for face_landmarks in face_results.multi_face_landmarks:
            img_h, img_w, _ = frame.shape

            ear, avg_iris_ratio = calculate_gaze_points(face_landmarks, img_h, img_w)

            gaze_x = int((avg_iris_ratio - calibration_iris_ratio) * screen_width + screen_width / 2)
            gaze_y = screen_height - int((ear - calibration_ear) * screen_height * 10 + screen_height / 2)

            if 0 <= gaze_x < screen_width and 0 <= gaze_y < screen_height:
                gaze_points.append((gaze_x, gaze_y))

            gaze_position = ""

            # 시선이 아래로 향하면 카운터에 1 추가
            if ear < calibration_ear - sensitivity:
                count += 1
                gaze_position = "DOWN"

            else:
                if ear > calibration_ear + sensitivity:
                    gaze_position = "UP"
                else:
                    gaze_position = "CENTER"
                count = 0

            # 10프레임 이상 시선이 아래를 향하면 gaze_down_count 추가
            if (count > 10):
                gaze_down_count += 1
                count = 0

            cv2.circle(frame, (gaze_x, gaze_y), 10, (0, 0, 255), -1)
            cv2.putText(frame, f"EAR: {ear:.2f}", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)
            cv2.putText(frame, "Gaze Tracking", (50, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(frame, gaze_position, (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    cv2.imshow("Eye Aspect Ratio Gaze Tracking", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

gaze_analysis_repository.insert_one({"gaze_down_count": gaze_down_count, "gaze_points": gaze_points})


cap.release()
cv2.destroyAllWindows()