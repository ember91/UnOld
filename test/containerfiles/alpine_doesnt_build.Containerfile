FROM alpine:3.20

RUN hfdjsk

# hadolint ignore=DL3059
RUN apk add --no-cache \
    git==2.43.0-r0 \
    nginx==1.26.2-r0
