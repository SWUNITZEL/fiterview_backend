FROM python:3.12



# 작업 디렉토리 설정
WORKDIR /code

# ./requirements.txt 를 /code/requirements.txt 로 복사
COPY ./requirements.txt /code/requirements.txt

# requirements.txt 를 보고 모듈 전체 설치(-r)
RUN pip install --no-cache-dir -r /code/requirements.txt
RUN pip install requests

# mecab 설치
RUN apt-get update && apt-get install -y \
    mecab \
    libmecab-dev \
    mecab-ipadic-utf8 \
    curl \
    git \
    gcc \
    poppler-utils \
    libgl1-mesa-glx

RUN pip install konlpy mecab-python3

# 애플리케이션 코드 복사
COPY ./app /code/app

# 실행
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
