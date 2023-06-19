#! /usr/bin/env python
"""Discovery task for Cisco IOS devices via Netmiko."""
__author__ = "Andrea Dainese"
__contact__ = "andrea@adainese.it"
__copyright__ = "Copyright 2022, Andrea Dainese"
__license__ = "GPLv3"

import argparse
import ipaddress
from scapy.all import IP, UDP, SNMP, SNMPget, SNMPvarbind, ASN1_OID, sr1

OID_SYSDESCR = "1.3.6.1.2.1.1.1.0"


# p = IP(dst="192.168.2.150")/UDP(sport=161)/SNMP(community="public",PDU=SNMPget(varbindlist=[SNMPvarbind(oid=ASN1_OID("1.3.6.1.2.1.1.1.0"))]))


def scan(communities, addresses):
    snmp_pdu = SNMPget(varbindlist=[SNMPvarbind(oid=ASN1_OID(OID_SYSDESCR))])
    l4 = UDP(sport=161)
    for address in addresses:
        l3 = IP(dst=address)

        for community in communities:
            l7 = SNMP(community=community,PDU=snmp_pdu)
            packet = l3/l4/l7
            answer = sr1(l3/l4/l7, timeout=1)
            # send(pkt)
            if answer and answer.sprintf("%IP.proto%") != "icmp":
                p1 = pkt.sprintf("%SNMP.PDU%").split("ASN1_STRING['", 1)
                p2 = p1[1].split("'", 1)
                print pkt.sprintf("%IP.src%") + " - " + p2[0]
                f.write(pkt.sprintf("%IP.src%") + " - " + p2[0] + "\n")
        print(address)



def parse_args():
    parser=argparse.ArgumentParser(description="SNMPv2 scanner")
    parser.add_argument("-c", type=str, help="SNMPv2 community", action="append", required=True)
    parser.add_argument("-i", type=str, help="IP address or network to be discovered", action="append", required=True)
    args=parser.parse_args()
    return args


def main():
    inputs=parse_args()
    communities = inputs.c
    addresses = []
    
    for element in inputs.i:
        # Creating IP address list
        try:
            network = ipaddress.ip_network(element)
            for address in network:
                addresses.append(str(address))
        except ValueError:
            # address is not an IPv4 address/network
            pass

    scan(communities, addresses)
    print(communities)
    print(addresses)




                # p = SNMP(
                #         version=self.version,
                #         PDU=SNMPget(varbindlist=[SNMPvarbind(oid=ASN1_OID('1.3.6.1.2.1.1.1.0'))])
                # )
                # r = []
                # for c in communities:
                #         i = randint(0, 2147483647)
                #         p.PDU.id = i
                #         p.community = c
                #         self.s.sendto(str(p), self.addr)
                #         sleep(1/self.rate)
                # while True:
                #         try:
                #                 p = SNMP(self.s.recvfrom(65535)[0])
                #         except timeout:
                #                 break
                #         r.append(p.community.val)
                # return r




if __name__ == '__main__':
    main()


#     IP(dst=ip)
#     p = IP(dst=ip)
# 		UDP(dport=161, sport=39445)
# 		SNMP(community="private", PDU=SNMPget(id=1416992799, varbindlist=[SNMPvarbind(oid=ASN1_OID("1.3.6.1.2.1.1.1.0"))]))
# 		pkt = sr1(p, timeout=1)
# 		if pkt and pkt.sprintf("%IP.pro


    



# import json

# from nornir_utils.plugins.functions import print_result
# from nornir.core.filter import F

# from netdoc import utils
# from netdoc.schemas import discoverable, discoverylog


# def discovery(nrni):
#     """Discovery devices via SNMP v2."""
#     print("HERE")
#     print("WIP")
#     # print(filtered_devices.dict())
#     # session = Session(hostname='169.254.1.1', community='public', version=2)
#     # sysname = session.get(utils.SNMP_OID_MAP.get("sysName"))
#     # print(sysname.value)

#     def multiple_tasks(task):
#         """Define commands (in order) for the playbook."""
#         utils.append_nornir_snmp_task(task, oids="sysName", template="HOSTNAME", order=0)
#     #     utils.append_nornir_netmiko_task(
#     #         task, "show running-config | include hostname", template="HOSTNAME", order=0
#     #     )
#     #     utils.append_nornir_netmiko_task(
#     #         task,
#     #         [
#     #             "show running-config",
#     #             "show interfaces",
#     #             "show cdp neighbors detail",
#     #             "show lldp neighbors detail",
#     #             "show vlan",
#     #             "show vrf",
#     #             "show ip interface",
#     #         ],
#     #         order=10,
#     #     )
#     #     utils.append_nornir_netmiko_task(
#     #         task, "show mac address-table dynamic", template="show mac address-table"
#     #     )
#     #     utils.append_nornir_netmiko_task(
#     #         task,
#     #         [
#     #             "show etherchannel summary",
#     #             "show interfaces switchport",
#     #             "show inventory",
#     #         ],
#     #     )
#     #     utils.append_nornir_netmiko_task(
#     #         task,
#     #         [
#     #             "show version",
#     #             "show logging",
#     #             "show spanning-tree",
#     #             "show interfaces trunk",
#     #             "show standby",
#     #             "show vrrp all",
#     #             "show glbp",
#     #             "show ip ospf neighbor",
#     #             "show ip eigrp neighbors",
#     #             "show ip bgp neighbors",
#     #         ],
#     #         supported=False,
#     #     )

#     # Run the playbook
#     aggregated_results = nrni.run(task=multiple_tasks)

#     # Print the result
#     print_result(aggregated_results)

#     # # Save outputs and define additional commands
#     for key, multi_result in aggregated_results.items():
#     #     vrfs = ["default"]  # Adding default VRF
#         current_nr = nrni.filter(F(name=key))

#         # MultiResult is an array of Result
#         for result in multi_result:
#             if result.name == "multiple_tasks":
#                 # Skip MultipleTask
#                 continue

#             address = result.host.dict().get("hostname")
#             discoverable_o = discoverable.get(address, discovered=True)
#             details = json.loads(result.name)
#             discoverylog.create(
#                 command=details.get("command"),
#                 discoverable_id=discoverable_o.id,
#                 raw_output=result.result,
#                 template=details.get("template"),
#                 order=details.get("order"),
#                 details=details,
#             )

#     #         # Save VRF list for later
#     #         if details.get("command") == "show vrf":
#     #             parsed_vrfs, parsed = utils.parse_netmiko_output(
#     #                 result.result, details.get("command"), platform
#     #             )
#     #             if parsed:
#     #                 for vrf in parsed_vrfs:
#     #                     vrfs.append(vrf.get("name"))

#     #     # Additional commands out of the multi result loop
#     #     def additional_tasks(task):
#     #         """Define additional commands (in order) for the playbook."""
#     #         # Per VRF commands
#     #         for vrf in vrfs:  # pylint: disable=cell-var-from-loop
#     #             if vrf == "default":
#     #                 # Default VRF has no name
#     #                 utils.append_nornir_netmiko_task(
#     #                     task,
#     #                     [
#     #                         "show ip arp",
#     #                     ],
#     #                 )
#     #                 utils.append_nornir_netmiko_task(
#     #                     task,
#     #                     commands="show ip route connected",
#     #                     template="show ip route",
#     #                 )
#     #                 utils.append_nornir_netmiko_task(
#     #                     task,
#     #                     commands="show ip route static",
#     #                     template="show ip route",
#     #                 )
#     #                 utils.append_nornir_netmiko_task(
#     #                     task,
#     #                     commands="show ip route rip",
#     #                     template="show ip route",
#     #                 )
#     #                 utils.append_nornir_netmiko_task(
#     #                     task,
#     #                     commands="show ip route bgp",
#     #                     template="show ip route",
#     #                 )
#     #                 utils.append_nornir_netmiko_task(
#     #                     task,
#     #                     commands="show ip route eigrp",
#     #                     template="show ip route",
#     #                 )
#     #                 utils.append_nornir_netmiko_task(
#     #                     task,
#     #                     commands="show ip route ospf",
#     #                     template="show ip route",
#     #                 )
#     #                 utils.append_nornir_netmiko_task(
#     #                     task,
#     #                     commands="show ip route isis",
#     #                     template="show ip route",
#     #                 )
#     #             else:
#     #                 # with non default VRF commands and templates differ
#     #                 utils.append_nornir_netmiko_task(
#     #                     task, commands=f"show ip arp vrf {vrf}", template="show ip arp"
#     #                 )
#     #                 utils.append_nornir_netmiko_task(
#     #                     task,
#     #                     commands=f"show ip route vrf {vrf}",
#     #                     template="show ip route",
#     #                 )

#     #     # Run the additional playbook
#     #     additional_aggregated_results = current_nr.run(task=additional_tasks)

#     #     # Print the result
#     #     print_result(additional_aggregated_results)

#     #     for key, additional_multi_result in additional_aggregated_results.items():
#     #         # MultiResult is an array of Result
#     #         for result in additional_multi_result:
#     #             if result.name == "additional_tasks":
#     #                 # Skip MultipleTask
#     #                 continue

#     #             details = json.loads(result.name)
#     #             if " vrf " in details.get("command"):
#     #                 # Save the VRF in details
#     #                 details["vrf"] = details.get("command").split(" vrf ").pop()
#     #             discoverylog.create(
#     #                 command=details.get("command"),
#     #                 discoverable_id=discoverable_o.id,
#     #                 raw_output=result.result,
#     #                 template=details.get("template"),
#     #                 order=details.get("order"),
#     #                 details=details,
#     #             )