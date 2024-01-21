FROM ubuntu:latest
LABEL authors="masterbean"

ENTRYPOINT ["top", "-b"]

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=America/New_York

# Install necessary dependencies
RUN apt-get update && apt-get install -y \
    gnupg \
    python-is-python3 \
    net-tools \
    software-properties-common
# Install Python
<<<<<<< HEAD
RUN apt-get update
RUN apt-get install -y python3.11-distutils curl
RUN apt-get install -y portaudio19-dev flac ffmpeg
RUN apt-get install -y python3.11-venv
RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
RUN python3.11 get-pip.py
=======
RUN apt-get update && \
    apt-get install -y python3.11-distutils curl && \
    apt-get install -y portaudio19-dev flac ffmpeg && \
    apt-get install -y  python3.11-venv && \
    curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && \
    python3.11 get-pip.py \
>>>>>>> 382e786 (initial commit.)

# Source Python
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

RUN mkdir /BeanHub-backend
WORKDIR /BeanHub-backend

COPY .github /BeanHub-backend/.github
COPY appendonlydir /BeanHub-backend/appendonlydir
COPY other /BeanHub-backend/other
COPY src /BeanHub-backend/src
COPY tests /BeanHub-backend/tests
COPY .env /BeanHub-backend/.env
COPY .gitignore /BeanHub-backend/.gitignore
COPY environment.sh /BeanHub-backend/environment.sh
COPY LICENSE /BeanHub-backend/LICENSE
COPY manage.py /BeanHub-backend/manage.py
COPY pytest.ini /BeanHub-backend/pytest.ini
COPY README.md /BeanHub-backend/README.md
COPY redis.conf /BeanHub-backend/redis.conf
COPY requirements.txt /BeanHub-backend/requirements.txt

<<<<<<< HEAD
CMD ["/bin/bash"]



=======
RUN pytest test

CMD ["/bin/bash"]
>>>>>>> 382e786 (initial commit.)
