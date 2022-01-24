from twilio.rest import Client
import os
import requests
import time

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

def notify_of_ip_block(ip_address: str, country_code: str, recipient_phone: str, twilio_phone: str, retries: int=3, delay: int=5):
    """
    Send message if an IP address was blocked for being in a certain blocked IP range.
    """
    if not ip_address or not country_code:
        print(f"Invalid parameters: IP address \"{ip_address}\", blocked ip range \"{blocked_ip_range}\"")
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

