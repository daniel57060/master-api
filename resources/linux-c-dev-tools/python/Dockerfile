# Use a base image with Linux and Python 3
FROM python:3

# Set the maintainer label for the image
LABEL maintainer="Your Name <your@email.com>"

# Install essential C development tools
RUN apt-get update && apt-get install -y \
  build-essential \
  gcc \
  make \
  gdb \
  && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

COPY ./inspector_print /inspector_print
COPY ./run.sh ./run.sh
COPY ./scripts.py ./scripts.py

# Command to run when the container starts
CMD ["/bin/bash"]
