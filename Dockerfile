# syntax=docker/dockerfile:1

FROM python:3.10

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /code

COPY . /code
RUN ls -la 
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
RUN pip install .
CMD [ "python3", "-m", "uvicorn", "src.server.exchange_server:app", "--host", "0.0.0.0" ]
