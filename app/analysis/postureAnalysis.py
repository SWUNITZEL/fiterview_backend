import math as m
import mediapipe as mp
from pymongo import MongoClient

# MongoDB 연결
client = MongoClient('mongodb://localhost:27017/')
db = client['test_db']
calibration_collection = db['posture_calibration']
analysis_collection = db['posture_analysis']

# 거리 계산
def findDistance(x1, y1, x2, y2):
    return m.sqrt((x2 - x1)**2 + (y2 - y1)**2)

# Mediapipe 초기화
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()

def calculate_pose_calibration(pose_landmarks, img_h, img_w):
    lm = pose_landmarks.landmark

    l_shldr = lm[mp_pose.PoseLandmark.LEFT_SHOULDER]
    r_shldr = lm[mp_pose.PoseLandmark.RIGHT_SHOULDER]
    l_ear = lm[mp_pose.PoseLandmark.LEFT_EAR]

    shoulder_distance = findDistance(l_shldr.x * img_w, l_shldr.y * img_h,
                                     r_shldr.x * img_w, r_shldr.y * img_h)
    head_x = l_ear.x * img_w

    return shoulder_distance, head_x


# print("실시간 자세 분석 시작")
#
# # 자세 분석
# threshold_shoulder = 20
# threshold_head = 15
#
# shoulder_move_count = 0
# head_move_count = 0
# shoulder_frame_counter = 0
# head_frame_counter = 0
#
# # 기준값 불러오기
# calib = calibration_collection.find_one(sort=[('_id', -1)])
# base_shoulder_distance = calib['shoulder_distance']
# base_head_x = calib['head_x']
#
# # 실시간 루프
# while cap.isOpened():
#     success, frame = cap.read()
#     if not success:
#         break
#
#     rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#     result = pose.process(rgb)
#
#     if result.pose_landmarks:
#         lm = result.pose_landmarks.landmark
#         width, height = frame.shape[1], frame.shape[0]
#
#         l_shldr = lm[mp_pose.PoseLandmark.LEFT_SHOULDER]
#         r_shldr = lm[mp_pose.PoseLandmark.RIGHT_SHOULDER]
#         l_ear = lm[mp_pose.PoseLandmark.LEFT_EAR]
#
#         curr_shoulder_distance = findDistance(l_shldr.x * width, l_shldr.y * height,
#                                               r_shldr.x * width, r_shldr.y * height)
#         curr_head_x = l_ear.x * width
#
#         # 어깨 움직임 감지 (몸 기울임,가까워 지거나 멀어짐, 위 아래 움직임 모두 고려)
#         if abs(curr_shoulder_distance - base_shoulder_distance) > threshold_shoulder:
#             shoulder_frame_counter += 1
#         else:
#             if shoulder_frame_counter > 5:
#                 shoulder_move_count += 1
#             shoulder_frame_counter = 0
#
#         # 머리 움직임 감지(좌우만)
#         if abs(curr_head_x - base_head_x) > threshold_head:
#             head_frame_counter += 1
#         else:
#             if head_frame_counter > 5:
#                 head_move_count += 1
#             head_frame_counter = 0


