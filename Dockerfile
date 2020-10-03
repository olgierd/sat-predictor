FROM python:3.7

COPY . /sat

RUN pip3 install -r /sat/requirements.txt

EXPOSE 7138

WORKDIR /sat/app

RUN ./updatesatdatabase.py satellites.csv

CMD gunicorn -w4 -b :7138 main:app
