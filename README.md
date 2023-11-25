pip freeze > requirements.txt

python -m venv venv
.\venv\Scripts\Activate.ps1

pip install -r requirements.txt

uvicorn api:app --reload --reload-dir="server"
uvicorn api:app --log-config logging_config.ini
uvicorn api:app --log-config logging_config.ini --reload --reload-dir="server"

http://localhost:8000/docs#/
http://localhost:8000/redoc#/

docker stop linux-c-dev-tools

docker build -t linux-c-dev-tools ./resources/linux-c-dev-tools/alpine
docker build -t linux-c-dev-tools ./resources/linux-c-dev-tools/python

$PWD = Get-Location
$FILE_DIR = "${PWD}\files"

docker run -it --rm -v "${FILE_DIR}:/mnt/files" --detach --name linux-c-dev-tools linux-c-dev-tools

docker exec -it linux-c-dev-tools sh

docker exec -it linux-c-dev-tools sh -c "gcc -o program -I/inspector_print /mnt/files/01113cce-3429-4baf-8267-79f89da2753b.c"
docker exec -it linux-c-dev-tools sh -c "./run.sh 01113cce-3429-4baf-8267-79f89da2753b.c"
