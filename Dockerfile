FROM python:3.9
COPY ./requirements.txt /app/requirements.txt
EXPOSE 80
WORKDIR /app
RUN pip install -r requirements.txt
COPY . /app
CMD ["python", "run.py"]
