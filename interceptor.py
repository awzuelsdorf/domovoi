from collections import Mapping

from twisted.names import dns, server, client, cache
from twisted.application import service, internet

import re
def myprint(value):
    print(value)
    if value:
        for v in value:
            if v:
                for v1 in v:
                    payload = v1.__dict__.get("payload")
                    if payload:
                        record = str(payload)

                        result = re.findall("<A address=(\d+\.\d+\.\d+\.\d+) ttl=\d+>", record)
                        if result:
                            print(f"Match: '{result}' '{record}'")
                        else:
                            print(f"No match: '{result}' '{record}'")
    return value

class MapResolver(client.Resolver):
    def __init__(self, servers):
        client.Resolver.__init__(self, servers=servers)

        self.ttl = 10

    def lookupAddress(self, name, timeout = None):
        lookup_result = self._lookup(name, dns.IN, dns.A, timeout)
        lookup_result.addCallback(myprint)
        return lookup_result


# Setup Twisted application with upstream dns server at 127.0.0.1:5335 (unbound dns resolver).
application = service.Application('dnsserver', 1, 1)
simpledns = MapResolver(servers=[("127.0.0.1", 5335)])

# Create protocols.
f = server.DNSServerFactory(caches=[cache.CacheResolver()], clients=[simpledns])
p = dns.DNSDatagramProtocol(f)
f.noisy = p.noisy = False

# Register both TCP and UDP on port 47786.
ret = service.MultiService()
PORT = 47786

# Attach services to the parent.
for (klass, arg) in [(internet.TCPServer, f), (internet.UDPServer, p)]:
    s = klass(PORT, arg)
    s.setServiceParent(ret)

# Run as a twistd application.
ret.setServiceParent(service.IServiceCollection(application))

if __name__ == '__main__':
    import sys
    print(f"Usage: twistd -ny {sys.argv[0]}")
