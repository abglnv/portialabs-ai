FROM python:3.11

WORKDIR /code
COPY requirements.txt /code/requirements.txt
RUN apt update
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
COPY app /code/app
ENV PYTHONPATH=/code/app
EXPOSE 8000
CMD ["uvicorn", "app.main:app"]