from konlpy.tag import Mecab
from collections import Counter
from app import database

# 어미 분석, 어휘 다양성 분석 서비스 함수
async def analysis_answer(answer : str) :
    m = Mecab()

    # Mecab의 전체 품사 태깅 결과 확인
    pos_list = m.pos(answer)

    # 형태소 분석: 명사, 동사, 형용사 등 주요 품사 추출
    words = [(word, pos) for word, pos in m.pos(answer) if
             pos.startswith('N') or pos.startswith('V') or pos.startswith('MM')]

    # 답변 다양성
    morph_counter = Counter(words).most_common()
    final_result = [(word, count) for (word, pos), count in morph_counter]

    # 서술어 추출
    predicates = []

    for i in range(1, len(pos_list)):
        if "EF" in pos_list[i][1]:
            if pos_list[i - 1][1].startswith("N"):
                predicates.append(pos_list[i][0])

            else:
                predicates.append(pos_list[i - 1][0] + pos_list[i][0])


    hesitant_endings = [word for word in predicates if word in ['같은데', '같아요', '같습니다', '듯 합니다', '느낌이에요']]


    await database.insert_document(database.answers_collection,
                                   {"lexical_analysis": final_result, "endings_analysis": hesitant_endings})

    return final_result, hesitant_endings



