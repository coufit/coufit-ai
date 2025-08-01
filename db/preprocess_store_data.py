import pandas as pd
import random

# 원본 CSV 읽기
df = pd.read_csv('data/raw/지역화폐 가맹점 현황_20250516.csv')

# open_time, close_time, phone_number 임의값 생성
df['open_time'] = [random.choice(['08:00:00', '09:00:00', '10:00:00']) for _ in range(len(df))]
df['close_time'] = [random.choice(['20:00:00', '21:00:00', '22:00:00']) for _ in range(len(df))]
df['phone_number'] = ['010-%04d-%04d' % (random.randint(0,9999), random.randint(0,9999)) for _ in range(len(df))]

# 도로명 주소 없으면 지번주소로 채우기 (address 컬럼)
df['address'] = df.apply(
    lambda row: row['소재지도로명주소'] if isinstance(row['소재지도로명주소'], str) and row['소재지도로명주소'] else row['소재지지번주소'], axis=1
)

# DB 테이블에 들어갈 컬럼 순서로만 남기기
df_final = df[['상호명', '가맹점번호', '업종코드', '업종명(종목명)', 'address', '위도', '경도', 'open_time', 'close_time', 'phone_number']]

# 컬럼명을 DB 컬럼과 맞추고 싶으면(선택)
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

# 최종 csv로 저장 (헤더O, utf-8, index 없이)
save_path = 'data/preprocessed/store_preprocessed.csv'
df_final.to_csv(save_path, index=False, encoding='utf-8')
print(f'완성 CSV 저장됨: {save_path}')
