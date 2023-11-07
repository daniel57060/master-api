set -e


mkdir -p ./outs
mkdir -p ./results/tmp
mkdir -p ./results/data

PROG=`basename -s ".c" $1`

JSON_PATH="/mnt/files/$PROG.json"
EXECUTABLE_PATH="./results/tmp/$PROG"
TRANSFORMED_PATH="/mnt/files/$PROG.c"
EXECUTABLE_PATH="./$PROG"

function clean_outputs() {
  rm -r outs
}

function compile() {
  echo -e "INFO: Compiling"
  gcc -o $EXECUTABLE_PATH -I/inspector_print -ggdb $TRANSFORMED_PATH 
}

function execute() {
  echo -e "INFO: Execute"
  echo -e "==============================================================="
  $EXECUTABLE_PATH
  echo -e "===============================================================\n"
}

function concat() {
  echo -e "INFO: Concatenating outs"
  echo "[" > $JSON_PATH
  cat outs/* | sort | sed s/$/,/ | sed s/^/\ \ / >> $JSON_PATH
  sed -i '$ s/.$//' $JSON_PATH
  echo "]" >> $JSON_PATH
}

clean_outputs
compile
execute
concat
