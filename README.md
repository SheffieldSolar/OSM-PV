# OSM-PV
Tools to validate the PV systems matched in OSM and cross-reference with other data sources.

## What is this repository for? ##

Generate validation data for the 'Enabling worldwide solar PV nowcasting via machine vision and open data' collaboration project between The Turing Institute, University of Sheffield and Open Climate Fix.
* Developed and tested with Python 3.7, should work for 3.7+.

## Getting set up ##

* Install Docker on your machine: https://docs.docker.com/install/
* Pull the latest container image: `docker pull sheffieldsolar/osm_pv` (https://hub.docker.com/repository/docker/sheffieldsolar/osm_pv)

## Running the Flask App to validate OSM data ##

```
>> docker run -it --rm -p 5000:5000 -v <local-results-dir>:/osm_pv/flask_ui/results osm_pv
```

Not that you should replace `<local-results-dir>` with the full path to the destination directory you wish to use.
e.g.

```
>> docker run -it --rm -p 5000:5000 -v C:\Users\EJones820\Desktop\Sheffield_Solar\osm_pv\flask_ui\results:/osm_pv/flask_ui/results osm_pv
```

Note that in the above examples, the following flags are used with the `docker run` command:
* `-it` flags tell docker we want to run the container interactively
* `--rm` flag tells docker to remove the container once it has exited
* `--p 5000:5000` tells docker to map the host's port 5000 onto the container's port 5000 (i.e. so we can see the Flask server from outside the container)
* `-v <local-results-dir>:/osm_pv/flask_ui/results` flag is mounting the local directory `<local-results-dir>` onto the container directory `/osm_pv/flask_ui/results` (which is the default location for results files within the container)

## How do I update? ##
Run `docker pull sheffieldsolar/osm_pv`.
