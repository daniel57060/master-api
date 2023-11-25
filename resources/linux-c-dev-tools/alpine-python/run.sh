set -e

mkdir -p ./outs
mkdir -p ./results/tmp
mkdir -p ./results/data

PROG=`basename ${1%.*}`

JSON_PATH="/mnt/files/$PROG.json"
EXECUTABLE_PATH="./results/tmp/$PROG"
TRANSFORMED_PATH="/mnt/files/$PROG.c"
EXECUTABLE_PATH="./$PROG"

echo -e "INFO: Removing outs"
python /app/scripts.py outs-remove

echo -e "INFO: Compiling"
gcc $TRANSFORMED_PATH -o $EXECUTABLE_PATH -I/inspector_print -ggdb

echo -e "INFO: Run"
echo -e "==============================================================="
$EXECUTABLE_PATH
echo -e "===============================================================\n"

echo -e "INFO: Concatenating outs"
python /app/scripts.py outs-concat --output ./results/data.json

echo -e "INFO: Renaming result"
mv ./results/data.json $JSON_PATH
