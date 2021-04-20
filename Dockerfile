FROM odoo:10.0
USER root
RUN apt-get update
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
RUN apt -y install python-pandas
RUN chmod 777 -R /home/
