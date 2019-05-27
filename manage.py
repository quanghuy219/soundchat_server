from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand

from main import app, models
from main import db
from database import drop_all, create_all


migrate = Migrate(app, db)
manager = Manager(app)
manager.add_command('db', MigrateCommand)


def _make_context():
    return dict(app=app, db=db, models=models)


manager.add_command('shell', Shell(make_context=_make_context))


@manager.command
def create_tables():
    create_all()


@manager.command
def drop_tables():
    drop_all()


if __name__ == '__main__':
    manager.run()
