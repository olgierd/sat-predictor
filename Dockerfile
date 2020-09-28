FROM debian:stable

COPY . /sat

RUN apt update && apt -y install python3 python3-pip && pip3 install -r /sat/requirements.txt && apt clean && apt autoclean

EXPOSE 7138

WORKDIR /sat/app

RUN ./updatesatdatabase.py satellites.csv

CMD gunicorn -w4 -b :7138 main:app
