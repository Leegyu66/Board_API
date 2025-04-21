FROM python:3.10

WORKDIR /code

RUN apt-get update \
    && apt-get install -y libgl1-mesa-glx libglib2.0-0 \
    && apt-get clean

COPY ./requirements.txt /code/requirements.txt


RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
 
COPY ./app /code/app
COPY ./front /code/front
COPY ./tests /code/tests
   
# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]