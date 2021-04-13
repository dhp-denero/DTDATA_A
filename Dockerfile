FROM odoo:10.0
USER root
RUN apt-get update
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
