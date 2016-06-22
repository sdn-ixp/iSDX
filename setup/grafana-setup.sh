#!/usr/bin/env bash

# download and install influxdb
wget https://dl.influxdata.com/influxdb/releases/influxdb_0.13.0_amd64.deb
sudo dpkg -i influxdb_0.13.0_amd64.deb
rm -f influxdb_0.13.0_amd64.deb

sudo service influxdb start
influx -execute 'create database sdx'

# download and install grafana
wget https://grafanarel.s3.amazonaws.com/builds/grafana_3.0.4-1464167696_amd64.deb
sudo apt-get install -y adduser libfontconfig
sudo dpkg -i grafana_3.0.4-1464167696_amd64.deb
rm -f grafana_3.0.4-1464167696_amd64.deb

# configure to start at boot
sudo update-rc.d grafana-server defaults 95 10

sudo service grafana-server start

# configure grafana
curl -X POST -d @/home/vagrant/iSDX/setup/grafanaDataSource.json http://admin:admin@localhost:3000/api/datasources --header "Content-Type:application/json"

# configure directories for stats
sudo mkdir -p /var/log/sdx
sudo chmod og+w /var/log/sdx
