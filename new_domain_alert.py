import os
import time
from twilio.rest import Client
from pi_hole_admin import PiHoleAdmin
from unique_domains_windower import UniqueDomainsWindower

def initialize_default_windower(url: str, file_name: str, types: list, only_domains: bool, pi_hole_password_env_var: str="PI_HOLE_PW"):
    if file_name is None:
        raise ValueError("Default windower should have a file name but received None.")

    client = PiHoleAdmin(url, pi_hole_password_env_var=pi_hole_password_env_var)

    if not os.path.isfile(file_name):
        print("Getting new default windower")
        windower = UniqueDomainsWindower(client, 86400 * 30, types, ["PTR"], 3600, only_domains, True, None, file_name)
    else:
        print("Getting previously saved default windower")
        windower = UniqueDomainsWindower.deserialize(client, file_name)

    return windower

def notify_of_new_domains(domains: list, recipient_phone: str, twilio_phone: str, msg_chars_limit: int=1000, blocked: bool=True):
    """
    Send message if a set of new domains has been seen.
    """
    if not domains:
        return

    account_sid = os.environ['TWILIO_ACCOUNT_SID']
    auth_token = os.environ['TWILIO_AUTH_TOKEN']
    client = Client(account_sid, auth_token)

    body = f"{'Blocked' if blocked else 'Permitted'} {len(domains)} domains that have not been seen recently:\n"

    i = 0

    while i < len(domains) and len(body) < msg_chars_limit:
        if len(body) + len(domains[i]) < msg_chars_limit:
            body += f"{domains[i]}\n"

            i += 1
        else:
            break

    if i != len(domains):
        body += "..."

    message = client.messages.create(
        body=body,
        from_=twilio_phone,
        to=recipient_phone
    )

    print(f"Sending message with SID: {message.sid}")

def main():
    start = time.time()
    print(f"Starting blacklist init at {start} sec since epoch")

    # To minimize alerts to a manageable level, only report on new domains for
    # whitelist, but report on subdomains for blacklist.
    windower_blacklist = initialize_default_windower(os.environ['PI_HOLE_URL'], 'windower_blacklist.bin', PiHoleAdmin.ALL_BLOCKED, False)

    print(f"Finished blacklist init in {time.time() - start} sec")

    start = time.time()
    print(f"Starting whitelist init at {start} sec since epoch")

    windower_whitelist = initialize_default_windower(os.environ['PI_HOLE_URL'], 'windower_whitelist.bin', PiHoleAdmin.ALL_PERMITTED, True)

    print(f"Finished whitelist init in {time.time() - start} sec")

    start = time.time()

    print(f"Starting blacklist assessment at {start} sec since epoch")
    
    previously_unseen_blocked_domains = list(windower_blacklist.get_previously_unseen_domains())

    print(f"Found blocked domains {previously_unseen_blocked_domains}")

    notify_of_new_domains(previously_unseen_blocked_domains, os.environ["ADMIN_PHONE"], os.environ["TWILIO_PHONE"], blocked=True)
    
    print(f"Finished blacklist assessment in {time.time() - start} sec")

    start = time.time()

    print(f"Starting whitelist assessment at {start} sec since epoch")

    previously_unseen_permitted_domains = list(windower_whitelist.get_previously_unseen_domains())

    print(f"Found permitted domains {previously_unseen_permitted_domains}")

    notify_of_new_domains(previously_unseen_permitted_domains, os.environ["ADMIN_PHONE"], os.environ["TWILIO_PHONE"], blocked=False)

    print(f"Finished whitelist assessment in {time.time() - start} sec")

if __name__ == "__main__":
    main()