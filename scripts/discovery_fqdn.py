import socket

from ipam.models import IPAddress

ip_addresses = IPAddress.objects.filter(dns_name="")
for ip_address_o in ip_addresses:
    ip_address = str(ip_address_o.address.ip)
    try:
        result = socket.gethostbyaddr(ip_address)
        # Host found
        fqdn = result[0].lower()
        print(f"{ip_address} is {fqdn}")
        ip_address_o.dns_name = fqdn
        ip_address_o.save()
    except Exception:
        # Host not found
        pass

