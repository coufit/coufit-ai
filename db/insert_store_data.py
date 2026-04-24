import sys
from pathlib import Path

import pymysql

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parent.parent))

from db.config import BASE_DIR, get_pymysql_connection_kwargs

conn = pymysql.connect(**get_pymysql_connection_kwargs())
cursor = conn.cursor()

csv_path = (BASE_DIR / "data" / "preprocessed" / "store_preprocessed.csv").resolve()

cursor.execute("""
INSERT INTO region_category (id, parent_id, name) VALUES
(1, NULL, '경기도'),
(2, 1, '시흥시')
ON DUPLICATE KEY UPDATE name = VALUES(name)
""")

sql = f"""
LOAD DATA LOCAL INFILE '{csv_path.as_posix()}'
INTO TABLE store
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

print(f"Store data loaded successfully from {csv_path.name}.")
