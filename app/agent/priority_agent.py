import re
from typing import List
from app.agent.gpt_api_utils import call_gpt, load_prompt

class PriorityAgent:
    def __init__(self, prompt_path="app/agent/prompt/priority_agent.txt"):
        self.prompt_path = prompt_path

    def clean_question(self, question: str) -> str:
        # 번호 제거
        question = re.sub(r'^\d+\).?\s*', '', question)
        # category 뒤 나머지 텍스트만 추출
        parts = re.split(r'\[.*?\]', question, maxsplit=1)
        return parts[-1].strip().replace('\"',"").replace("'","") if parts else question.strip().replace('\"',"").replace("'","")

    def parse_question(self, question: str) -> dict:
        # ranking 추출 (앞번호)
        ranking = question.split(")")[0].split(".")[0].strip()
        
        # level 추출
        level_match = re.search(r'level:(\d+)', question)
        level = int(level_match.group(1)) if level_match else None

        # category 추출
        cat_match = re.search(r'\[(.*?)\]', question)
        category = cat_match.group(1) if cat_match else None

        # 질문 내용
        q_text = self.clean_question(question)

        return {
            "question_index": int(ranking),
            "level": level,
            "category": category,
            "question_text": q_text
        }

    def generate_priority(self, department: str, questions: List[str]):
        prompt = load_prompt(
            self.prompt_path,
            department=department,
            questions=questions,
        )
        system_prompt, user_prompt = prompt.split("---", 1)

        # ChatGPT API 호출
        result = call_gpt(system_prompt, user_prompt)

        # 줄바꿈 기준으로 나누고, 빈줄 제거 후 parse
        questions_parsed = [self.parse_question(q) 
                            for q in result.split("\n") if q.strip() != ""]
        return questions_parsed