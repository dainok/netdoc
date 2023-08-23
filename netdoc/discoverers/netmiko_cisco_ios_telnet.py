"""Wrapper for Cisco IOS devices via Netmiko telnet."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2022, Andrea Dainese"
__license__ = "GPLv3"

from netdoc.discoverers.netmiko_cisco_ios import discovery

discovery.platform = "cisco_ios_telnet"
