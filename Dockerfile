FROM python:3.11

ENV PYTHONUNBUFFERED 1
ENV TZ=America/New_York

WORKDIR /beanhub_app

RUN apt-get update && \
    apt-get install -y \
        gnupg \
        python-is-python3 \
        net-tools \
        software-properties-common \
        python3.11-distutils \
        portaudio19-dev \
        flac \
        ffmpeg \
        gcc \
        python3.11-dev \
        python3.11-venv

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

RUN python manage.py test
RUN pytest tests

EXPOSE 8000

CMD ["python", "manage.py", "runserver"]