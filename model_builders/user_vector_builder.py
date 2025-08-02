import pandas as pd
import numpy as np
from sklearn.preprocessing import OneHotEncoder
from db.connection import get_engine
import joblib

def build_user_vectors():
    engine = get_engine()

    # 1) User별 카테고리 소비 합계 (카테고리별 소비 비율 계산을 위한 집계)
    sql = """
    SELECT p.user_id, s.category_code, SUM(p.amount) as total_amount
    FROM PaymentHistory p
    JOIN Store s ON p.store_id = s.id
    GROUP BY p.user_id, s.category_code
    """
    payment_user_cat = pd.read_sql(sql, con=engine)

    # 2) 피벗테이블 : user_id x category_code (소비금액)
    pivot = payment_user_cat.pivot(index='user_id', columns='category_code', values='total_amount').fillna(0)

    # 3) 총 소비 대비 카테고리별 비율로 변환
    pivot = pivot.div(pivot.sum(axis=1), axis=0).fillna(0)

    # 4) 카테고리 one-hot encoder (store index와 동일한 encoder 써야 함)
    encoder = joblib.load("model/store_encoder.pkl")

    encoded_categories = list(encoder.categories_[0])
    missing_cols = set(encoded_categories) - set(pivot.columns)
    for mc in missing_cols:
        pivot[mc] = 0

    pivot = pivot[encoded_categories]  # 컬럼 순서 맞춤

    # 5) 위치 관련 부분 제거 (이전 location_df, scaler_loc 제거)

    # 6) 유저 소비 카테고리 비율 벡터 생성 (float32)
    user_vectors = pivot.values.astype('float32')

    # 7) id 리스트 별도 저장
    user_ids = pivot.index.tolist()

    # 8) 저장 (id map + user 소비 패턴 벡터)
    joblib.dump(user_ids, "model/user_id_map.pkl")
    np.save("model/user_pattern_vectors.npy", user_vectors)

    print("User pattern vectors 생성 및 저장 완료")

if __name__ == "__main__":
    build_user_vectors()