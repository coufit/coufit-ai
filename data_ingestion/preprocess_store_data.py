import pandas as pd
import random

# 원본 CSV 읽기
df = pd.read_csv('data/raw/지역화폐 가맹점 현황_20250516.csv')

# 시군명이 '시흥시'인 행만 필터
df = df[df['시군명'] == '시흥시'].copy()

# 업종명 간단화 매핑
mapping_dict = {
    'd.음식점업': '음식점',
    'e.교육서비스업': '교육',
    'h.개인서비스업': '미용',
    'b.소매업': '마트',
    'g.스포츠및여가관련서비스업': '스포츠',
    'f.보건업': '의료',
    'a.제조업': '제조',
    'c.숙박업': '숙박',
    'i.기타': '잡화',
    'B.소매업': '마트'
}

# 간단 업종명 ➝ 4자리 코드 매핑
category_code_dict = {
    '음식점': 1001,
    '교육': 1002,
    '미용': 1003,
    '마트': 1004,
    '스포츠': 1005,
    '의료': 1006,
    '제조': 1007,
    '숙박': 1008,
    '잡화': 1009,
    '기타': 9999
}

# 간단 업종명 생성
df['category_name'] = df['업종명(종목명)'].map(mapping_dict).fillna('기타')

# 숫자 코드 생성 (int로 명확하게 지정!)
df['category_code'] = df['category_name'].map(category_code_dict).fillna(9999).astype(int)

# 기타 필드 생성
df['open_time'] = [random.choice(['08:00:00', '09:00:00', '10:00:00', '11:00:00', '12:00:00']) for _ in range(len(df))]
df['close_time'] = [random.choice(['19:00:00','20:00:00', '21:00:00', '22:00:00', '23:00:00']) for _ in range(len(df))]
df['phone_number'] = ['010-%04d-%04d' % (random.randint(0, 9999), random.randint(0, 9999)) for _ in range(len(df))]

# 주소
df['address'] = df.apply(
    lambda row: row['소재지도로명주소'] if isinstance(row['소재지도로명주소'], str) and row['소재지도로명주소'] else row['소재지지번주소'],
    axis=1
)

# 최종 정리
df_final = df[['상호명', '가맹점번호', 'category_code', 'category_name', 'address', '위도', '경도', 'open_time', 'close_time', 'phone_number']]

# 컬럼명 변경
df_final.columns = [
    'name',
    'store_number',
    'category_code',
    'category_name',
    'address',
    'latitude',
    'longitude',
    'open_time',
    'close_time',
    'phone_number'
]

# 저장
save_path = 'data/preprocessed/store_preprocessed.csv'
df_final.to_csv(save_path, index=False, encoding='utf-8')
print(f'완성 CSV 저장됨: {save_path}')
