#
# Nios2 emulator.
# To build: docker build -t nios2 .
# To run: docker run -p 8080:8080 nios2 --ip 0.0.0.0
#
ARG BASE_CONTAINER=ubuntu:18.04
FROM $BASE_CONTAINER
LABEL MAINTAINER="Eric Wustrow <ewust@colorado.edu>"

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -yq --no-install-recommends \
    				   build-essential python3 python3-dev python3-pip \
				   python3-setuptools python3-numpy \
				   python3-bottle && \
    rm -rf /var/lib/apt/lists/*

RUN   pip3 install Cython bs4 jinja2

COPY . /opt/nios2

WORKDIR /opt/nios2

EXPOSE	8080

RUN	(cd lib ; make install)
RUN	python3 setup.py install

ENTRYPOINT  [ "python3", "app.py" ]
