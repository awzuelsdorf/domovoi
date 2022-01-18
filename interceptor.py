from twisted.names import dns, server, client, cache
from twisted.application import service, internet

from ip_address_utils import ip_cidr_to_ip_value_range, get_value, value_to_ip

import twilio_utils

import re
import os

DEFAULT_INTERCEPTOR_PORT = 47786

class MapResolver(client.Resolver):
    def __init__(self, servers, ip_address_file_name):
        client.Resolver.__init__(self, servers=servers)

        self.blocked_ip_value_ranges = self._populate_blocked_ip_value_ranges(ip_address_file_name)

        self.blocked_ips = set()

        self.ttl = 10

    def lookupAddress(self, name, timeout = None):
        lookup_result = self._lookup(name, dns.IN, dns.A, timeout)
        lookup_result.addCallback(lambda value: self.assess_found_ips(value))
        return lookup_result

    def _populate_blocked_ip_value_ranges(self, ip_cidr_file_name):
        ip_value_ranges = list()

        with open(ip_cidr_file_name, 'r', encoding='utf-8') as ip_cidr_file:
            for ip_cidr in ip_cidr_file:
                ip_value_ranges.append(ip_cidr_to_ip_value_range(ip_cidr.strip()))

        return ip_value_ranges

    def _search_range_tuples(self, value):
        """
        Binary searches the IP value range tuples, using the midpoint of the
        range as the 'value' of the range, to see if 'value' is contained in
        any of the ranges. Returns the matching IP value range or None
        if no containing range found.
        """
        for range_i in self.blocked_ip_value_ranges:
            if range_i[0] <= value and value <= range_i[1]:
                return range_i

        # element was not present in the list, return None
        return None
  
    def get_blocked_ip_value_range(self, ip_address):
        """
        Checks whether ip address is in a blocked IP range. Returns the blocked
        range if one is found. Returns None otherwise.
        """
        ip_address_value = get_value(ip_address)

        found_range = self._search_range_tuples(ip_address_value)

        if found_range is None:
            print(f"IP address {ip_address} with value {ip_address_value} not found in IP address ranges.")
            return None
        else:
            print(f"IP address {ip_address} with value {ip_address_value} found in IP address range {(value_to_ip(found_range[0]), value_to_ip(found_range[1]))} with values {found_range} .")
            return found_range

    def assess_found_ips(self, value):
        print(value)

        if value:
            for v in value:
                if v:
                    for v1 in v:
                        if v1:
                            payload = v1.__dict__.get("payload")
                            if payload:
                                record = str(payload)

                                result = re.findall("<A address=(\d+\.\d+\.\d+\.\d+) ttl=\d+>", record)

                                if result:
                                    print(f"Match: '{result}' '{record}'")

                                    blocked_ip_range = self.get_blocked_ip_value_range(result[0])

                                    if blocked_ip_range:
                                        if result[0] not in self.blocked_ips:
                                            print(f"Adding '{result[0]}' to blocked IP address list.")
                                            self.blocked_ips.add(result[0])
                                            #twilio_utils.notify_of_ip_block(result[0], (value_to_ip(blocked_ip_range[0]), value_to_ip(blocked_ip_range[1])), os.environ["ADMIN_PHONE"], os.environ["TWILIO_PHONE"])
                                        else:
                                            print(f"Not adding '{result[0]}' to blocked IP address list or notifiying via Twilio")

                                        return []
                                else:
                                    print(f"No match: '{result}' '{record}'")
        return value


# Setup Twisted application with upstream dns server at 127.0.0.1:5335 (unbound dns resolver).
application = service.Application('dnsserver', 1, 1)
simpledns = MapResolver(servers=[("127.0.0.1", 5335)], ip_address_file_name=os.environ["IP_ADDRESS_FILE_PATH"])

# Create protocols.
f = server.DNSServerFactory(caches=[cache.CacheResolver()], clients=[simpledns])
p = dns.DNSDatagramProtocol(f)
f.noisy = p.noisy = False

# Register both TCP and UDP on port 47786.
ret = service.MultiService()
PORT = os.environ.get("INTERCEPTOR_PORT", DEFAULT_INTERCEPTOR_PORT) or DEFAULT_INTERCEPTOR_PORT

# Attach services to the parent.
for (klass, arg) in [(internet.TCPServer, f), (internet.UDPServer, p)]:
    s = klass(PORT, arg)
    s.setServiceParent(ret)

# Run as a twistd application.
ret.setServiceParent(service.IServiceCollection(application))

if __name__ == '__main__':
    import sys
    print(f"Usage: twistd -ny {sys.argv[0]}")
