from twilio.rest import Client
import os
import requests
import time

def notify_of_new_domains(all_domains: list, recipient_phone: str, twilio_phone: str, blocked: bool=True, batch_size=50):
    """
    Send message if a set of new domains has been seen.
    """
    if not all_domains:
        return

    num_domains = 0

    account_sid = os.environ['TWILIO_ACCOUNT_SID']
    auth_token = os.environ['TWILIO_AUTH_TOKEN']
    client = Client(account_sid, auth_token)

    domains = list()

    for domain in all_domains:
        domains.append(f"https://duckduckgo.com/?q={domain}")

        if len(domains) == batch_size:
            body = f"{'Blocked' if blocked else 'Permitted'} {len(domains)} domains that have not been seen recently:\n" + ('\n'.join(domains))

            message = client.messages.create(
                body=body,
                from_=twilio_phone,
                to=recipient_phone
            )

            print(f"Sending message with SID: {message.sid}")

            num_domains += len(domains)
            domains = list()

    if domains:
        body = f"{'Blocked' if blocked else 'Permitted'} {len(domains)} domains that have not been seen recently:\n" + ('\n'.join(domains))

        message = client.messages.create(
            body=body,
            from_=twilio_phone,
            to=recipient_phone
        )

        print(f"Sending message with SID: {message.sid}")
        num_domains += len(domains)

    if num_domains != len(all_domains):
        raise ValueError(f"Received invalid number of domains. Expected {len(all_domains)} but got {num_domains}")

def notify_of_ip_block(ip_address: str, country_code: str, recipient_phone: str, twilio_phone: str, retries: int=3, delay: int=5):
    """
    Send message if an IP address was blocked for being in a certain blocked IP range.
    """
    if not ip_address or not country_code:
        print(f"Invalid parameters: IP address \"{ip_address}\", country code \"{country_code}\"")
        return

    account_sid = os.environ['TWILIO_ACCOUNT_SID']
    auth_token = os.environ['TWILIO_AUTH_TOKEN']

    body = f"Blocked IP address '{ip_address}' in blocked country '{country_code}'"

    retry = 0

    while retry < retries:
        try:
            client = Client(account_sid, auth_token)
            message = client.messages.create(
                body=body,
                from_=twilio_phone,
                to=recipient_phone
            )

            print(f"Sending message with SID: {message.sid}")
            break
        except requests.exceptions.ConnectionError as ce:
            retry += 1
            print(f"Received connection error {ce} . Retry {retry} / {retries} . Delay is {delay} seconds")
            time.sleep(delay)

