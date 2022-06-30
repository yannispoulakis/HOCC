FROM python:3.8-slim-buster
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
ENV SEMANTICS-BLOCK-URL="https://semantics-block.apps.ocphub.physics-faas.eu"
COPY . .
RUN useradd -ms /bin/bash admin

EXPOSE 5000
RUN chown -R admin:admin /app
RUN chmod 777 /app
USER admin
ENTRYPOINT ["python"]

CMD [ "app.py"]