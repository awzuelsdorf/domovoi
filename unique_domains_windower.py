from pi_hole_admin import PiHoleAdmin
import datetime
from copy import deepcopy
import pickle

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
    def deserialize(cls, client: PiHoleAdmin, unique_domains_file: str, verbose: bool=True):
        if verbose:
            print(f"Loading domains from file {unique_domains_file}")

        windower = None

        with open(unique_domains_file, 'rb') as unique_file:
            windower = pickle.load(unique_file)

        if verbose:
            print(windower.__dict__)

        windower._client = client

        return windower

    def get_previously_unseen_domains(self):
        previous_domains = set(self._unique_domains_window.keys())

        self.update_window()

        current_domains = set(self._unique_domains_window.keys())

        if self._verbose:
            print(len(previous_domains))
            print(len(current_domains))

        newly_seen_domains = current_domains.difference(previous_domains)

        if self._verbose:
            print(newly_seen_domains)

        return newly_seen_domains

    def save_to_file(self):
        if self._unique_domains_file is not None:
            print(f"Saving domains to file {self._unique_domains_file}")

            with open(self._unique_domains_file, 'wb') as unique_file:
                pickle.dump(self, unique_file)

    def update_window(self):
        self._window_oldest_bound = deepcopy(self._window_newest_bound)

        self._window_newest_bound = datetime.datetime.now(tz=datetime.timezone.utc)

        cutoff = self._window_newest_bound - datetime.timedelta(seconds=self._window_size_sec)

        if self._window_newest_bound - self._window_oldest_bound > datetime.timedelta(seconds=self._interval_sec):
            if self._verbose:
                print("Interval is insufficient")
            new_domains = {domain: self._window_newest_bound for domain in self._client.get_unique_domains_between_times(self._window_oldest_bound, self._window_newest_bound, self._types, self._excluded_dns_types, self._interval_sec, self._only_domains, self._verbose)}
        else:
            if self._verbose:
                print("Interval is sufficient")
            new_domains = {domain: self._window_newest_bound for domain in self._client.get_unique_domains_between_times(self._window_newest_bound - datetime.timedelta(seconds=self._interval_sec), self._window_newest_bound, self._types, self._excluded_dns_types, self._interval_sec, self._only_domains, self._verbose)}

        if self._verbose:
            print(f"Found new domains {new_domains}")

        self._unique_domains_window.update(new_domains)
        
        self._unique_domains_window = dict(filter(lambda item: item[1] >= cutoff, self._unique_domains_window.items()))

        self.save_to_file()