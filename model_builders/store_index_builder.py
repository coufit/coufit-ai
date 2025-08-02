import pandas as pd
import numpy as np
import faiss
from sklearn.preprocessing import OneHotEncoder, StandardScaler, MinMaxScaler
from datetime import datetime
from db.connection import get_engine
import joblib

def build_store_index():
    engine = get_engine()
    now = datetime.now()

    # 1) Store 기본정보 + 집계 쿼리로 한 번에 가져오기
    store_df = pd.read_sql("""
        SELECT 
            s.id, s.category_code, s.latitude, s.longitude,
            IFNULL(p.total_sales, 0) AS total_sales,
            IFNULL(p.avg_amount, 0) AS avg_amount,
            IFNULL(p.user_count, 0) AS user_count
        FROM Store s
        LEFT JOIN (
            SELECT 
                store_id,
                SUM(amount) AS total_sales,
                AVG(amount) AS avg_amount,
                COUNT(DISTINCT user_id) AS user_count
            FROM PaymentHistory
            GROUP BY store_id
        ) p ON s.id = p.store_id
        WHERE s.latitude IS NOT NULL AND s.longitude IS NOT NULL
    """, con=engine)

    # 2) 기존 할인정보는 제외한다고 가정

    # 3) category one-hot 인코딩
    encoder = OneHotEncoder(sparse_output=False)
    cat_vec = encoder.fit_transform(store_df[['category_code']])

    # 4) 위도, 경도 정규화
    scaler_loc = StandardScaler()
    loc_vec = scaler_loc.fit_transform(store_df[['latitude', 'longitude']])

    # 5) 추가 숫자형 feature 정규화 (total_sales, avg_amount, user_count)
    scaler_extra = MinMaxScaler()
    extra_features = store_df[['total_sales', 'avg_amount', 'user_count']]
    extra_vec = scaler_extra.fit_transform(extra_features)

    # 6) 전체 벡터 결합 (9 + 2 + 3 = 14)
    vectors = np.hstack([cat_vec, loc_vec, extra_vec]).astype('float32')

    # 7) faiss 인덱스 생성 및 저장
    # (1) 벡터 중복 제거
    vectors_unique, unique_indices = np.unique(vectors, axis=0, return_index=True)
    store_df_unique = store_df.iloc[unique_indices]

    # (2) FAISS 인덱스 생성
    index = faiss.IndexFlatL2(vectors_unique.shape[1])
    index.add(vectors_unique.astype('float32'))

    # (3) 저장
    faiss.write_index(index, "model/store.index")
    joblib.dump(store_df_unique['id'].tolist(), "model/store_id_map.pkl")
    joblib.dump(encoder, "model/store_encoder.pkl")
    joblib.dump(scaler_loc, "model/store_scaler_loc.pkl")
    joblib.dump(scaler_extra, "model/store_scaler_extra.pkl")

    print("Store FAISS index 및 관련 객체 저장 완료")


if __name__ == "__main__":
    build_store_index()