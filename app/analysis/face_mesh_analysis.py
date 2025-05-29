import numpy as np
import mediapipe as mp

left_iris_indices = [468, 469, 470, 471]
right_iris_indices = [473, 474, 475, 476]

mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(max_num_faces=1,
                                  refine_landmarks=True,
                                  min_detection_confidence=0.6,
                                  min_tracking_confidence=0.7)

# 여러 프레임의 얼굴 랜드마크에서 평균 입꼬리 변화를 기반으로 웃음 여부를 판단합니다.
# 웃는 정도를 계산하여 점수화한 평균값과 웃었는지의 여부를 반환합니다.
def calculate_smile_points(face_landmarks):
    # 기준점: 코 밑 ref_y
    ref_y = face_landmarks.landmark[1].y

    # 코 밑과 턱 끝 사이의 거리
    face_height = face_landmarks.landmark[152].y - face_landmarks.landmark[1].y
    if face_height == 0:
        return None

    left_mouth = face_landmarks.landmark[61].y
    right_mouth = face_landmarks.landmark[291].y

    left_point = (left_mouth - ref_y) / face_height
    right_point = (right_mouth - ref_y) / face_height

    smile_point = (left_point + right_point) / 2
    return smile_point


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