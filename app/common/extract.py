import re
from typing import List

def extract_model_answers(text: str) -> List[str]:
    '## [모범 답변 n]  형식으로 되어 있는 답변들을 모두 리스트로 추출'

    pattern = r"## \[모범 답변 \d+\](.*?)(?=## \[모범 답변|\Z)"
    matches = re.findall(pattern, text, re.DOTALL)
    return [match.strip() for match in matches]


def extract_improved_answer(response_text: str) -> str:

    '## Step 3. 개선된 답변 : 이후만 추출'

    match = re.search(r"Step 3\. 개선된 답변:\s*(.*)", response_text, re.DOTALL)
    return match.group(1).strip() if match else response_text
