import os
import sys

import pytest

from main import db as _db, app as _app
from database import drop_all, create_all

if os.getenv('FLASK_ENV') != 'test':
    print('Tests should be run with "FLASK_ENV=test"')
    sys.exit(1)


@pytest.fixture(scope='session', autouse=True)
def db(request):
    # create tables in testing database
    create_all()

    def teardown():
        # drop tables after finishing test cases
        drop_all()

    request.addfinalizer(teardown)


@pytest.fixture(scope='session', autouse=True)
def app(request):
    ctx = _app.test_request_context()
    ctx.push()

    def teardown():
        ctx.pop()

    request.addfinalizer(teardown)
    return app


@pytest.fixture(scope='function', autouse=True)
def session(request):
    """Create a test session to connect to database"""
    connection = _db.engine.connect()
    transaction = connection.begin()
    options = dict(bind=connection, binds={})
    session = _db.create_scoped_session(options=options)

    _db.session = session

    def teardown():
        session.close()
        transaction.rollback()
        connection.close()

    request.addfinalizer(teardown)
    return session
