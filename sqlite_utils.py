import sqlite3
import twilio_utils
import os
import ses_utils

def get_domains_in_interval(domain_data_db_file, oldest_timestamp, newest_timestamp, permitted, new_only):
    if new_only:
        if permitted:
            query = """select domain from domain_actions where permitted = ? group by domain having min(first_time_seen) >= ? and min(first_time_seen) <= ?"""
        else:
            query = """select name as domain from domain_actions where permitted = ? and first_time_seen >= ? and first_time_seen <= ?"""
    else:
        if permitted:
            query = """select domain from domain_actions where permitted = ? group by domain having min(last_time_seen) >= ? and min(last_time_seen) <= ?"""
        else:
            query = """select name as domain from domain_actions where permitted = ? and last_time_seen >= ? and last_time_seen <= ?"""

    domains = list()

    with sqlite3.connect(domain_data_db_file) as cursor:
        cursor.row_factory = sqlite3.Row
        result = cursor.execute(query, (permitted, oldest_timestamp, newest_timestamp))

        domains = [row['domain'] for row in result]

    return domains

def notify_of_new_domains_in_interval_twilio(domain_data_db_file, oldest_timestamp, newest_timestamp, permitted, admin_phone, twilio_phone):
    previously_unseen_domains = get_domains_in_interval(domain_data_db_file, oldest_timestamp, newest_timestamp, permitted, True)

    twilio_utils.notify_of_new_domains(previously_unseen_domains, admin_phone, twilio_phone, blocked=not permitted)

def notify_of_new_domains_in_interval_ses(domain_data_db_file, oldest_timestamp, newest_timestamp, permitted, admin_email):
    previously_unseen_domains = get_domains_in_interval(domain_data_db_file, oldest_timestamp, newest_timestamp, permitted, True)

    ses_utils.notify_of_new_domains(previously_unseen_domains, admin_email, blocked=not permitted)

def notify_of_new_domains_in_interval(domain_data_db_file, oldest_timestamp, newest_timestamp, permitted, admin_phone=None, twilio_phone=None, admin_email=None):
    if os.environ['NOTIFY_METHOD'].upper() == 'TWILIO':
        notify_of_new_domains_in_interval_twilio(domain_data_db_file, oldest_timestamp, newest_timestamp, permitted, admin_phone, twilio_phone)
    if os.environ['NOTIFY_METHOD'].upper() == 'SES':
        notify_of_new_domains_in_interval_ses(domain_data_db_file, oldest_timestamp, newest_timestamp, permitted, admin_email)

def log_reason(domain_data_db_file, values_dicts, updateable_fields=None):
    """
    Log reason for blocking/allowing a domain
    """
    required_fields = ['domain', 'name', 'first_time_seen', 'last_time_seen', 'permitted', 'reason']

    # Sanity checks
    for values_dict in values_dicts:
        for field in required_fields:
            if field not in values_dict:
                raise ValueError(f"Missing field \"{field}\" from record {values_dict}")

    if updateable_fields:
        for updateable_field in updateable_fields:
            if updateable_field not in required_fields:
                raise ValueError(f"Updateable field {updateable_field} is not in required fields {required_fields}")

    with sqlite3.connect(domain_data_db_file) as cursor:
        cursor.execute('''CREATE TABLE IF NOT EXISTS domain_actions 
                        (name TEXT PRIMARY KEY, 
                        domain TEXT, 
                        first_time_seen TIMESTAMP WITH TIME ZONE,
                        last_time_seen TIMESTAMP WITH TIME ZONE,
                        permitted BOOLEAN,
                        reason TEXT)''')

        if updateable_fields:
            command = 'INSERT INTO domain_actions (' + (', '.join(required_fields)) + ') VALUES (' + (', '.join(['?' for _ in required_fields])) + ') ON CONFLICT (name) DO UPDATE SET ' + (", ".join([f"{field} = CASE WHEN domain_actions.last_time_seen < EXCLUDED.last_time_seen THEN EXCLUDED.{field} ELSE domain_actions.{field} END" for field in updateable_fields]))
        else:
            command = 'INSERT INTO domain_actions (' + (', '.join(required_fields)) + ') VALUES (' + (', '.join(['?' for _ in required_fields])) + ') ON CONFLICT DO NOTHING'

        print(f"Running command \"{command}\"")

        for values_dict in values_dicts:
            print(f"Processing values dict {values_dict}")
            values_tuple = tuple([values_dict[field] for field in required_fields])
            print(f"Executing command with values tuple {values_tuple}")
            cursor.execute(command, values_tuple)
            print(f"Executed command with values tuple {values_tuple}")

        print("Committing results")
        cursor.commit()
        print("Committed results")
