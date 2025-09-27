import re
from .gpt_api_utils import call_gpt, load_prompt
from typing import List

class QuestionGenAgent:
    def __init__(self, prompt_path="app/agent/prompt/question_gen_agent.txt"):
        self.prompt_path = prompt_path

    def generate_questions(self, department: str, document: str, comment: str):
        """
        생활기록부 주요 내용 및 코멘트를 바탕으로 질문 생성
        """
        # 프롬프트 불러오기 + 변수 치환
        prompt = load_prompt(
            self.prompt_path,
            department=department,
            document=document,
            comment=comment
        )

        system_prompt, user_prompt = prompt.split("---", 1)

        # ChatGPT API 호출
        result = call_gpt(system_prompt, user_prompt)
        questions = [re.sub(r'^\(?\d+\)?\.?\s*', '', question).strip() for question in result.split("\n") if
                     question.strip() != ""]
        return questions
