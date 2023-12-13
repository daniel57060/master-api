# Run: docker build --tag linux-c-dev .
# Run: docker run -it --rm -d --publish=8080:80 --name api linux-c-dev
# Use a base image with Linux and Python 3
# https://stackoverflow.com/questions/62554991/how-do-i-install-python-on-alpine-linux
FROM python:3.12-alpine as library

# Install C/C++ dependencies
RUN apk --no-cache add build-base gcc

# Set the working directory
WORKDIR /app

# Install parser dependencies
COPY ./requirements.txt ./requirements.txt
RUN pip3 install --no-cache-dir --upgrade -r ./requirements.txt

COPY ./api.py ./api.py
COPY ./scripts.py ./scripts.py
COPY ./run.sh ./run.sh
COPY ./inspector_print /inspector_print

RUN chmod +x ./run.sh

# Command to run when the container starts
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "80"]
