FROM python:3.9-slim-bullseye AS compile-image
LABEL maintainer="Wazo Maintainers <dev@wazo.community>"

RUN apt-get -qq update && apt-get -qq -y install gcc
RUN python3 -m venv /opt/venv
# Activate virtual env
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt /usr/local/src/wazo-confgend/requirements.txt
WORKDIR /usr/local/src/wazo-confgend

# incremental==24.7.0+ is downloaded automatically by twisted install
# but this version is incompatible with setuptools 58.1 from python:3.9-slim-bullseye
RUN pip install incremental==17.5.0
RUN pip install -r requirements.txt

COPY setup.py /usr/local/src/wazo-confgend/
COPY bin /usr/local/src/wazo-confgend/bin
COPY wazo_confgend /usr/local/src/wazo-confgend/wazo_confgend
RUN python3 -m pip install .

FROM python:3.9-slim-bullseye AS build-image
COPY --from=compile-image /opt/venv /opt/venv

COPY ./etc/wazo-confgend /etc/wazo-confgend
RUN true\
    && adduser --quiet --system --group --home /var/lib/wazo-confgend wazo-confgend \
    && mkdir -p /etc/wazo-confgend/conf.d \
    && install -D -o wazo-confgend -g wazo-confgend /dev/null /var/log/wazo-confgend.log \
    && install -d -o wazo-confgend -g wazo-confgend /var/cache/wazo-confgend

EXPOSE 8668

# Activate virtual env
ENV PATH="/opt/venv/bin:$PATH"
CMD ["wazo-confgend"]
