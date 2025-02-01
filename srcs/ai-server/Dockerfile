# 베이스 이미지로 python:3.9-slim 사용
FROM python:3.9-slim

# 작업 디렉토리 생성 및 설정
WORKDIR /app

# 종속성 설치를 위해 requirements.txt 복사 및 설치
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# 애플리케이션 코드 복사
# COPY ./app /app

COPY entrypoint.sh /home/entrypoint.sh
RUN chmod +x /home/entrypoint.sh

# 컨테이너의 8000 포트를 외부에 노출
EXPOSE 8000

ENTRYPOINT [ "/home/entrypoint.sh" ]
