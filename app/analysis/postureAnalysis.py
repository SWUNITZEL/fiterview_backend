import math as m
import mediapipe as mp

# Mediapipe 초기화
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()

def calculate_pose_calibration(pose_landmarks, img_h, img_w):
    landmarks = pose_landmarks.landmark

    left_shoulder_y = landmarks[11].y
    right_shoulder_y = landmarks[12].y
    shoulder_diff = abs(left_shoulder_y - right_shoulder_y)

    nose_x = landmarks[0].x
    left_ear_x = landmarks[7].x
    right_ear_x = landmarks[8].x
    head_center_x = (left_ear_x + right_ear_x) / 2
    head_rotation = nose_x - head_center_x

    return shoulder_diff, head_rotation



