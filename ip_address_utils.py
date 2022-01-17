"""
Copyright 2021 Andrew Zuelsdorf
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
    http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import functools
import itertools

cache = dict()

def get_value(ip_addr):
    """
    Converts IP address to its numeric value.
    """

    ip_num_value = 0

    ip_octets = list(reversed(ip_addr.split(".")))

    for exponent in range(0, 4, 1):
        ip_num_value += int(ip_octets[exponent]) * (1 << (exponent << 3))

    return ip_num_value

def get_min_value(prefix, mask):
    """
    Gets numeric value of minimum IP address in an IP CIDR with prefix
    `prefix` and mask `mask`.
    """
    ip_num_value = get_value(prefix)

    mask_value = sum([(1 << i) for i in range(32 - mask, 32)])

    return ip_num_value & mask_value

def get_max_value(min_value, mask):
    """
    Gets numeric value of maximum IP address in an IP CIDR with prefix
    `prefix` and mask `mask`.
    """
    max_value = min_value

    for i in range(32 - mask):
        max_value += (1 << i)

    return max_value

def ip_cidr_to_ip_value_range(ip_cidr):
    """
    Gets numeric value of min and max IP address in an IP CIDR with prefix
    `prefix` and mask `mask`.
    """
    prefix, mask = ip_cidr.split("/")

    min_value = get_min_value(prefix, int(mask))
   
    max_value = get_max_value(min_value, int(mask))

    return (min_value, max_value)

def ip_cidr_to_ip_range(ip_cidr):
    """
    Gets minimum and maximum IP addresses in IP CIDR `ip_cidr`
    """
    min_value, max_value = ip_cidr_to_ip_value_range(ip_cidr)

    min_ip_addr = value_to_ip(min_value)
    max_ip_addr = value_to_ip(max_value)

    return (min_ip_addr, max_ip_addr)

def is_ip_in_cidr(ip_addr, ip_cidr):
    """
    Returns true if IP address `ip_addr` is in the IP CIDR `ip_cidr`
    Returns false if IP address `ip_addr` is not in the IP CIDR `ip_cidr`
    """
    value_range = ip_cidr_to_ip_value_range(ip_cidr)

    ip_addr_value = get_value(ip_addr)

    return ip_addr_value >= value_range[0] and ip_addr_value <= value_range[1]

def value_to_ip(value):
    """
    Converts numeric value to an IP address and returns the result.
    """
    octets = list()

    v1 = sum([(1 << i) for i in range(8)])

    for i in range(0, 32, 8):
        v2 = (v1 << i)
        octet = (value & v2) // (1 << i)

        octets.append(str(octet))

    return ".".join(reversed(octets))

def get_ip_cidr_from_ips(ip_addrs):
    """
    Gets the minimal IP CIDR that includes a collection of IP addresses
    """

    values = [get_value(ip_addr) for ip_addr in ip_addrs]

    if all([ip_addr_1 == ip_addr_2 for (ip_addr_1, ip_addr_2) in itertools.product(values, values)]):
        return f"{ip_addrs[0]}/32"

    i = 32

    mask = 0

    while i > 0:
        i -= 1

        if any([(value_1 & (1 << i)) != (value_2 & (1 << i)) for (value_1, value_2) in itertools.product(values, values)]):
            break

        mask += (1 << i)

    prefix = mask & values[0]

    return f"{value_to_ip(prefix)}/{32 - (i + 1)}"

def compare_ip_address_ranges(ip_range_1, ip_range_2):
    """
    Returns value determined by comparing lower bound of ip_range_1 to lower IP
    bound of ip_range_2, conceptually comparing the lower bounds' octets'
    numeric values from left to right.
    """
    return get_value(ip_range_1[0]) - get_value(ip_range_2[0])

def ip_ranges_overlap(ip_range_1, ip_range_2):
    """
    Returns True if IP ranges overlap, False otherwise.
    """
    return get_value(ip_range_1[1]) >= get_value(ip_range_2[0]) and get_value(ip_range_2[1]) >= get_value(ip_range_1[0])

def sort_ip_address_ranges(ip_ranges):
    """
    Sort IP address ranges by comparing octets of lower bounds to IP ranges.
    """
    return sorted(ip_ranges, key=functools.cmp_to_key(compare_ip_address_ranges))

def combine_ip_ranges(ip_range_1, ip_range_2):
    """
    Combines two IP ranges.
    """

    if get_value(ip_range_1[0]) < get_value(ip_range_2[0]):
        min_ip_range = ip_range_1[0]
    else:
        min_ip_range = ip_range_2[0]

    if get_value(ip_range_1[1]) > get_value(ip_range_2[1]):
        max_ip_range = ip_range_1[1]
    else:
        max_ip_range = ip_range_2[1]

    return [min_ip_range, max_ip_range]

def consolidate_ip_ranges(ip_ranges):
    """
    Compute IP ranges, sort IP ranges, combine them by comparing the next
    unprocessed range with only the last range added to the overall list of
    non-overlapping ranges and adding to list if no overlap and combining with
    previously added range if there is overlap.
    """
    consolidated_ranges = []

    #print('\n'.join([str(_) for _ in sort_ip_address_ranges(ip_ranges)]))

    for index, ip_range in enumerate(sort_ip_address_ranges(ip_ranges)):
        last_consolidated_range = consolidated_ranges[-1] if consolidated_ranges else None

        if last_consolidated_range and ip_ranges_overlap(ip_range, last_consolidated_range):
            #print(f"Found overlapping ranges: {ip_range} and {last_consolidated_range}")
            consolidated_ranges.pop()
            consolidated_ranges.append(combine_ip_ranges(ip_range, last_consolidated_range))
        else:
            #print(f"Found no overlapping range: {ip_range} and {last_consolidated_range}")
            consolidated_ranges.append(ip_range)

    return consolidated_ranges

def consolidate_ip_cidrs(ip_cidrs):
    ip_ranges = [ip_cidr_to_ip_range(ip_cidr) for ip_cidr in ip_cidrs]

    print(f"Converted {len(ip_cidrs)} IP CIDRs to {len(ip_ranges)} IP ranges")

    consolidated_ranges = consolidate_ip_ranges(ip_ranges)

    return [get_ip_cidr_from_ips(ip_range) for ip_range in consolidated_ranges]

def main():
    ip_cidr = "210.105.44.170/21" 
    ip_addr = "210.105.41.0"

    print(is_ip_in_cidr(ip_addr, ip_cidr))

    ip_range = ip_cidr_to_ip_range(ip_cidr)

    print(ip_range)

    print(get_ip_cidr_from_ips(["192.168.43.0", "192.168.44.0", "192.168.45.0"]))
    print(get_ip_cidr_from_ips(["1.2.3.4", "1.2.3.4"]))
    print(get_ip_cidr_from_ips(["254.0.0.0", "254.255.255.255"]))
    print(get_ip_cidr_from_ips(["224.255.255.255", "0.0.0.0"]))
    print(get_ip_cidr_from_ips(["2.255.2.3", "2.0.3.4", "2.30.4.5"]))
    print(get_ip_cidr_from_ips("1.2.3.4 - 1.2.3.4\n".split(" - ")))
    print(get_ip_cidr_from_ips("1.2.3.4 - 1.2.3.5".split(" - ")))

if __name__ == "__main__":
    main()
