FROM postgres:latest

ENV POSTGRES_USER=nois
ENV POSTGRES_PASSWORD=senha_massa
ENV POSTGRES_DB=ru_bd

RUN apt-get update && apt-get install -y locales && \
    sed -i -e 's/# pt_BR.UTF-8 UTF-8/pt_BR.UTF-8 UTF-8/' /etc/locale.gen && \
    dpkg-reconfigure --frontend=noninteractive locales && \
    update-locale LANG=pt_BR.UTF-8

ENV LANG=pt_BR.UTF-8
ENV LANGUAGE=pt_BR:pt_BR
ENV LC_ALL=pt_BR.UTF-8