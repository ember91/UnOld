FROM ubuntu:24.04

RUN apt-get -y update \
    && apt-get install --no-install-recommends -y \
        git=1:2.43.0-1ubuntu7.1 \
    && rm -rf /var/lib/apt/lists/*
