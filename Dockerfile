FROM tiangolo/uwsgi-nginx-flask:python3.7

ENV FLASK_ENV=production

RUN apt-get update
RUN apt-get -y install default-libmysqlclient-dev || apt-get -y install libmysqlclient-dev

ADD ./requirements.txt /soundchat-server/requirements.txt

WORKDIR /soundchat-server

COPY . /soundchat-server

RUN pip install -r requirements.txt

RUN chmod +x /soundchat-server/run.sh
RUN chmod +x /soundchat-server/wait-for-it.sh

CMD ./run.sh