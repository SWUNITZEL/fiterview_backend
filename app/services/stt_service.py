import subprocess
import os
import json
import uuid

WHISPER_CLI = "./whisper.cpp/build/bin/whisper-cli"
MODEL_PATH = "./whisper.cpp/models/ggml-small.bin"

def transcribe_wav(wav_path: str) -> str:
    output_json_path = f"{wav_path}.json"

    result = subprocess.run([
        WHISPER_CLI,
        "-m", MODEL_PATH,
        "-f", wav_path,
        "--output-json"
    ], capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"STT 실패: {result.stderr}")

    with open(output_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    text = " ".join([seg["text"] for seg in data["segments"]])

    # 파일 정리
    os.remove(output_json_path)

    return text
