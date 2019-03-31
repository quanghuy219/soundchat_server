from main import db
from main.models import *


def drop_all():
    db.drop_all()


def create_all():
    db.create_all()


if __name__ == '__main__':
    """create database schema"""
    create_all()
