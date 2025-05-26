import openai
import json
from app.core.config import settings
from app.core.exceptions.base import AppException


class GPTService:
    api_key = settings.GPT_API_KEY
    client = openai.OpenAI(api_key=api_key)

    def analyze_student_record_structured(self, record_text):
        prompt = f"""
        너는 학생 생활기록부를 분석하는 교육 전문가야.
        다음은 '세부능력 및 특기사항' 항목이야:

        "{record_text}"


        이 내용을 바탕으로 다음을 생성해줘:
        1. 이 학생을 잘 나타낼 수 있는 유형을 써줘(예: 솔선수범하는 학업전공열정 다재다능형)
        2. 이 학생을 잘 나타낼 수 있는 핵심 키워드를 해시태그 형식으로 5개 출력해줘. (예: #목표지향 #리더형 #솔선수범 #탐구왕성 #진취적 등)
        3. 1번에서 왜 그 유형인지에 대한 설명 2~3문장 써줘.


        이 내용을 바탕으로 다음과 같이 JSON 형식으로 출력해줘:

        {{
            "type": "",
            "hashtags": ["#키워드1", "#키워드2", "#키워드3", "#키워드4", "#키워드5"],
            "explanation" : ""
        }}

        불필요한 설명 없이 위의 JSON만 응답해.
            """

        response = self.client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
        )

        content = response.choices[0].message.content

        try:
            return json.loads(content)

        except json.JSONDecodeError:
            raise AppException(status_code=400, message="세특 분석에 실패했습니다.")
            # return None

