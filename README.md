# OSM-PV
Tools to validate the PV systems mapped in OSM and cross-reference with other data sources.

## What is this repository for? ##

Generate validation data for the 'Enabling worldwide solar PV nowcasting via machine vision and open data' collaboration project between The Turing Institute, University of Sheffield and Open Climate Fix.
* Developed and tested with Python 3.7, should work for 3.6+.

## Getting set up ##

* Install Docker on your machine: https://docs.docker.com/install/
* Pull the latest container image: `docker pull sheffieldsolar/osm_pv` (https://hub.docker.com/repository/docker/sheffieldsolar/osm_pv)

## Running the _fix_groupings.py_ script to expand pairwise group chains ##

```
>> docker run -it --rm sheffieldsolar/osm_pv python fix_groupings.py -h
```

This will print the CLI help for the Python script:

```
usage: fix_groupings.py [-h] -f </path/to/file> -o </path/to/file>
This is a command line interface (CLI) for the fix_groupings.py module
optional arguments:
  -h, --help            show this help message and exit
  -f </path/to/file>, --input-file </path/to/file>
                        Specify the path to the input CSV file.
  -o </path/to/file>, --output-file </path/to/file>
                        Specify the path to the output CSV file.
Jamie Taylor & Ethan Jones, 2020-03-04
```

Note that you need to specify an input file (of pairwise groupings) and an output file. The easiest way to do this whilst still running inside the Docker container is to mount a folder on your local machine onto the container, e.g.

```
>> docker run -it --rm -v C:\Users\jamie\Downloads\osm_pv:/data sheffieldsolar/osm_pv python fix_groupings.py -f /data/osm_solar_farm_neighbour_objects.csv -o /data/osm_solar_farm_neighbour_objects_grouped.csv
```

The output file will be a CSV with columns:

* id - Arbitrary group ID
* objects - Link to the OSM way
* lats - Pipe-separated list of latitudes for the nodes that make up the way
* lons - Pipe-separated list of longitudes for the nodes that make up the way

e.g.

```
id,objects,lats,lons
1,https://www.openstreetmap.org/way/677301225,52.9520724|52.9520817|52.9517843|52.9517748|52.9520724,-1.1396374|-1.1395169|-1.1394524|-1.1395738|-1.1396374
1,https://www.openstreetmap.org/way/677301226,52.9520614|52.9520708|52.9517734|52.9517639|52.9520614,-1.1397766|-1.139656|-1.1395915|-1.1397129|-1.1397766
1,https://www.openstreetmap.org/way/677301224,52.9520781|52.9520886|52.9518761|52.9518729|52.9517896|52.9517832|52.9520781,-1.1395017|-1.1393877|-1.1393421|-1.1393662|-1.1393514|-1.1394426|-1.1395017
1,https://www.openstreetmap.org/way/677301233,52.9520894|52.9520987|52.9518769|52.9518675|52.9520894,-1.1393701|-1.1392483|-1.1392015|-1.1393232|-1.1393701
1,https://www.openstreetmap.org/way/677301227,52.9520525|52.9520619|52.9517645|52.951755|52.9520525,-1.1399187|-1.1397982|-1.1397337|-1.1398551|-1.1399187
1,https://www.openstreetmap.org/way/677301234,52.9520968|52.9521021|52.9518819|52.9518767|52.9520968,-1.1392176|-1.1391454|-1.139101|-1.1391732|-1.1392176
1,https://www.openstreetmap.org/way/677301228,52.9520364|52.9520457|52.9517483|52.9517388|52.9520364,-1.1400582|-1.1399376|-1.1398732|-1.1399946|-1.1400582
1,https://www.openstreetmap.org/way/677301229,52.9520283|52.9520376|52.9517403|52.9517307|52.9520283,-1.1402003|-1.1400798|-1.1400153|-1.1401367|-1.1402003
1,https://www.openstreetmap.org/way/677301230,52.9520099|52.9520193|52.9517219|52.9517124|52.9520099,-1.1403418|-1.1402212|-1.1401567|-1.1402781|-1.1403418
2,https://www.openstreetmap.org/way/681746448,51.7378823|51.7381049|51.7372678|51.7371947|51.7372844|51.7378823,-2.3676127|-2.3664004|-2.3662609|-2.3668456|-2.3670387|-2.3676127
...
```

This output file is needed for the Grouping Validation Flask App...

## Running the Flask App to validate OSM data ##

```
>> docker run -it --rm -p 5000:5000 -v <local-results-dir>:/osm_pv/flask_ui/results sheffieldsolar/osm_pv
```

Note that you should replace `<local-results-dir>` with the full path to the destination directory you wish to use.
e.g.

```
>> docker run -it --rm -p 5000:5000 -v C:\Users\EJones820\Desktop\Sheffield_Solar\osm_pv\flask_ui\results:/osm_pv/flask_ui/results sheffieldsolar/osm_pv
```

Now, just visit http://127.0.0.1:5000 in your browser! (preferably Chrome)

Note that in the above examples, the following flags are used with the `docker run` command:
* `-it` flags tell docker we want to run the container interactively
* `--rm` flag tells docker to remove the container once it has exited
* `--p 5000:5000` tells docker to map the host's port 5000 onto the container's port 5000 (i.e. so we can see the Flask server from outside the container)
* `-v <local-results-dir>:/osm_pv/flask_ui/results` flag is mounting the local directory `<local-results-dir>` onto the container directory `/osm_pv/flask_ui/results` (which is the default location for results files within the container)

## How do I update? ##
Run `docker pull sheffieldsolar/osm_pv`.

## To Do ##
1. <s>Load Bing Maps API key from file</s>
2. <s>Add text box to record notes on rejected groupings</s>
3. <s>Fix bug whereby groupings validator doesn't return to home after last group</s>
4. <s>Add standarised notes through check boxes</s>
5. <s>Fixed bug whereby couldn't jump to specific group from the home page</s>
