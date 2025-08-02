import numpy as np
import pandas as pd
import faiss
import joblib
from db.connection import get_engine
from sqlalchemy import text

def recommend_stores(user_id, user_lat, user_lon, k=10):
    engine = get_engine()

    # 1) 사용자 카테고리별 소비 비율
    sql_cat = text("""
        SELECT s.category_code, SUM(p.amount) as total_amount
        FROM PaymentHistory p
        JOIN Store s ON p.store_id = s.id
        WHERE p.user_id = :user_id
        GROUP BY s.category_code
    """)
    user_cat_df = pd.read_sql(sql_cat, con=engine, params={"user_id": user_id})

    if user_cat_df.empty:
        return []

    total = user_cat_df['total_amount'].sum()
    user_cat_df['ratio'] = user_cat_df['total_amount'] / total

    # 2) 사용자 총 결제액, 평균 결제금액 구하기 (예시)
    sql_user_extra = text("""
        SELECT 
            SUM(amount) as total_sales,
            AVG(amount) as avg_amount
        FROM PaymentHistory
        WHERE user_id = :user_id
    """)
    user_extra_df = pd.read_sql(sql_user_extra, con=engine, params={"user_id": user_id})

    user_total_sales = user_extra_df.at[0, 'total_sales'] if not user_extra_df.empty else 0
    user_avg_payment = user_extra_df.at[0, 'avg_amount'] if not user_extra_df.empty else 0
    user_count = 1  # 방문자 수는 매장 단위라 사용자엔 1로 고정

    # 3) 인코더, 스케일러, 인덱스 로드
    encoder = joblib.load("model/store_encoder.pkl")
    scaler_loc = joblib.load("model/store_scaler_loc.pkl")
    scaler_extra = joblib.load("model/store_scaler_extra.pkl")
    index = faiss.read_index("model/store.index")
    store_id_map = joblib.load("model/store_id_map.pkl")

    # 4) 사용자 카테고리 벡터 생성
    categories = encoder.categories_[0]
    user_cat_ratio = np.zeros(len(categories), dtype='float32')
    for i, cat in enumerate(categories):
        if cat in user_cat_df['category_code'].values:
            user_cat_ratio[i] = user_cat_df.loc[user_cat_df['category_code'] == cat, 'ratio'].values[0]

    # 5) 사용자 위치 정규화
    if user_lat is None or user_lon is None:
        user_loc_scaled = np.zeros(2, dtype='float32')
    else:
        user_loc_scaled = scaler_loc.transform(np.array([[user_lat, user_lon]]))[0].astype('float32')

    # 6) 사용자 extra feature 정규화
    user_extra_vec = scaler_extra.transform([[user_total_sales, user_avg_payment, user_count]])[0]

    # 7) 최종 user 벡터 생성
    user_vector = np.hstack([user_cat_ratio, user_loc_scaled, user_extra_vec]).reshape(1, -1)

    # 8) faiss 검색
    D, I = index.search(user_vector, k)

    # 9) 추천 결과 생성
    recommended_store_ids = [store_id_map[i] for i in I[0]]
    return recommended_store_ids
    # results = []
    # for store_id, dist in zip(recommended_store_ids, D[0]):
    #     results.append({"store_id": store_id, "distance": float(dist)})

    # return results

