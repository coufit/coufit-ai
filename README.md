프로젝트 환경 세팅 순서
1. 가상환경 생성
python -m venv .venv
2. 가상환경 활성화
Windows
.venv\Scripts\activate

macOS / Linux
source .venv/bin/activate
가상환경이 활성화되면 터미널 앞에 (venv)가 표시됩니다.

3. 필수 패키지 설치
pip install -r requirements.txt

4. docker DB서버 생성
docker run --name coufit-mysql -e MYSQL_ROOT_PASSWORD=1234 -e MYSQL_DATABASE=coufit -e MYSQL_USER=coufit -e MYSQL_PASSWORD=coufit_98 -p 3306:3306 -d mysql:8.4.5

5. DB 테이블 생성 및 데이터 삽입
python data_ingestion/preprocess_store_data.py (raw데이터 가공)
python db/create_tables.py (테이블 생성)
SET GLOBAL local_infile = 1; (LOAD DATA LOCAL INFILE 기능 활성화 [root 계정 사용])
python db/insert_store_data.py (데이터 삽입)
