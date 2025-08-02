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

# 테이블 생성 SQL 리스트 (모든 id 컬럼에 AUTO_INCREMENT 적용)
sql_list = [

    # 지역_카테고리
    """
    CREATE TABLE IF NOT EXISTS RegionCategory (
        id BIGINT PRIMARY KEY AUTO_INCREMENT,
        parent_id BIGINT,
        name VARCHAR(20)
    )
    """,

    # 가맹점
    """
    CREATE TABLE IF NOT EXISTS Store (
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
        FOREIGN KEY(region_category_id) REFERENCES RegionCategory(id)
    )
    """,

    # 가맹점_이미지
    """
    CREATE TABLE IF NOT EXISTS StoreImage (
        id BIGINT PRIMARY KEY AUTO_INCREMENT,
        store_id BIGINT,
        image_url VARCHAR(255),
        created_at DATETIME,
        FOREIGN KEY(store_id) REFERENCES Store(id)
    )
    """,

    # 가맹점_할인
    """
    CREATE TABLE IF NOT EXISTS StoreDiscount (
        id BIGINT PRIMARY KEY AUTO_INCREMENT,
        store_id BIGINT,
        title VARCHAR(50),
        description VARCHAR(200),
        discount_rate INT,
        start_time DATETIME,
        end_time DATETIME,
        created_at DATETIME,
        FOREIGN KEY(store_id) REFERENCES Store(id)
    )
    """,

    # 유저
    """
    CREATE TABLE IF NOT EXISTS User (
        id BIGINT PRIMARY KEY AUTO_INCREMENT,
        email VARCHAR(30),
        password VARCHAR(30),
        name VARCHAR(10),
        created_at DATETIME
    )
    """,

    # 포인트
    """
    CREATE TABLE IF NOT EXISTS Point (
        id BIGINT PRIMARY KEY AUTO_INCREMENT,
        point_balance INT,
        updated_at DATETIME,
        expired_at DATETIME,
        user_id BIGINT,
        FOREIGN KEY(user_id) REFERENCES User(id)
    )
    """,

    # 소비내역
    """
    CREATE TABLE IF NOT EXISTS PaymentHistory (
        id BIGINT PRIMARY KEY AUTO_INCREMENT,
        amount INT,
        paid_at DATETIME,
        user_id BIGINT,
        store_id BIGINT,
        FOREIGN KEY(user_id) REFERENCES User(id),
        FOREIGN KEY(store_id) REFERENCES Store(id)
    )
    """,

    # 충전내역
    """
    CREATE TABLE IF NOT EXISTS ChargeHistory (
        id BIGINT PRIMARY KEY AUTO_INCREMENT,
        user_id BIGINT,
        amount INT,
        payment_method ENUM('CARD','BANK','CASH'),
        charged_at DATETIME,
        FOREIGN KEY(user_id) REFERENCES User(id)
    )
    """
]

# 순서대로 테이블 생성 실행
for sql in sql_list:
    cursor.execute(sql)

cursor.close()
conn.close()

print("모든 테이블 생성이 완료되었습니다.")
