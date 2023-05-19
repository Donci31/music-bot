FROM python

RUN apt-get -y update && apt-get install -y ffmpeg	

WORKDIR /app/

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY musicbot/ musicbot/
COPY main.py .

CMD ["python3", "main.py"]

