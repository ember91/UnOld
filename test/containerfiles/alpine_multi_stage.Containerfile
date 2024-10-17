FROM alpine:3.20
RUN apk add --no-cache git==2.43.0-r0

FROM alpine:3.20
RUN apk add --no-cache nginx==1.26.1-r0
