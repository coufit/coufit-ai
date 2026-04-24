# COUFIT AI Server

COUFIT AI Server는 COUFIT 서비스의 AI 백엔드 레포지토리입니다.
FastAPI 기반으로 동작하며, 사용자 결제 이력 기반 가맹점 추천과 Qwen 기반 자연어 응답 기능을 제공합니다.

서버가 시작되면 추천 인덱스를 빌드하고, 사용자 벡터를 생성한 뒤, LLM 서비스를 초기화합니다.

## 주요 기능

- `FAISS` 기반 유사도 검색으로 가맹점 추천 제공
- 사용자 소비 패턴과 위치 정보 기반 추천 결과 반환
- `Qwen2.5-3B-Instruct` 기반 추천 설명 생성
- 일반 텍스트 생성 및 컨텍스트 포함 응답 API 제공
- `/health`, `/llm/health` 기반 상태 점검 지원

## 기술 스택

- Python
- FastAPI
- SQLAlchemy / PyMySQL
- Pandas / NumPy / scikit-learn
- FAISS
- Hugging Face Transformers
- PyTorch

## 디렉터리 구조

- `api/`: FastAPI 라우터
- `data/`: 원본 데이터와 전처리 결과
- `data_ingestion/`: 데이터 전처리 스크립트
- `db/`: 테이블 생성, 데이터 적재, DB 연결
- `model/`: 생성된 인덱스와 학습 산출물
- `model_builders/`: 추천 인덱스, 사용자 벡터, LLM 로더
- `services/`: 추천 및 LLM 서비스 로직
- `main.py`: 서버 진입점
- `requirements.txt`: Python 의존성 목록

## 실행 전 준비

### 1. 가상환경 생성 및 의존성 설치

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
pip install -r requirements.txt
```

macOS / Linux:

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

참고:

- 현재 `requirements.txt`에는 `torch==2.7.1+cu118`이 고정되어 있습니다.
- GPU/CUDA 환경이 아니면 PyTorch 설치 방식은 개발 환경에 맞게 조정이 필요할 수 있습니다.

### 2. 환경 변수 설정

프로젝트 루트에 `.env` 파일을 직접 생성한 뒤, 환경에 맞는 실제 값을 입력합니다.

주요 DB 환경 변수 예시:

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=coufit
DB_CHARSET=utf8mb4
DB_AUTOCOMMIT=true
DB_LOCAL_INFILE=true
```

참고:

- 위 값은 로컬 개발 환경 기준 예시입니다.
- 실제 운영 환경에서는 DB 호스트, 계정, 비밀번호를 환경에 맞게 별도로 설정해야 합니다.
- `.env`가 없으면 기존 개발 환경과의 호환을 위해 기본값이 사용됩니다.
- 운영 환경에서는 반드시 실제 값을 환경 변수 또는 `.env`로 주입하는 편이 안전합니다.

### 3. MySQL 실행

예시:

```bash
docker run --name coufit-mysql ^
  -e MYSQL_ROOT_PASSWORD=1234 ^
  -e MYSQL_DATABASE=coufit ^
  -p 3306:3306 ^
  -d mysql:8.4.5
```

## 데이터 및 추천 모델 준비

### 1. 원본 데이터 확인

기본 원본 파일 경로:

```text
data/raw/지역화폐 가맹점 현황_20250516.csv
```

### 2. 전처리

```bash
python data_ingestion/preprocess_store_data.py
```

생성 파일:

```text
data/preprocessed/store_preprocessed.csv
```

### 3. 테이블 생성

```bash
python db/create_tables.py
```

### 4. MySQL `local_infile` 활성화

`LOAD DATA LOCAL INFILE`을 사용하므로 MySQL에서 아래 설정이 필요합니다.

```sql
SET GLOBAL local_infile = 1;
```

### 5. 데이터 적재

```bash
python db/insert_store_data.py
```

### 6. 추천 인덱스 및 사용자 벡터 생성

서버 시작 시 자동 실행되지만, 필요하면 개별 실행도 가능합니다.

```bash
python model_builders/store_index_builder.py
python model_builders/user_vector_builder.py
```

생성 산출물:

- `model/store.index`
- `model/store_info.pkl`
- `model/store_encoder.pkl`
- `model/store_scaler_loc.pkl`
- `model/store_scaler_extra.pkl`
- `model/user_id_map.pkl`
- `model/user_pattern_vectors.npy`

## 서버 실행

```bash
uvicorn main:app --reload
```

기본 주소:

- API: `http://127.0.0.1:8000`
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## 서버 시작 시 수행되는 작업

`main.py` 기준으로 서버 부팅 시 아래 작업이 실행됩니다.

1. `build_store_index()`
2. `build_user_vectors()`
3. `initialize_llm_service()`

즉, 추천 인덱스가 준비되지 않았더라도 서버 시작 과정에서 자동 생성됩니다.

## API 요약

### 공통

- `GET /`
- `GET /health`
- `GET /llm/health`

### 추천 API

#### `POST /recommend/top-stores`

기본 추천 결과만 반환합니다.

요청 예시:

```json
{
  "user_id": 1,
  "user_lat": 37.5665,
  "user_lon": 126.9780,
  "k": 10
}
```

응답 예시:

```json
{
  "recommendations": [
    {
      "id": 101,
      "name": "sample store",
      "category": "food",
      "distance": 0.1234
    }
  ]
}
```

#### `POST /recommend/with-llm`

추천 결과와 함께 LLM이 생성한 설명 문장을 반환합니다.

요청 형식은 `/recommend/top-stores`와 동일합니다.

### LLM API

#### `POST /llm/chat`

일반 텍스트 응답 생성 API입니다.

요청 예시:

```json
{
  "prompt": "오늘 점심 추천해줘",
  "max_tokens": 100,
  "temperature": 0.7,
  "top_p": 0.9,
  "top_k": 50
}
```

#### `POST /llm/chat-with-context`

외부 컨텍스트를 함께 전달하는 응답 생성 API입니다.

요청 예시:

```json
{
  "user_message": "이 추천 결과를 설명해줘",
  "context": "1. A식당 (한식)\n2. B카페 (카페)",
  "max_tokens": 200
}
```

#### `POST /llm/generate`

단순 텍스트 생성용 엔드포인트입니다.

## LLM 설정

LLM 로더는 기본적으로 아래 값을 사용합니다.

- 모델: `Qwen/Qwen2.5-3B-Instruct`
- CUDA 사용 가능 시 GPU 우선
- 환경 변수로 일부 옵션 변경 가능

지원하는 주요 환경 변수:

- `MODEL_NAME`
- `HF_CACHE_DIR`
- `HF_LOCAL_ONLY`
- `LOAD_IN_4BIT`
- `LOAD_IN_8BIT`
- `DEVICE_MAP`
- `TORCH_NUM_THREADS`

예시:

```bash
set MODEL_NAME=Qwen/Qwen2.5-3B-Instruct
set HF_LOCAL_ONLY=0
set LOAD_IN_4BIT=0
```

macOS / Linux:

```bash
export MODEL_NAME=Qwen/Qwen2.5-3B-Instruct
export HF_LOCAL_ONLY=0
export LOAD_IN_4BIT=0
```

## 현재 코드 기준 운영 메모

- 추천 서비스는 MySQL 데이터와 `model/` 산출물에 의존합니다.
- DB 연결 정보는 `.env` 또는 환경 변수로 주입할 수 있습니다.
- `.env`가 없으면 기본 개발값으로 동작합니다.
- CORS는 현재 모든 Origin을 허용하도록 설정되어 있습니다.
- 서버 기동 시 인덱스 빌드와 LLM 초기화가 함께 실행되므로 첫 실행 시간이 길 수 있습니다.

## 추천 개발 개선 포인트

- DB 연결 실패 시 더 명확한 에러 메시지 제공
- 앱 전체 설정을 하나의 config 계층으로 통합
- 개발/운영 환경별 CORS 분리
- 모델 초기화 옵션 문서화 및 배포 전략 정리
- 인덱스 재생성 여부를 제어하는 배치 분리
