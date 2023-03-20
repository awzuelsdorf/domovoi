import traceback
from twisted.names import dns, server, client, cache
from twisted.application import service, internet

import tldextract
import re
import os
import IP2Location
import datetime
from constants import DB_FILE_NAME
from pi_hole_admin import PiHoleAdmin

import sqlite_utils

import pylru

INTERCEPTOR_UPSTREAM_DNS_IP = os.environ["INTERCEPTOR_UPSTREAM_DNS_SERVER_IP"]
INTERCEPTOR_UPSTREAM_DNS_PORT = int(os.environ["INTERCEPTOR_UPSTREAM_DNS_SERVER_PORT"])
PORT = int(os.environ["INTERCEPTOR_PORT"])

class MapResolver(client.Resolver):
    def __init__(self, servers, blocked_countries_list, ip2location_bin_file_path='IP2LOCATION-LITE-DB1.BIN', ip2location_mode='SHARED_MEMORY', domain_data_db_file=DB_FILE_NAME, whitelist_cache_sec=180):
        client.Resolver.__init__(self, servers=servers)
        self.extractor = tldextract.TLDExtract(cache_dir=os.environ['TLDEXTRACT_CACHE'])

        self.pi_hole_client = PiHoleAdmin(os.environ['PI_HOLE_URL'], pi_hole_password_env_var="PI_HOLE_PW")

        self.last_whitelist_refresh_time = None

        self.whitelist_cache_sec = whitelist_cache_sec

        self.blocked_countries_list = list(blocked_countries_list)

        self.ip2location_client = IP2Location.IP2Location(filename=ip2location_bin_file_path, mode=ip2location_mode)

        self.ttl = 10

        # key: ip address. Value: country code
        self.cached_ip_lookups = pylru.lrucache(10000)

        self.domain_data_db_file = domain_data_db_file

    def get_domain_from_fqdn(self, fqdn):
        result = self.extractor(fqdn)

        if result.suffix is not None and result.suffix.strip() != '':
            return f"{result.domain}.{result.suffix}"

        return None

    def lookupAddress(self, name, timeout=None):
        lookup_result = self._lookup(name, dns.IN, dns.A, timeout)
        lookup_result.addCallback(lambda value: self.assess_and_log_reason(value, name))
        return lookup_result

    def log_reason(self, name, domain, reason, permitted):
        right_now = datetime.datetime.now(tz=datetime.timezone.utc)

        sqlite_utils.log_reason(self.domain_data_db_file, [{'name': name, 'domain': domain, 'reason': reason, 'permitted': permitted, 'first_time_seen': right_now, 'last_time_seen': right_now}], ['permitted', 'reason', 'last_time_seen'])

    def assess_and_log_reason(self, value, name):
        right_now = datetime.datetime.now(tz=datetime.timezone.utc)

        if self.last_whitelist_refresh_time is None or right_now - self.last_whitelist_refresh_time > datetime.timedelta(seconds=self.whitelist_cache_sec):
            print(f"Doing refresh. Current time is {right_now}, last time was {self.last_whitelist_refresh_time}")
            do_refresh = True
            self.last_whitelist_refresh_time = right_now
        else:
            do_refresh = False

        applicable_whitelist_entries = self.pi_hole_client.get_whitelist_or_blacklist_entries_containing_domain(name.decode('utf-8'), ltype='white', bust_cache=do_refresh, wildcard=True, only_enabled=True, groups=re.split(r',', os.environ['GROUP_IDS']))

        has_whitelist_entry = applicable_whitelist_entries is not None and applicable_whitelist_entries != []

        if do_refresh or has_whitelist_entry:
            print(f"Applicable whitelist entries for domain {name} are {applicable_whitelist_entries}")

        reason, response = self.assess_found_ips(value, has_whitelist_entry)

        # We want to log the domain name only (e.g., the 'example.com' in
        # 'my.example.com' or 'www.example.com') if the domain is permitted.
        # Log the fqdn (e.g., the 'my.example.com' in 'my.example.com') if it
        # is blocked.
        try:
            if not response:
                domain_name = self.get_domain_from_fqdn(name.decode('utf-8'))

                self.log_reason(name.decode('utf-8'), domain_name, reason, False)

                print(f"Saving domain name \"{domain_name}\" that corresponds to FQDN \"{name}\" that was permitted")
            else:
                domain_name = self.get_domain_from_fqdn(name.decode('utf-8'))

                if domain_name is not None:
                    print(f"Saving domain name \"{domain_name}\" that corresponds to FQDN \"{name}\" that was permitted")

                    self.log_reason(name.decode('utf-8'), domain_name, reason, True)
                else:
                    raise ValueError(f"Could not get domain name from \"{name}\"")

        except BaseException as be:
            traceback.print_exc()
            print(f"Could not log reason '{reason}' for name '{name}' due to exception '{be}'")

        return response

    def assess_found_ips(self, value, skip_country_validation):
        print(value)

        reason = None

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
                                    if skip_country_validation:
                                        reason = "Skipping country validation due to applicable whitelist entries."

                                        print(reason)
                                    else:
                                        if result[0] not in self.cached_ip_lookups:
                                            self.cached_ip_lookups[result[0]] = self.ip2location_client.get_country_short(result[0])

                                        country_code = self.cached_ip_lookups[result[0]]

                                        if country_code in self.blocked_countries_list:
                                            reason = f"Blocked IP '{result[0]}' with country code '{country_code}'. Blocked country codes were {', '.join(self.blocked_countries_list)}"

                                            print(reason)

                                            return reason, []
                                        else:
                                            reason = f"Permitted IP '{result[0]}' with country code '{country_code}'. Blocked country codes were {', '.join(self.blocked_countries_list)}"

                                            print(reason)
                                else:
                                    reason = f"No match: '{result}' '{record}'"

                                    print(reason)
        return reason, value

# Setup Twisted application with upstream dns server.
application = service.Application('dnsserver', 1, 1)
simpledns = MapResolver(servers=[(INTERCEPTOR_UPSTREAM_DNS_IP, INTERCEPTOR_UPSTREAM_DNS_PORT)], blocked_countries_list=[_.upper() for _ in os.environ["BLOCKED_COUNTRIES_LIST"].split(",")], ip2location_bin_file_path=os.environ["IP2LOCATION_BIN_FILE_PATH"], ip2location_mode=os.environ["IP2LOCATION_MODE"], whitelist_cache_sec=int(os.environ["WHITELIST_CACHE_SEC"]))

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
