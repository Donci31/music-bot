FROM python

RUN apt-get -y update && apt-get install -y ffmpeg	

ADD . /app

WORKDIR /app

RUN pip install -r requirements.txt

CMD ["python3", "main.py"]

