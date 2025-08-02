import pymysql

# MySQL 연결 정보 입력
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

# 스네이크 케이스로 변경된 테이블 및 컬럼명
sql_list = [

    # 지역 카테고리
    """
    CREATE TABLE IF NOT EXISTS region_category (
        id BIGINT PRIMARY KEY AUTO_INCREMENT,
        parent_id BIGINT,
        name VARCHAR(20)
    )
    """,

    # 가맹점
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

    # 가맹점 이미지
    """
    CREATE TABLE IF NOT EXISTS store_image (
        id BIGINT PRIMARY KEY AUTO_INCREMENT,
        store_id BIGINT,
        image_url VARCHAR(255),
        created_at DATETIME,
        FOREIGN KEY(store_id) REFERENCES store(id)
    )
    """,

    # 가맹점 할인
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

    # 유저
    """
    CREATE TABLE IF NOT EXISTS user (
        id BIGINT PRIMARY KEY AUTO_INCREMENT,
        email VARCHAR(30),
        password VARCHAR(30),
        name VARCHAR(10),
        created_at DATETIME
    )
    """,

    # 포인트
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

    # 소비내역
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

    # 충전내역
    """
    CREATE TABLE IF NOT EXISTS charge_history (
        id BIGINT PRIMARY KEY AUTO_INCREMENT,
        user_id BIGINT,
        amount INT,
        payment_method ENUM('CARD','BANK','CASH'),
        charged_at DATETIME,
        FOREIGN KEY(user_id) REFERENCES user(id)
    )
    """
]

# 순서대로 테이블 생성 실행
for sql in sql_list:
    cursor.execute(sql)

cursor.close()
conn.close()

print("모든 테이블 생성이 완료되었습니다.")
