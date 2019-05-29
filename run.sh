#!/bin/bash

./wait-for-it.sh soundchat-mysql:3306 --timeout=60 -- python manage.py db upgrade;

init_db() {
  python manage.py db migrate;
  python manage.py db upgrade;
}

init_db
/start.sh