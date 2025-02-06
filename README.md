- 깃허브 readme에 테스트 방법 작성
    
- 개발 현황
    - 데이터
        - 음식테마거리 데이터 정제 (요약 + 마크다운형식) 후 `data/food/음식테마거리`에 CSV 형태로 저장
        - `scripts/create_restaurant_vectordb.py`로 `vectordb/restaurant finder`에 벡터DB 저장
    - 라우팅 설정
        - `routers/restaurant.py`에서 API 통신을 위한 URL을 설정
    - 특정 벡터DB와 프롬프트 사용
        - 벡터DB 로드를 위해 정의했던 `utils/vectordb.py`를 `services/base.py`에서 Import하여 RAG 준비
        - `services/restaurant.py`에서 `services/base.py`를 Import하고 디자인한 프롬프트를 적용하여 벡엔드로 보낼 데이터를 생성
    - 테스트
        1. `tests/test_api.py`를 실행하여 테스트 가능
- 개발 계획
    - 서버
        - 두가지 방법
            1. 두 개의 서로 다른 AWS 인스턴스로 AI, 벡엔드 서버를 각 각 구축 후 통신
            2. 하나의 AWS 인스턴스로 AI서비스는 Localhost에서 실행 & 벡엔드 서버로 사용
    - 데이터
        - 다른 domain의 데이터도 {요약 + 마크다운} 형식 데이터로 정제하여 벡터DB 생성 및 서비스 구축
    - 서비스
        - 퍼블리싱 작업물 확인 후 서비스 FLOW를 다시 분석하며, AI가 사용되는 부분을 정리
        - 사용되어야하는 데이터와 프롬프트 정리하면서 서비스 구축