from twisted.names import dns, server, client, cache
from twisted.application import service, internet

import re
import os
import IP2Location

INTERCEPTOR_UPSTREAM_DNS_IP = os.environ["INTERCEPTOR_UPSTREAM_DNS_SERVER_IP"]
INTERCEPTOR_UPSTREAM_DNS_PORT = int(os.environ["INTERCEPTOR_UPSTREAM_DNS_SERVER_PORT"])
PORT = int(os.environ["INTERCEPTOR_PORT"])

class MapResolver(client.Resolver):
    def __init__(self, servers, blocked_countries_list, ip2location_bin_file_path='IP2LOCATION-LITE-DB1.BIN', ip2location_mode='SHARED_MEMORY'):
        client.Resolver.__init__(self, servers=servers)

        self.blocked_countries_list = list(blocked_countries_list)

        self.ip2location_client = IP2Location.IP2Location(filename=ip2location_bin_file_path, mode=ip2location_mode)

        self.ttl = 10

    def lookupAddress(self, name, timeout = None):
        lookup_result = self._lookup(name, dns.IN, dns.A, timeout)
        lookup_result.addCallback(lambda value: self.assess_found_ips(value))
        return lookup_result

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

                                    country_code = self.ip2location_client.get_country_short(result[0])
                                    if country_code in self.blocked_countries_list:
                                        print(f"Blocked IP '{result[0]}' with country code '{country_code}'. Blocked country codes were {', '.join(self.blocked_countries_list)}")
                                        return []
                                    else:
                                        print(f"Permitted IP '{result[0]}' with country code '{country_code}'. Blocked country codes were {', '.join(self.blocked_countries_list)}")
                                else:
                                    print(f"No match: '{result}' '{record}'")
        return value

# Setup Twisted application with upstream dns server.
application = service.Application('dnsserver', 1, 1)
simpledns = MapResolver(servers=[(INTERCEPTOR_UPSTREAM_DNS_IP, INTERCEPTOR_UPSTREAM_DNS_PORT)], blocked_countries_list=[_.upper() for _ in os.environ["BLOCKED_COUNTRIES_LIST"].split(",")], ip2location_bin_file_path=os.environ["IP2LOCATION_BIN_FILE_PATH"], ip2location_mode=os.environ["IP2LOCATION_MODE"])

# Create protocols.
f = server.DNSServerFactory(caches=[cache.CacheResolver()], clients=[simpledns])
p = dns.DNSDatagramProtocol(f)
f.noisy = p.noisy = False

# Register both TCP and UDP on port 47786.
ret = service.MultiService()

# Attach services to the parent.
for (klass, arg) in [(internet.TCPServer, f), (internet.UDPServer, p)]:
    s = klass(PORT, arg)
    s.setServiceParent(ret)

# Run as a twistd application.
ret.setServiceParent(service.IServiceCollection(application))

if __name__ == '__main__':
    import sys
    print(f"Usage: twistd -ny {sys.argv[0]}")
