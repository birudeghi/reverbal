# syntax=docker/dockerfile:1

FROM python:3.11.2-buster

WORKDIR /app

COPY requirements.txt ./

RUN pip install -r requirements.txt

RUN apt-get update

RUN apt-get install libsndfile1 -y

COPY . ./

EXPOSE 8080

CMD [ "python", "app.py" ]