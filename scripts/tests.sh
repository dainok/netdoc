#!/bin/bash

/opt/netbox/venv/bin/python3 /opt/netbox/netbox/manage.py test netdoc --verbosity=2 --keepdb
