import pandas as pd
import numpy as np
import faiss
from sklearn.preprocessing import OneHotEncoder, StandardScaler, MinMaxScaler
from datetime import datetime
from db.connection import get_engine
import joblib
import os

def build_store_index():
    engine = get_engine()
    now = datetime.now()

    os.makedirs("model", exist_ok=True)

    # 1️⃣ Store 기본정보 + 집계 쿼리
    store_df = pd.read_sql("""
        SELECT 
            s.id, s.name, s.category_name, s.latitude, s.longitude,
            IFNULL(p.total_sales, 0) AS total_sales,
            IFNULL(p.avg_amount, 0) AS avg_amount,
            IFNULL(p.user_count, 0) AS user_count
        FROM store s
        LEFT JOIN (
            SELECT 
                store_id,
                SUM(amount) AS total_sales,
                AVG(amount) AS avg_amount,
                COUNT(DISTINCT user_id) AS user_count
            FROM payment_history
            GROUP BY store_id
        ) p ON s.id = p.store_id
        WHERE s.latitude IS NOT NULL AND s.longitude IS NOT NULL
    """, con=engine)
    
    if store_df.empty:
        raise ValueError("❌ store 테이블이 비어 있습니다. 인덱스를 생성할 수 없습니다.")

    # 2️⃣ 카테고리 원-핫 인코딩
    encoder = OneHotEncoder(sparse_output=False)
    cat_vec = encoder.fit_transform(store_df[['category_name']])

    # 3️⃣ 위도/경도 정규화
    scaler_loc = StandardScaler()
    loc_vec = scaler_loc.fit_transform(store_df[['latitude', 'longitude']])

    # 4️⃣ 추가 numeric feature 정규화
    scaler_extra = MinMaxScaler()
    extra_vec = scaler_extra.fit_transform(store_df[['total_sales', 'avg_amount', 'user_count']])

    # 5️⃣ 전체 feature 결합
    vectors = np.hstack([cat_vec, loc_vec, extra_vec]).astype('float32')

    # 6️⃣ 중복 제거
    vectors_unique, unique_indices = np.unique(vectors, axis=0, return_index=True)
    store_df_unique = store_df.iloc[unique_indices].reset_index(drop=True)

    # 7️⃣ FAISS 인덱스 생성
    index = faiss.IndexFlatL2(vectors_unique.shape[1])
    index.add(vectors_unique)

    # 8️⃣ 파일 저장
    faiss.write_index(index, "model/store.index")
    joblib.dump(encoder, "model/store_encoder.pkl")
    joblib.dump(scaler_loc, "model/store_scaler_loc.pkl")
    joblib.dump(scaler_extra, "model/store_scaler_extra.pkl")

    # 🔹 (추가) store_info.pkl 저장 (id, name, category 포함)
    store_info = [
        {"id": int(row["id"]), "name": str(row["name"]), "category": row["category_name"]}
        for _, row in store_df_unique.iterrows()
    ]
    joblib.dump(store_info, "model/store_info.pkl")

    print(f"✅ {len(store_info)}개 매장 인덱스 저장 완료 (store_info.pkl 포함)")
    print(" - model/store.index")
    print(" - model/store_info.pkl")
    print(" - model/store_encoder.pkl")
    print(" - model/store_scaler_loc.pkl")
    print(" - model/store_scaler_extra.pkl")


if __name__ == "__main__":
    build_store_index()
