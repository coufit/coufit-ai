import sys
from pathlib import Path

import pymysql

if __package__ in {None, ""}:
    sys.path.append(str(Path(__file__).resolve().parent.parent))

from db.config import get_pymysql_connection_kwargs

conn = pymysql.connect(**get_pymysql_connection_kwargs())
cursor = conn.cursor()

sql_list = [
    """
    CREATE TABLE IF NOT EXISTS region_category (
        id BIGINT PRIMARY KEY AUTO_INCREMENT,
        parent_id BIGINT,
        name VARCHAR(20)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS store (
        id BIGINT PRIMARY KEY AUTO_INCREMENT,
        name VARCHAR(50),
        store_number VARCHAR(30),
        category_code INT,
        category_name VARCHAR(50),
        address VARCHAR(200),
        latitude DOUBLE,
        longitude DOUBLE,
        region_category_id BIGINT,
        open_time TIME,
        close_time TIME,
        phone_number VARCHAR(30),
        FOREIGN KEY(region_category_id) REFERENCES region_category(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS store_image (
        id BIGINT PRIMARY KEY AUTO_INCREMENT,
        store_id BIGINT,
        image_url VARCHAR(255),
        created_at DATETIME,
        FOREIGN KEY(store_id) REFERENCES store(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS store_discount (
        id BIGINT PRIMARY KEY AUTO_INCREMENT,
        store_id BIGINT,
        title VARCHAR(50),
        description VARCHAR(200),
        discount_rate INT,
        start_time DATETIME,
        end_time DATETIME,
        created_at DATETIME,
        FOREIGN KEY(store_id) REFERENCES store(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS user (
        id BIGINT PRIMARY KEY AUTO_INCREMENT,
        email VARCHAR(30),
        password VARCHAR(30),
        name VARCHAR(10),
        created_at DATETIME
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS point (
        id BIGINT PRIMARY KEY AUTO_INCREMENT,
        point_balance INT,
        updated_at DATETIME,
        expired_at DATETIME,
        user_id BIGINT,
        FOREIGN KEY(user_id) REFERENCES user(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS payment_history (
        id BIGINT PRIMARY KEY AUTO_INCREMENT,
        amount INT,
        paid_at DATETIME,
        user_id BIGINT,
        store_id BIGINT,
        FOREIGN KEY(user_id) REFERENCES user(id),
        FOREIGN KEY(store_id) REFERENCES store(id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS charge_history (
        id BIGINT PRIMARY KEY AUTO_INCREMENT,
        user_id BIGINT,
        amount INT,
        payment_method ENUM('CARD','BANK','CASH'),
        charged_at DATETIME,
        FOREIGN KEY(user_id) REFERENCES user(id)
    )
    """,
]

for sql in sql_list:
    cursor.execute(sql)

cursor.close()
conn.close()

print("All tables created successfully.")
