import os
import time
from constants import DB_FILE_NAME
from pi_hole_admin import PiHoleAdmin
from unique_domains_windower import UniqueDomainsWindower
import sqlite_utils
import tldextract

def initialize_default_windower(url: str, file_name: str, types: list, only_domains: bool, pi_hole_password_env_var: str="PI_HOLE_PW"):
    if file_name is None:
        raise ValueError("Default windower should have a file name but received None.")

    client = PiHoleAdmin(url, pi_hole_password_env_var=pi_hole_password_env_var)

    if not os.path.isfile(file_name):
        print("Getting new default windower")
        windower = UniqueDomainsWindower(client, 86400 * 30, types, ["PTR"], 3600, True, None, file_name)
    else:
        print("Getting previously saved default windower")
        windower = UniqueDomainsWindower.deserialize(client, file_name)

    return windower

def get_domain_from_fqdn(fqdn, extractor):
    result = extractor(fqdn)

    if result.suffix is not None and result.suffix.strip() != '':
        return f"{result.domain}.{result.suffix}"

    return None

def main():
    start = time.time()
    print(f"Starting blacklist init at {start} sec since epoch")

    # To minimize alerts to a manageable level, only report on new domains for
    # whitelist, but report on subdomains for blacklist.
    windower_blacklist = initialize_default_windower(os.environ['PI_HOLE_URL'], 'windower_blacklist.bin', PiHoleAdmin.ALL_BLOCKED, False)

    print(f"Finished blacklist init in {time.time() - start} sec")

    start = time.time()

    print(f"Starting blacklist assessment at {start} sec since epoch")

    previously_unseen_blocked_domain_data = windower_blacklist.get_previously_unseen_domains()
 
    oldest_bound, newest_bound = windower_blacklist.get_time_interval()

    extractor = tldextract.TLDExtract(cache_dir=os.environ['TLDEXTRACT_CACHE'])

    sqlite_utils.log_reason(DB_FILE_NAME, [{'domain': get_domain_from_fqdn(name, extractor), 'first_time_seen': seen_time, 'last_time_seen': seen_time, 'permitted': False, "reason": "Blocked by PiHole", "name": name} for name, seen_time in previously_unseen_blocked_domain_data.items()], updateable_fields=['permitted', 'reason', 'last_time_seen'])

    sqlite_utils.notify_of_new_domains_in_interval(DB_FILE_NAME, windower_blacklist._window_oldest_bound, windower_blacklist._window_newest_bound, False, os.environ['ADMIN_PHONE'], os.environ['TWILIO_PHONE'], os.environ['SES_EMAIL_ADMIN'])

    print(f"Finished blacklist assessment in {time.time() - start} sec")

    start = time.time()

    print(f"Starting whitelist assessment at {start} sec since epoch")

    # Don't log "permitted" domains (according to pihole API) to DB because interceptor.py has the final say on what is permitted, so no updates or inserts should be necessary on permitted domains from the PiHole API.
    # Instead, just perform notification based on data already in DB.
    sqlite_utils.notify_of_new_domains_in_interval(DB_FILE_NAME, oldest_bound, newest_bound, True, os.environ['ADMIN_PHONE'], os.environ['TWILIO_PHONE'], os.environ['SES_EMAIL_ADMIN'])

    print(f"Finished whitelist assessment in {time.time() - start} sec")

if __name__ == "__main__":
    main()