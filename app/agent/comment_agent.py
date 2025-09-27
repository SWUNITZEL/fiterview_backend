from .gpt_api_utils import call_gpt, load_prompt

class CommentAgent:
    def __init__(self, prompt_path="app/agent/prompt/comment_agent.txt"):
        self.prompt_path = prompt_path

    def generate_comment(self, department: str, document: str):
        """
        생활기록부 주요 내용 요약 및 코멘트 생성
        """
        # 프롬프트 불러오기 + 변수 치환
        prompt = load_prompt(
            self.prompt_path,
            department=department,
            document=document
        )

        system_prompt, user_prompt= prompt.split("---", 1)
        # ChatGPT API 호출
        comment = call_gpt(system_prompt, user_prompt)
        return comment

