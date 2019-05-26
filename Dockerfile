FROM tiangolo/uwsgi-nginx-flask:python3.7

ENV FLASK_ENV=production

RUN apt-get update
RUN apt-get -y install default-libmysqlclient-dev || apt-get -y install libmysqlclient-dev

ADD ./requirements.txt /soundchat-server/requirements.txt

WORKDIR /soundchat-server

COPY ./main ./main
COPY ./run.py ./run.py
COPY ./manage.py ./manage.py
COPY ./database.py ./database.py
COPY ./start_server.sh ./start_server.sh

RUN pip install -r requirements.txt

RUN chmod +x ./start_server.sh

CMD python database.py

CMD ./start_server.sh