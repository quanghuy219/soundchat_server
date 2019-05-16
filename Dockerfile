FROM tiangolo/uwsgi-nginx-flask:python3.7

ENV FLASK_ENV=development

RUN apt-get update
RUN apt-get -y install default-libmysqlclient-dev || apt-get -y install libmysqlclient-dev

COPY . .

RUN pip install -r requirements.txt

RUN chmod +x ./start_server.sh

CMD python database.py

CMD ./start_server.sh