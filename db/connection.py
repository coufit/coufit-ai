from sqlalchemy import create_engine

def get_engine():
    # 여기에 여러분의 실제 데이터베이스 접속 URL 넣기
    db_url = "mysql+pymysql://root:1234@localhost:3306/coufit"
    engine = create_engine(db_url)
    return engine
