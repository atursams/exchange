FROM python:3.8-alpine

# ENV PATH="/scripts:${PATH}"

COPY ./requirements.txt /requirements.txt

RUN pip install -r requirements.txt

RUN mkdir /mainsite
COPY ./mainsite /mainsite
WORKDIR /mainsite

