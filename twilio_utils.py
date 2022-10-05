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
        domains.append(f"https://duckduckgo.com/?q=%22{domain}%22")

        if len(domains) == batch_size:
            body = f"{'Blocked' if blocked else 'Permitted'} {len(domains)} domain(s) that have/has not been seen recently:\n" + ('\n'.join(domains))

            message = client.messages.create(
                body=body,
                from_=twilio_phone,
                to=recipient_phone
            )

            print(f"Sending message with SID: {message.sid}")

            num_domains += len(domains)
            domains = list()

    if domains:
        body = f"{'Blocked' if blocked else 'Permitted'} {len(domains)} domain(s) that have/has not been seen recently:\n" + ('\n'.join(domains))

        message = client.messages.create(
            body=body,
            from_=twilio_phone,
            to=recipient_phone
        )

        print(f"Sending message with SID: {message.sid}")
        num_domains += len(domains)

    if num_domains != len(all_domains):
        raise ValueError(f"Received invalid number of domains. Expected {len(all_domains)} but got {num_domains}")
