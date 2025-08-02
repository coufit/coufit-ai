import pandas as pd
import numpy as np
import faiss
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from db.connection import get_engine
import joblib

# DB에서 가맹점 데이터 불러오기
engine = get_engine()
df = pd.read_sql("SELECT * FROM merchants", con=engine)

# 전처리: 필요한 컬럼만 사용
df = df[['merchant_id', 'category_code', 'latitude', 'longitude']]
df = df.dropna()

# 1. One-hot encode 업종코드
encoder = OneHotEncoder(sparse=False)
cat_vec = encoder.fit_transform(df[['category_code']])

# 2. 위치 정규화
scaler = StandardScaler()
loc_vec = scaler.fit_transform(df[['latitude', 'longitude']])

# 3. 벡터 결합
vectors = np.hstack([cat_vec, loc_vec]).astype('float32')

# 4. FAISS 인덱스 생성
index = faiss.IndexFlatL2(vectors.shape[1])
index.add(vectors)

# 5. 저장
faiss.write_index(index, "recommend/merchant.index")
joblib.dump(df["merchant_id"].tolist(), "recommend/id_map.pkl")
joblib.dump(encoder, "recommend/encoder.pkl")
joblib.dump(scaler, "recommend/scaler.pkl")
