import os
import openai
from app.core.config import settings

client = openai.OpenAI(api_key=settings.GPT_API_KEY)

def get_dynamic_fewshot(prompt_text: str) -> str:
    if "장단점" in prompt_text or "자신의 장점과 단점" in prompt_text:
        return """
[예시]
질문: 본인의 장점과 단점에 대해 말해주세요.
답변: 저의 장점은 성실함이고 저의 단점은 한 번 몰입하면 너무 지나칠 때가 있다는 것입니다.
Step 1. 분석: 흔한 모범답변처럼 보여 차별성이 떨어집니다.
Step 2. 개선 방향: 구체적인 사례와 그로 인한 결과를 담으면 좋습니다.
Step 3. 개선 답변: 저의 장점은 성실함입니다. 예를 들어, 영어 성적을 끌어올리기 위해 매일 공부계획을 세워 1년간 꾸준히 실천했고, 결국 1등급 향상이라는 결과를 얻었습니다...
"""
    elif "자기소개" in prompt_text or "1분 자기소개" in prompt_text:
        return """
[예시]
질문: 1분 자기소개 해보세요.
답변: 안녕하세요. 저는 ESG경영과 생성형 AI를 마케팅에 접목시키는 데 관심이 있는 학생입니다.
Step 1. 분석: 관심은 드러나지만, 구체적인 활동이나 강점이 부족합니다.
Step 2. 개선 방향: 본인의 특성과 활동을 연결해 간결히 표현해야 합니다.
Step 3. 개선 답변: 저는 ESG경영과 생성형 AI에 대해 학습하고, 실제 프로젝트에 적용한 경험이 있습니다. 이를 통해 기술적 감각과 사회적 가치를 함께 고려하는 마케터로 성장하고자 합니다.
"""
    else:
        return ""

def build_prompt(question: str, answer: str, major: str) -> str:
    prompt_text = f"{question}\n{answer}\n{major}"
    example = get_dynamic_fewshot(prompt_text)

    prompt = f"""
당신은 대학 입시 면접관이자 {major} 전공 교수입니다.
면접관의 시각에서 수험생의 답변을 분석하고 논리성과 구체성, 설득력을 기준으로 평가한 뒤, 개선된 답변을 제시해야 합니다.

질문: {question}
지원자 답변: "{answer}"

{example}


아래 형식에 맞춰 작성하세요:

Step 1. 분석:
Step 2. 개선 방향:
Step 3. 개선된 답변:
"""
    return prompt

def generate_feedback(prompt: str) -> str:
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "너는 대학 입시 면접 전문가야."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=1000
    )
    return completion.choices[0].message.content




