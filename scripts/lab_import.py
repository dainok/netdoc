"""Blank the current database and load a specific scenario.

Usage:
/opt/netbox/venv/bin/python3 /opt/netbox/netbox/manage.py shell < lab_import.py
"""
from netdoc.tests.test import load_scenario

LAB_DIR = "netdoc/tests/netmiko_aruba_oscx/lab1"

load_scenario(LAB_DIR)
