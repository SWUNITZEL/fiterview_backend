import openai
import os
from app.core.config import Settings

client = openai.OpenAI(api_key=Settings.GPT_API_KEY)

async def generate_interview_questions(document_text: str, persona_label: str, major: str) -> str:
    prompt = f"""
당신은 다음과 같은 성향의 대학 면접관입니다:

{persona_label}

아래는 한 수험생의 자기소개서 또는 생활기록부입니다.

아래 형식에 따라 총 10개의 질문을 생성하세요.  
질문은 지원 전공 '{major}'과 문서 내용을 기반으로 하며, 면접관의 성격도 반영되어야 합니다.

[질문 구성]
1. 자기소개를 요청하는 질문  
2. 학교(대학) 지원 동기를 묻는 질문  
3. 전공(학과) 지원 동기를 묻는 질문  
4. 본인의 장단점을 묻는 질문  
5~9. 아래 문서를 참고하여 학생의 경험, 가치관, 활동, 전공 관련성 등을 기반으로 위 면접관 스타일에 맞춘 심화 질문 5개 생성  
10. 마지막 한마디 혹은 마무리 발언을 요청하는 질문

[문서 내용]
{document_text}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )

    return response.choices[0].message.content.strip()

