from sqlalchemy import create_engine

from main.cfg import config
from main import db

engine = create_engine(config.SQLALCHEMY_DATABASE_URI)


def drop_all():
    db.drop_all()


def create_all():
    db.create_all()


if __name__ == '__main__':
    """create database schema"""
    create_all()
