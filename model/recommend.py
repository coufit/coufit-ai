import faiss
import numpy as np
import joblib

# 로딩
index = faiss.read_index("recommend/merchant.index")
id_map = joblib.load("recommend/id_map.pkl")
encoder = joblib.load("recommend/encoder.pkl")
scaler = joblib.load("recommend/scaler.pkl")

def get_user_vector(category_code: str, lat: float, lon: float) -> np.ndarray:
    cat_vec = encoder.transform([[category_code]])
    loc_vec = scaler.transform([[lat, lon]])
    return np.hstack([cat_vec, loc_vec]).astype("float32")

def recommend_merchants(category_code: str, lat: float, lon: float, top_k=5):
    user_vec = get_user_vector(category_code, lat, lon)
    D, I = index.search(user_vec, top_k)
    return [id_map[i] for i in I[0]]
