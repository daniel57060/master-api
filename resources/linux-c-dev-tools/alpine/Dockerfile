# Use Alpine Linux as the base image
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

RUN chmod +x ./run.sh

# Command to run when the container starts
CMD ["/bin/sh"]