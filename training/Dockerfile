FROM python:3.12-slim

WORKDIR /app
COPY training/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY training/treinar.py ./treinar.py

CMD ["python", "-u", "treinar.py"]
