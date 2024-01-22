FROM ubuntu:latest
LABEL authors="masterbean"

# I. Codebase
# Set the working directory
WORKDIR /BeanHub-backend

# II. Dependencies
# Install necessary dependencies
RUN apt-get update && apt-get install -y \
    gnupg \
    python-is-python3 \
    net-tools \
    software-properties-common \
    python3.11-distutils \
    curl \
    portaudio19-dev \
    flac \
    ffmpeg

# Install Python
RUN apt-get install -y python3.11-venv
RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
RUN python3.11 get-pip.py

# Source Python
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

# III. Config
# Config stored in the environment
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=America/New_York

# IV. Backing services
# Consider adding instructions or configuration for connecting to backing services (e.g., database connection settings) based on your application's requirements.

# V. Build, release, run
# Copy files from local to container
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

# VI. Processes
# Execute the app as one or more stateless processes
ENTRYPOINT ["python3.11", "manage.py"]
CMD ["runserver", "0.0.0.0:8000"]

# VII. Port binding
# Export services via port binding - adjust based on your application's port requirements
EXPOSE 8000

# VIII. Concurrency
# Scale out via the process model - consider running multiple container instances based on your application's needs

# IX. Disposability
# Maximize robustness with fast startup and graceful shutdown - handled by Docker default behavior

# X. Dev/prod parity
# Keep development, staging, and production as similar as possible - additional considerations outside the Dockerfile may be needed

# XI. Logs
# Treat logs as event streams - consider configuring logging in your application code

# XII. Admin processes
# Run admin/management tasks as one-off processes - handled by using the manage.py script

# Default command for the run stage
CMD ["/bin/bash"]
