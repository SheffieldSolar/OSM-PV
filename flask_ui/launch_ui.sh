# Launch the flask UI on localhost:5000
SCRIPTDIR=`dirname "${BASH_SOURCE[0]}"`
export FLASK_APP="$SCRIPTDIR/osm_validator.py"
export FLASK_ENV="development"
flask run --host 0.0.0.0 --port 5000
