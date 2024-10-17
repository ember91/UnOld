FROM opensuse/leap:15.6

RUN zypper install -y \
        git==2.43.0 \
        nginx==1.21.5 \
    && zypper clean
