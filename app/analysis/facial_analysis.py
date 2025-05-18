import numpy as np

# 여러 프레임의 얼굴 랜드마크에서 평균 입꼬리 변화를 기반으로 웃음 여부를 판단합니다.
# 웃는 정도를 계산하여 점수화한 평균값과 웃었는지의 여부를 반환합니다.
def detect_smile_from_video(face_landmarks: list[np.ndarray], threshold: float = 0.05) -> dict:
    smile_scores = []

    for landmarks in face_landmarks:
        if landmarks.shape != (468, 3):
            continue  # 잘못된 프레임은 무시

        face_height = landmarks[152][1] - landmarks[1][1]
        if face_height == 0:
            continue

        # 기준점: 코 밑 ref_y
        ref_y = landmarks[1][1]
        left_mouth = landmarks[61][1]
        right_mouth = landmarks[291][1]

        # 입꼬리 올라간 정도 (y축 기준, ref보다 위로 갈수록 음수 -> 올라간 것)
        left_score = (ref_y - left_mouth) / face_height
        right_score = (ref_y - right_mouth) / face_height

        smile_score = (left_score + right_score) / 2
        smile_scores.append(smile_score)

    if not smile_scores:
        return {"smile_score": 0.0, "is_smiling": False}

    avg_smile_score = round(np.mean(smile_scores), 4)
    is_smiling = avg_smile_score > threshold #threshold는 0.05

    return {
        "smile_score": avg_smile_score,
        "is_smiling": is_smiling
    }