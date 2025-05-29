
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