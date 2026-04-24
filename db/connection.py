from sqlalchemy import create_engine

from db.config import get_sqlalchemy_url


def get_engine():
    return create_engine(get_sqlalchemy_url())
