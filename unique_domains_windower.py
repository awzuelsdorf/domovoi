from pi_hole_admin import PiHoleAdmin
import datetime
from copy import deepcopy
import pickle
from constants import DB_FILE_NAME
import sqlite_utils

class UniqueDomainsWindower(object):
    """
    An object for maintaining the state of a window of unique domains seen in a period of time relative to now.
    This is useful for determining what domains have been seen since the current window was computed.
    """
    def __init__(self, client: PiHoleAdmin, window_size_sec: int, types: list, excluded_dns_types: list, interval_sec: int, only_domains: bool, verbose: bool, newest_bound: datetime.datetime=None, unique_domains_file: str=None):
        if window_size_sec < 0:
            raise ValueError(f"Window size in seconds is invalid, should be greater than zero but was {window_size_sec}")

        self._window_size_sec = window_size_sec

        if newest_bound is None:
            self._window_newest_bound = datetime.datetime.now(tz=datetime.timezone.utc)
        else:
            self._window_newest_bound = deepcopy(newest_bound)

        self._window_oldest_bound = self._window_newest_bound - datetime.timedelta(seconds=self._window_size_sec)

        self._types = types
        self._excluded_dns_types = excluded_dns_types
        self._interval_sec = interval_sec
        self._only_domains = only_domains
        self._verbose = verbose
        self._client = client
        self._unique_domains_file = unique_domains_file

        self._unique_domains_window = {domain: self._window_newest_bound for domain in self._client.get_unique_domains_between_times(self._window_oldest_bound, self._window_newest_bound, self._types, self._excluded_dns_types, self._interval_sec, self._only_domains, self._verbose)}

        self.save_to_file()

    @classmethod
    def _get_domains_in_interval(windower):
        if windower._types == PiHoleAdmin.ALL_PERMITTED:
            windower._unique_domains_window = {domain: windower._window_newest_bound for domain in sqlite_utils.get_domains_in_interval(DB_FILE_NAME, windower._window_oldest_bound, windower._window_newest_bound, True, False)}
        elif windower._types == PiHoleAdmin.ALL_BLOCKED:
            windower._unique_domains_window = {domain: windower._window_newest_bound for domain in sqlite_utils.get_domains_in_interval(DB_FILE_NAME, windower._window_oldest_bound, windower._window_newest_bound, False, False)}
        else:
            raise ValueError(f"unknown windower types: {windower._types}")

    @classmethod
    def deserialize(cls, client: PiHoleAdmin, unique_domains_file: str, verbose: bool=True):
        if verbose:
            print(f"Loading domains from file {unique_domains_file}")

        windower = None

        with open(unique_domains_file, 'rb') as unique_file:
            windower = pickle.load(unique_file)

        if verbose:
            print(windower.__dict__)

        windower._client = client

        UniqueDomainsWindower._get_domains_in_interval(windower)

        return windower

    def get_previously_unseen_domains(self):
        previous_domains = {key: value for key, value in self._unique_domains_window.items()}

        self.update_window()

        UniqueDomainsWindower._get_domains_in_interval(self)

        current_domains = {key: value for key, value in self._unique_domains_window.items()}

        if self._verbose:
            print(len(previous_domains))
            print(len(current_domains))

        newly_seen_domains = dict()

        for current_domain, timestamp in current_domains.items():
            if current_domain not in previous_domains:
                newly_seen_domains[current_domain] = timestamp

        if self._verbose:
            print(newly_seen_domains)

        return newly_seen_domains

    def save_to_file(self):
        # Don't save unique domains to a file since sqlite file should be
        # source of truth on what domains have been permitted and which
        # haven't.
        unique_domains = deepcopy(self._unique_domains_window)

        self._unique_domains_window = None

        if self._unique_domains_file is not None:
            print(f"Saving domains to file {self._unique_domains_file}")

            with open(self._unique_domains_file, 'wb') as unique_file:
                pickle.dump(self, unique_file)

        self._unique_domains_window = unique_domains

    def update_window(self):
        self._window_oldest_bound = deepcopy(self._window_newest_bound)

        self._window_newest_bound = datetime.datetime.now(tz=datetime.timezone.utc)

        self.save_to_file()