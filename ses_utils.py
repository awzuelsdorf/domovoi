from twilio.rest import Client
import os

def notify_of_new_domains(all_domains: list, admin_email: str, blocked: bool=True, batch_size=50):
    """
    Send message if a set of new domains has been seen.
    """
    if not all_domains or not os.environ.get('SES_ENABLED'):
        return

    num_domains = 0

    access_key_id = os.environ['SES_ACCESS_KEY_ID']
    secret_access_key = os.environ['SES_SECRET_ACCESS_KEY']
    client = Client(access_key_id, secret_access_key)

    domains = list()

    for domain in all_domains:
        domains.append(f"https://duckduckgo.com/?q=%22{domain}%22")

        if len(domains) == batch_size:
            body = f"{'Blocked' if blocked else 'Permitted'} {len(domains)} domain(s) that have/has not been seen recently:\n" + ('\n'.join(domains))

            response = client.send_email(
                Source=admin_email,
                Destination={
                    'ToAddresses': [
                        admin_email
                    ]
                },
                Message={
                    'Subject': {
                        'Data': 'New domains found on network',
                        'Charset': 'utf-8'
                    },
                    'Body': {
                        'Text': {
                            'Data': body,
                            'Charset': 'utf-8'
                        }
                    }
                }
            )

            print(response)

            num_domains += len(domains)
            domains = list()

    if domains:
        body = f"{'Blocked' if blocked else 'Permitted'} {len(domains)} domain(s) that have/has not been seen recently:\n" + ('\n'.join(domains))

        response = client.send_email(
                Source=admin_email,
                Destination={
                    'ToAddresses': [
                        admin_email
                    ]
                },
                Message={
                    'Subject': {
                        'Data': 'New domains found on network',
                        'Charset': 'utf-8'
                    },
                    'Body': {
                        'Text': {
                            'Data': body,
                            'Charset': 'utf-8'
                        }
                    }
                }
            )

        print(response)
        num_domains += len(domains)

    if num_domains != len(all_domains):
        raise ValueError(f"Received invalid number of domains. Expected {len(all_domains)} but got {num_domains}")
