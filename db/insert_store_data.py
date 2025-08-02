import pymysql

conn = pymysql.connect(
    host='localhost',
    user='root',
    password='1234',
    db='coufit',
    charset='utf8',
    autocommit=True,
    local_infile=1
)
cursor = conn.cursor()

# 1) RegionCategory 필요한 데이터 먼저 넣기
cursor.execute("""
INSERT INTO RegionCategory (id, parent_id, name) VALUES
(1, NULL, '경기도'),
(2, 1, '시흥시')
ON DUPLICATE KEY UPDATE name = VALUES(name)
""")

# 2) Store 테이블에 CSV 데이터 적재
sql = """
LOAD DATA LOCAL INFILE 'data/preprocessed/store_preprocessed.csv'
INTO TABLE Store
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(name, store_number, category_code, category_name, address, latitude, longitude, open_time, close_time, phone_number)
SET region_category_id = 2
"""

cursor.execute(sql)
conn.commit()

cursor.close()
conn.close()
print('RegionCategory 데이터 삽입 및 Store LOAD DATA 적재 완료!')
