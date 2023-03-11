FROM alpine:3.17

RUN apk --no-cache --update-cache add python3 py3-pip py3-wheel
RUN pip install --no-cache-dir python-decouple==3.8 requests==2.28.2 telebot==0.0.5

COPY run.py utils.py heroes.csv /app/
WORKDIR /app

CMD ["python3", "/app/run.py"]