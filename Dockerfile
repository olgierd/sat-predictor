FROM python:3.7

COPY requirements.txt /sat/requirements.txt

RUN pip3 install -r /sat/requirements.txt

COPY . /sat

EXPOSE 7138

WORKDIR /sat/app

RUN ./updatesatdatabase.py satellites.csv

CMD gunicorn -w4 -b :7138 main:app
