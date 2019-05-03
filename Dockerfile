FROM python:3.7

RUN apt-get update \
 && apt-get install -y zip \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir photos src

WORKDIR /usr/src/app/src

COPY src/ .

CMD ["python", "server.py"]