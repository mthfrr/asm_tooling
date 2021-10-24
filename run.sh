#/bin/sh
[ $# -ne 1 ] && echo "Usage: $0 [tp_nb]" && exit 1

sudo ./start.sh students/tp$1-*
sudo chown "$USER:$USER" -R results/
cp docker/generate_traces_json.py results/.
cd results
./generate_traces_json.py tp$1-*
