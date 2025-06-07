FROM python:3.12



# 작업 디렉토리 설정
WORKDIR /code

# ./requirements.txt 를 /code/requirements.txt 로 복사
COPY ./requirements.txt /code/requirements.txt


RUN apt-get update && apt-get install -y \
    curl \
    git \
    gcc \
    poppler-utils \
    libgl1-mesa-glx

# OpenJDK 17 수동 설치 (aarch64 호환)
RUN mkdir -p /usr/lib/jvm && \
    wget https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.10+7/OpenJDK17U-jdk_aarch64_linux_hotspot_17.0.10_7.tar.gz && \
    tar -xzf OpenJDK17U-jdk_aarch64_linux_hotspot_17.0.10_7.tar.gz -C /usr/lib/jvm && \
    rm OpenJDK17U-jdk_aarch64_linux_hotspot_17.0.10_7.tar.gz

ENV JAVA_HOME=/usr/lib/jvm/jdk-17
ENV PATH="${JAVA_HOME}/bin:${PATH}"

# 애플리케이션 코드 복사
COPY ./app /code/app

# 실행
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
