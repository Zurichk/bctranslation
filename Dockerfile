FROM python:3.8.4-slim-buster 
#FROM python:3.8-alpine

RUN mkdir /usr/src/app/
COPY ./code /usr/src/app/
WORKDIR /usr/src/app/

#COPY ./requirements.txt /usr/src/app/requirements.txt
#RUN pip install --no-cache-dir --upgrade -r /usr/src/app/requirements.txt

ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_ENV=development
ENV FLASK_DEBUG=True

#RUN apt-get update && apt-get install -y python3-dev gcc libc-dev musl-dev linux-headers
#RUN apt-get install -y zlib1g-dev libjpeg-dev
RUN pip install --no-cache-dir --upgrade -r /usr/src/app/requirements.txt
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

EXPOSE 5000

CMD ["flask", "run", "--host", "0.0.0.0"]