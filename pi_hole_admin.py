import requests
import datetime
import os
import math
import re
import bs4
import tldextract

class PiHoleAdmin(object):
    """
    An object for performing administrative tasks in PiHole including viewing queries, updating blacklists, and updating whitelists.
    """
    ALL_PERMITTED = [2, 14, 3, 12, 13]

    ALL_BLOCKED = [1, 4, 5, 6, 7, 8, 9, 10, 11, 15]

    def __init__(self, url: str, pi_hole_password_env_var: str=None, pi_hole_password: str=None):
        self._url = url
        self._php_session_id = None
        self._white_groups_domains_token = None
        self._black_groups_domains_token = None
        self._whitelist_entries = None
        self._blacklist_entries = None

        if pi_hole_password is not None:
            self._pi_hole_password = pi_hole_password
        elif pi_hole_password_env_var is not None:
            self._pi_hole_password = os.environ.get(pi_hole_password_env_var)
        else:
            raise ValueError("Invalid parameters: both pi hole password and pi hole environment variable were null!")

        if self._pi_hole_password is None:
            raise ValueError("Invalid parameters: provided parameters resulted in null password.")

    def get_php_session_id(self):
        """
        Get login session id.
        """
        if self._php_session_id is not None:
            return self._php_session_id

        response = requests.post(f"{self._url}/index.php?login=", data={"pw": self._pi_hole_password}, headers={'Content-Type': 'application/x-www-form-urlencoded'})

        session_id = re.findall(r"PHPSESSID=([a-zA-Z0-9]+);", response.headers.get('Set-Cookie', ""))

        if session_id:
            self._php_session_id = session_id[0]
        else:
            self._php_session_id = None

        return self._php_session_id

    def get_whitelist_or_blacklist_entries_containing_domain(self, domain: str, ltype: str, bust_cache: bool=False, wildcard: bool=False, only_enabled=False):
        """
        Determines whether the current whitelist or blacklist entries contain
        the proposed domain. Returns list of all matching list entries. Will
        distinguish between enabled and disabled groups if only_enabled = True
        """
        if ltype is None or ltype.lower().strip() not in ['white', 'black']:
            raise ValueError(f"Invalid list type: \"{ltype}\"")

        ltype_clean = ltype.lower().strip()

        containing_entries = []

        for entry in self.get_whitelist_or_blacklist_entries(bust_cache=bust_cache, ltype=ltype_clean, only_enabled=only_enabled):
            if ltype_clean == 'white':
                if wildcard and entry["type"] == 2 and (re.match(f".*{entry['domain']}", domain) or domain == entry["domain"]):
                    containing_entries.append(entry)
                elif not wildcard and entry["type"] == 0 and entry["domain"] == domain:
                    containing_entries.append(entry)
            else:
                if wildcard and entry["type"] == 3 and (re.match(f".*{entry['domain']}", domain) or domain == entry["domain"]):
                    containing_entries.append(entry)
                elif not wildcard and entry["type"] == 1 and entry["domain"] == domain:
                    containing_entries.append(entry)

        return containing_entries

    def get_groups_domains_token(self, ltype: str):
        """
        Retrieves groups domains token for list type. Necessary for getting data
        on which domains have been whitelisted or blacklisted.
        """
        if ltype is None or ltype.lower().strip() not in ['black', 'white']:
            raise ValueError(f"Invalid list type {ltype}")

        ltype_clean = ltype.lower().strip()

        if ltype_clean == 'white' and self._white_groups_domains_token is not None:
            return self._white_groups_domains_token

        if ltype_clean == 'black' and self._black_groups_domains_token is not None:
            return self._black_groups_domains_token

        php_session_id = self.get_php_session_id()

        if php_session_id is None:
            raise RuntimeError("Could not get PHP session id.")

        groups_domains = requests.post(f"{self._url}/groups-domains.php?type={ltype_clean}", headers={'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8', 'Cookie': f"PHPSESSID={php_session_id}", 'Upgrade-Insecure-Requests': '1', 'Cache-Control': 'max-age=0'})

        soup = bs4.BeautifulSoup(groups_domains.content, features='html.parser')

        groups_domains_token = None

        for div in soup.find_all("div", attrs={"id": "token"}):
            groups_domains_token = div.text
            break

        if ltype_clean == 'black':
            self._black_groups_domains_token = groups_domains_token
            return self._black_groups_domains_token

        if ltype_clean == 'white':
            self._white_groups_domains_token = groups_domains_token
            return self._white_groups_domains_token

        return None

    def _printv(self, msg, verbose):
        if verbose:
            print(msg)

    def get_whitelist_or_blacklist_entries(self, ltype: str, bust_cache: bool=False, only_enabled=False):
        """
        Get entries from whitelist if list type `ltype` is 'white' or blacklist
        if list type `ltype` is 'black'.
        """
        if ltype is None or ltype.lower().strip() not in ['white', 'black']:
            raise ValueError(f"Invalid list type: \"{ltype}\"")

        ltype_clean = ltype.lower().strip()

        if not bust_cache:
            if ltype_clean == 'white' and self._whitelist_entries is not None:
                return self._whitelist_entries

            if ltype_clean == 'black' and self._blacklist_entries is not None:
                return self._blacklist_entries

            return None

        php_session_id = self.get_php_session_id()

        if php_session_id is None:
           raise RuntimeError("Could not get PHP session id.")

        groups_domains_token = self.get_groups_domains_token(ltype=ltype_clean)

        if groups_domains_token is None:
            raise RuntimeError("Groups domains token not found.")

        response = requests.post(f"{self._url}/scripts/pi-hole/php/groups.php", headers={'Accept': 'application/json', 'Content-Type': 'application/x-www-form-urlencoded', 'Cookie': f"PHPSESSID={php_session_id}"}, data={'action': 'get_domains', 'showtype': ltype_clean, 'token': groups_domains_token})

        response_json = response.json()

        if ltype_clean == 'white':
            self._whitelist_entries = [datum for datum in response_json.get("data", []) if not only_enabled or int(datum['enabled']) != 0]

            return self._whitelist_entries
        if ltype_clean == 'black':
            self._blacklist_entries = [datum for datum in response_json.get("data", []) if not only_enabled or int(datum['enabled']) != 0]

            return self._blacklist_entries

        return None

    def enable_domain_on_list(self, entry, ltype, groups="0"):
        """
        Enable domain on whitelist or blacklist. Assumes domain is already present in the list.
        """
        if ltype is None or ltype.lower().strip() not in ['white', 'black']:
            raise ValueError(f"Invalid list type {ltype}")

        ltype_clean = ltype.lower().strip()

        headers = {'Accept': 'application/json, text/javascript, */*; q=0.01', 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8', 'Cookie': f"PHPSESSID={self.get_php_session_id()}"}

        data = {'action': 'edit_domain', 'id': entry["id"], 'type': entry['type'], 'comment': entry['comment'], 'status': '1', 'groups[]': groups, 'token': self.get_groups_domains_token(ltype_clean)}

        response = requests.post(f"{self._url}/scripts/pi-hole/php/groups.php", headers=headers, data=data)

        response_json = response.json()

        return response_json

    def add_domain_to_list(self, domain: str, ltype: str, wildcard: bool=False, comment: str="Added by PiHoleAdmin", verbose: bool=False):
        """
        Add domain to list if it's not there or enables it if it isn't present already. Return response dict
        """
        if ltype is None or ltype.lower().strip() not in ['black', 'white']:
            raise ValueError(f"Invalid list type {ltype}")

        ltype_clean = ltype.lower().strip()

        php_session_id = self.get_php_session_id()

        if php_session_id is None:
            raise RuntimeError("Could not get PHP session id.")

        groups_domains_token = self.get_groups_domains_token(ltype_clean)

        if groups_domains_token is None:
            raise RuntimeError("Group domains token not found.")

        list_groups = self.get_whitelist_or_blacklist_entries_containing_domain(domain, ltype_clean, bust_cache=True, wildcard=wildcard)

        enabled_list_groups = [group for group in list_groups if group["enabled"] != 0]
        disabled_list_groups = [group for group in list_groups if group["enabled"] == 0]

        # If adding a wildcarded domain, then add the domain only if there are
        # no list groups containing that wildcarded domain already.
        # If adding a non-wildcarded domain, then add the domain only if there
        # are no containing list groups that aren't regexes.
        if not wildcard:
            disabled_groups = [group for group in disabled_list_groups if group['type'] == 0 or group['type'] == 1]
            enabled_groups = [group for group in enabled_list_groups if group['type'] == 0 or group['type'] == 1]
        else:
            disabled_groups = disabled_list_groups
            enabled_groups = enabled_list_groups

        if enabled_groups:
            self._printv(f"Not adding domain {domain} with wildcard {wildcard}, already in group(s): {enabled_groups}.", verbose)

            return {"success": True, "message": f"Domain already contained in groups {', '.join([g['domain'] for g in enabled_groups])}"}
        elif disabled_groups:
            self._printv(f"Enabling domain {domain} with wildcard {wildcard}, already in disabled group: {disabled_groups[0]}.", verbose)

            return self.enable_domain_on_list(disabled_groups[0], ltype_clean)
        else:
            self._printv(f"Adding domain {domain} with wildcard {wildcard} since it is not in an enabled or disabled whitelisted group.", verbose)

            etype = None

            if wildcard:
                if ltype_clean == 'white':
                    etype = '2W'
                else:
                    etype = '3W'
            else:
                if ltype_clean == 'white':
                    etype = '0'
                else:
                    etype = '1'

            try:
                response = requests.post(f"{self._url}/scripts/pi-hole/php/groups.php", headers={'Accept': 'application/json, text/javascript, */*; q=0.01', 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8', 'Cookie': f"PHPSESSID={php_session_id}"}, data={'action': 'add_domain', 'domain': domain, 'type': etype, 'comment': comment, 'token': groups_domains_token})

                return response.json()
            except BaseException as be:
                return {"success": False, "message": f"Received exception '{be}'"}

    def remove_domain_from_list(self, domain: str, ltype: str, wildcard: bool=False, verbose: bool=False):
        """
        Remove domain from list if it's there. Return response dict
        """
        if ltype is None or ltype.lower().strip() not in ['black', 'white']:
            raise ValueError(f"Invalid list type {ltype}")

        ltype_clean = ltype.lower().strip()

        php_session_id = self.get_php_session_id()

        if php_session_id is None:
            raise RuntimeError("Could not get PHP session id.")

        groups_domains_token = self.get_groups_domains_token(ltype_clean)

        if groups_domains_token is None:
            raise RuntimeError("Group domains token not found.")

        list_groups = self.get_whitelist_or_blacklist_entries_containing_domain(domain, ltype_clean, bust_cache=True, wildcard=wildcard)

        # If adding a wildcarded domain, then add the domain only if there are
        # no list groups containing that wildcarded domain already.
        # If adding a non-wildcarded domain, then add the domain only if there
        # are no containing list groups that aren't regexes.
        if not wildcard:
            groups = [group for group in list_groups if group['type'] == 0 or group['type'] == 1]
        else:
            groups = list_groups

        if groups:
            self._printv(f"Removing domain {domain} with wildcard {wildcard}, already in group: {groups[0]}.", verbose)

            try:
                return requests.post(f"{self._url}/scripts/pi-hole/php/groups.php", headers={'Accept': 'application/json, text/javascript, */*; q=0.01', 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8', 'Cookie': f"PHPSESSID={php_session_id}"}, data={'action': 'delete_domain', 'id': groups[0]['id'], 'token': groups_domains_token}).json()
            except BaseException as be:
                return {'success': False, 'message': f"Received exception {be}"}
        else:
            return {"success": True, "message": f"Domain {domain} already not in groups."}

    def get_queries_between_times(self, from_time: datetime.datetime, until_time: datetime.datetime, types: list, interval_sec: int=3600, verbose: bool=False):
        """
        Gets all queries of the specified types that happened at/after
        `from_time` and before/at `until_time`.
        """
        queries = list()

        until_time_sec = int(until_time.timestamp())

        from_time_sec = int(from_time.timestamp())

        number_of_intervals = int(math.ceil((until_time_sec - from_time_sec) / interval_sec))

        for interval in range(number_of_intervals):
            t0_sec = interval * interval_sec + from_time_sec
            t1_sec = min(t0_sec + interval_sec, until_time_sec)

            self._printv(f"{t0_sec}, {t1_sec}, {from_time_sec}, {until_time_sec}", verbose)

            url = f"{self._url}/api_db.php?getAllQueries&from={t0_sec}&until={t1_sec}&types={','.join([str(type_i) for type_i in types])}"

            php_session_id = self.get_php_session_id()

            if php_session_id is None:
                raise RuntimeError("Could not get PHP session id.")

            r = requests.get(url, headers={'Content-Type': "application/json", 'Accept': 'application/json', 'Cookie': f"PHPSESSID={php_session_id}"})

            if r.status_code != 200:
                data = dict()
            else:
                data = r.json()

            queries.extend(data.get("data", []))

        return queries

    def get_unique_queries_between_times(self, from_time: datetime.datetime, until_time: datetime.datetime, types: list, excluded_dns_types: list, interval_sec: int=3600, verbose: bool=False):
        """
        Get unique queries (based on the 5-tuple of DNS record type, FQDN,
        client IP address, query status, and DNS server).
        """

        queries = self.get_queries_between_times(from_time, until_time, types, interval_sec=interval_sec, verbose=verbose)

        unique_queries = dict()

        for query in queries:
            if query[1] in excluded_dns_types:
                continue

            key = "".join([str(q) for q in query[1:]])

            if key not in unique_queries:
                unique_queries[key] = {"record": query[1:], "count": 0}

            unique_queries[key]["count"] += 1

        return list(unique_queries.values())

    def get_unique_domains_between_times(self, from_time: datetime.datetime, until_time: datetime.datetime, types: list, excluded_dns_types: list, interval_sec: int=3600, only_domains: bool=True, verbose: bool=False):
        """
        Gets a list of unique domains that fit the given types and were seen between `from_time` and `until_time`
        """
        queries = self.get_unique_queries_between_times(from_time, until_time, types, excluded_dns_types, interval_sec=interval_sec, verbose=verbose)

        unique_domains = set()

        for query in queries:
            if not only_domains:
                unique_domains.add(query['record'][1])
            else:
                result = tldextract.extract(query['record'][1])

                if result.suffix is not None and result.suffix.strip() != '':
                    unique_domains.add(f"{result.domain}.{result.suffix}")

        return unique_domains

    def get_unique_new_domains_between_times(self, new_domains_start_time: datetime.datetime, new_domains_until_time: datetime.datetime, old_domains_until_time: datetime.datetime, types: list, excluded_dns_types: list, interval_sec: int=3600, only_domains: bool=True, verbose: bool=False):
        """
        Returns a list of unique domains that were seen between
        `new_domains_start_time` and `new_domains_until_time`
        but were not seen after `new_domains_until_time` and
        before `old_domains_until_time`.
        """

        new_unique_domains = self.get_unique_domains_between_times(new_domains_start_time, new_domains_until_time, types, excluded_dns_types, interval_sec, only_domains, verbose)
        old_unique_domains = self.get_unique_domains_between_times(old_domains_until_time, new_domains_start_time, types, excluded_dns_types, interval_sec, only_domains, verbose)

        return new_unique_domains.difference(old_unique_domains)