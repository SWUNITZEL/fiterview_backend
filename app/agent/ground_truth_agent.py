import re
from typing import List
from app.agent.gpt_api_utils import call_gpt, load_prompt

class GroundTruthAgent:
    def __init__(self, prompt_path="app/agent/prompt/ground_truth_agent.txt"):
        self.prompt_path = prompt_path

    def generate_ground_truth(self, department: str, document: str, questions: List[str]):
        """
        생성된 질문에 ground truth 생성
        """
        # 프롬프트 불러오기 + 변수 치환
        prompt = load_prompt(
            self.prompt_path,
            department=department,
            document=document,
            questions=questions
        )

        system_prompt, user_prompt= prompt.split("---", 1)
        
        # ChatGPT API 호출
        result = call_gpt(system_prompt, user_prompt, 0.8)
        ground_truth={}
        # 정규식으로 groundtruth 전처리        
        # 패턴 1
        pattern1 = re.compile(r'\(?(\d+)\)?\s*:\s*\[(.*?)\]', re.DOTALL)
        matches1 = pattern1.findall(result)

        for key, val in matches1:
            # 쉼표 기준으로 나누고, 빈 문자열 제거
            answers = [a.strip().strip('()"') for a in val.split('.,') if a.strip()]
            ground_truth[key] = answers

        # 2) 괄호 패턴: (숫자): [(답변1), (답변2), ...]
        pattern2 = re.compile(r'\(?(\d+)\)?\s*:\s*\[\s*(\([^\]]*?\))\s*\]', re.DOTALL)
        matches2 = pattern2.findall(result)

        for key, val in matches2:
            # 괄호 안 문자열 추출
            answers = re.findall(r'\((.*?)\)', val, re.DOTALL)
            answers = [a.strip().replace('"',"").replace("'","") for a in answers if a.strip()]
            ground_truth[key] = answers
            
        return ground_truth