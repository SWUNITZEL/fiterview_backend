import cv2
import mediapipe as mp

left_iris_indices = [468, 469, 470, 471]
right_iris_indices = [473, 474, 475, 476]

class LandmarkService:
    # face_mesh 초기화
    face_mesh = mp.solutions.face_mesh.FaceMesh(
        static_image_mode=True,
        max_num_faces=1,
        refine_landmarks=True
    )

    @staticmethod
    def calibrate_gaze_points(image_path: str):
        # 사진 받아오기
        image = cv2.imread(image_path)
        if image is None:
            print("Image not found!")
            return

        results = LandmarkService.face_mesh.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        if not results.multi_face_landmarks:
            print("No face landmarks found!")
            return
        face_landmarks = results.multi_face_landmarks[0]

        ear, avg_iris_ratio = LandmarkService.calculate_gaze_points(face_landmarks, image.shape[0], image.shape[1])
        smile_point = LandmarkService.calculate_smile_points(face_landmarks)

        return ear, avg_iris_ratio, smile_point

    # 눈의 종횡비와 동공 위치를 비율로 계산한 값을 반환
    @staticmethod
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
        import numpy as np
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

    # 표정 분석을 위한 기준점 계산
    @staticmethod
    def calculate_smile_points(face_landmarks):
        landmarks = face_landmarks.landmark

        # 기준점: 코 밑 ref_y
        ref_y = landmarks[1].y

        # 코 밑과 턱 끝 사이의 거리
        face_height = landmarks[152].y - landmarks[1].y
        left_mouth = landmarks[61].y
        right_mouth = landmarks[291].y

        left_point = (left_mouth - ref_y) / face_height
        right_point = (right_mouth - ref_y) / face_height

        smile_point = (left_point + right_point) / 2
        return smile_point

