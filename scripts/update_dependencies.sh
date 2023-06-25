#!/bin/bash

wget -O- https://visjs.github.io/vis-network/standalone/umd/vis-network.min.js > netdoc/static/netdoc/js/vis-network.min.js
wget -O- https://visjs.github.io/vis-network/standalone/umd/vis-network.min.js.map > netdoc/static/netdoc/js/vis-network.min.js.map
wget -O- https://visjs.github.io/vis-network/dist/dist/vis-network.min.css > netdoc/static/netdoc/css/vis-network.min.css
