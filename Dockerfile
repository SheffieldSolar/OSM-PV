FROM python:3.7
WORKDIR /osm_pv

COPY requirements.txt /osm_pv/requirements.txt

RUN pip install --no-cache-dir -r /osm_pv/requirements.txt > /dev/null

COPY . /osm_pv/

CMD ["/bin/bash", "/osm_pv/flask_ui/launch_ui.sh"]
