# Use a base image with Linux and Python 3
FROM alpine:latest


# Update the package list and install essential development tools
RUN apk --no-cache add \
  build-base \
  gcc \
  make \
  gdb

# Set the working directory
WORKDIR /app

COPY ./inspector_print /inspector_print
COPY ./run.sh ./run.sh
COPY ./scripts.py ./scripts.py

RUN chmod +x ./run.sh

# Command to run when the container starts
CMD ["/bin/sh"]
