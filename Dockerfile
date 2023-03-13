FROM python:3.11-bullseye

WORKDIR /app

COPY ./requirements.txt /app
RUN pip install --no-cache-dir --upgrade -r requirements.txt

RUN apt-get update -y
RUN apt-get install -y tzdata

ENV TZ America/Vancouver

COPY . /app

CMD [ "python", "-m", "bot" ]
