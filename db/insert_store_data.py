import pymysql

conn = pymysql.connect(
    host='localhost',
    user='root',
    password='1234',
    db='coufit',
    charset='utf8',
    autocommit=True,
    local_infile=1     # 이 부분 반드시 켜기!
)
cursor = conn.cursor()

sql = """
LOAD DATA LOCAL INFILE 'data/preprocessed/store_preprocessed.csv'
INTO TABLE Store
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 LINES
(name, store_number, category_code, category_name, address, latitude, longitude, open_time, close_time, phone_number)
"""

cursor.execute(sql)
conn.commit()
cursor.close()
conn.close()
print('LOAD DATA INFILE로 초고속 데이터 적재 완료!')
