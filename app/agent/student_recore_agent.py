import json
from .gpt_api_utils import call_gpt, load_prompt
from ..core.exceptions.base import AppException


class StudentRecordAgent:
    def __init__(self, prompt_path="app/agent/prompt/student_record_agent.txt",
                 prompt_path_3rd="app/agent/prompt/student_record_3rd_agent.txt"):
        self.prompt_path = prompt_path
        self.prompt_path_3rd = prompt_path_3rd

    def analyze_student_record(self, document: str, grade: dict[str, list], school_year: int):
        """
        생활기록부 주요 내용 요약 및 코멘트 생성
        """
        if school_year <= 0:
            raise AppException(status_code=400, message="성적 기록이 존재하지 않습니다.")

        if school_year >= 5:
            prompt = load_prompt(
                self.prompt_path_3rd,
                document=document,
                grade=grade
            )

        else:
            prompt = load_prompt(
                self.prompt_path,
                document=document,
                grade=grade
            )

        system_prompt, user_prompt= prompt.split("---", 1)

        # ChatGPT API 호출
        result = call_gpt(system_prompt, user_prompt)
        return self.parse_advice_response(result)


    def parse_advice_response(self, response_str: str) -> dict:
        try:
            data = json.loads(response_str)

            if "major" in data and "type" in data and "explanation" in data and "hashtags" in data:
                if "advice" in data:
                    return data['major'], data['advice'], data['type'], data['explanation'], data['hashtags']
                else :
                    return data['major'], "", data['type'], data['explanation'], data['hashtags']

            else:
                raise AppException(status_code=400, message="1111생기부 분석 실패: ")

        except Exception as e:
            # 4. 그 외 예기치 못한 오류 처리
            raise AppException(status_code=400, message="생기부 분석 실패: " + e)

