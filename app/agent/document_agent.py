from app.agent.gpt_api_utils import call_gpt, load_prompt

class DocumentAgent:
    def __init__(self, prompt_path="app/agent/prompt/document_agent.txt"):
        self.prompt_path = prompt_path

    def generate_document(self, department: str, document: str):
        """
        생활기록부 부정적 뉘앙스 잡아주는 에이전트
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