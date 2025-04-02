FROM python:3.12

# 작업 디렉토리 설정
WORKDIR /code

# ./requirements.txt 를 /code/requirements.txt 로 복사
COPY ./requirements.txt /code/requirements.txt

# requirements.txt 를 보고 모듈 전체 설치(-r)
RUN pip install --no-cache-dir -r /code/requirements.txt

# 애플리케이션 코드 복사
COPY ./app /code/app

# 실행
CMD ["python", "main.py"]