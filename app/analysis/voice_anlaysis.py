import parselmouth
import numpy as np


def calculate_pitch_mean(filepath):
    try:
        sound = parselmouth.Sound(filepath)
        pitch = sound.to_pitch()
        pitch_values = pitch.selected_array['frequency']
        pitch_values = pitch_values[pitch_values != 0]  # 0Hz 제외 (무성 구간)

        if len(pitch_values) == 0:
            return None  # 유효한 pitch 값이 없음

        pitch_mean = round(np.nanmean(pitch_values))
        return pitch_mean
    except Exception as e:
        print(f"오류 발생: {e}")
        return None