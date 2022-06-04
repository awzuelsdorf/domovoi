import sqlite3
import twilio_utils

def notify_of_new_domains_in_interval(domain_data_db_file, oldest_timestamp, newest_timestamp, permitted, admin_phone, twilio_phone):
    query = """select domain from domain_actions where first_time_seen >= ? and first_time_seen <= ? and permitted = ?"""

    with sqlite3.connect(domain_data_db_file) as cursor:
        cursor.row_factory = sqlite3.Row
        result = cursor.execute(query, (oldest_timestamp, newest_timestamp, permitted))

        previously_unseen_domains = [row['domain'] for row in result]

        twilio_utils.notify_of_new_domains(previously_unseen_domains, admin_phone, twilio_phone, blocked=not permitted)


def log_reason(domain_data_db_file, values_dicts, updateable_fields=None):
    """
    Log reason for blocking/allowing a domain
    """
    required_fields = ['domain', 'first_time_seen', 'last_time_seen', 'permitted', 'reason']

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
                        (domain TEXT PRIMARY KEY, 
                        first_time_seen TIMESTAMP WITH TIME ZONE,
                        last_time_seen TIMESTAMP WITH TIME ZONE,
                        permitted BOOLEAN,
                        reason TEXT)''')

        if updateable_fields:
            command = 'INSERT INTO domain_actions (' + (', '.join(required_fields)) + ') VALUES (?, ?, ?, ?, ?) ON CONFLICT (domain) DO UPDATE SET ' + (", ".join([f"{field} = CASE WHEN domain_actions.last_time_seen < EXCLUDED.last_time_seen THEN EXCLUDED.{field} ELSE domain_actions.{field} END" for field in updateable_fields]))
        else:
            command = 'INSERT INTO domain_actions (' + (', '.join(required_fields)) + ') VALUES (?, ?, ?, ?, ?) ON CONFLICT DO NOTHING'

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
