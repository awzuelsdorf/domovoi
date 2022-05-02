# Domovoi #

## Purpose ##

This repository has two parts. The first allows you to get text alerts sent to your mobile phone whenever your PiHole permits a DNS query for a new domain name (e.g., wikipedia.org) and whenever your PiHole blocks a DNS query for a new subdomain (e.g., zh.wikipedia.org or en.m.wikipedia.org). This way, you won't have to periodically, manually query PiHole's admin interface to see what unique DNS queries were seen in a given time frame, which can be time-consuming and often will yield no interesting results (most people don't visit new websites very often, but the manual inspection will take time regardless of whether there are interesting results or not). This can also help to quickly detect when PiHole occasionally block of necessary domains, which can cause apps or background functionality in webpages to silently fail with no obvious explanation.

The second part of this program allows you to effectively block a website based on the geographic location of the IP address returned as the response to the DNS query. For example, if you submit a DNS query for weibo.com, this will return an IP address such as 36.51.254.228. Domovoi will use IP2Location to determine what country corresponds to this IP address. The aforementioned IP address currently corresponds to Communist China. So if you were blocking DNS queries returning IP addresses in Communist China, then your DNS query to weibo.com would fail as you intended. 

## Assumptions ##

This guide assumes you are installing this software on a Raspberry Pi Zero W or 4B+ running the Raspberry Pi OS (formerly the Raspbian operating system). It also assumes you have a copy of the LITE IP-COUNTRY Database from IP2Location, available [here](https://lite.ip2location.com/database/db1-ip-country). It also assumes you have Pi-Hole installed on your raspberry pi.

## Installation ##

First, if you have not already, install [PiHole](https://docs.pi-hole.net/) on your Raspberry Pi. Make sure you make note of the password to your PiHole, since you will need it later (or for using the PiHole admin console in general).

Then, clone this repo to your home directory under the name 'domovoi' using:

```
cd ~

git clone https://github.com/awzuelsdorf/domovoi
```

Next, you will need your [twilio](https://www.twilio.com) credentials, your password to your PiHole, and the url for your PiHole's admin interface. This means that the `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE`, `ADMIN_PHONE`, `PI_HOLE_URL`, and `PI_HOLE_PW` environment variables need to be defined and exported in a file named '.twilio_creds' in your ~/domovoi directory. Example:

```
#! /bin/bash

export TWILIO_ACCOUNT_SID="<redacted"
export TWILIO_AUTH_TOKEN="<redacted>"
export TWILIO_PHONE="<redacted>" #This should be your twilio-assigned phone number
export ADMIN_PHONE="<redacted>" #This should be your phone number
export PI_HOLE_URL="http://<pi_hole_ip_address>/admin" # Note: there should be no backslash following 'admin'.
export PI_HOLE_PW="<redacted>"
```

If you want a different list of blocked countries than the one provided by default, then either update `start_interceptor.sh`'s default list of blocked countries or export the environment variable `BLOCKED_COUNTRIES_LIST` with a comma-separated list of short country codes (example: to block just Russia and Iran, use `export BLOCKED_COUNTRIES_LIST='ru,ir'` . And to block just Communist Cuba, use `export BLOCKED_COUNTRIES_LIST='cu'`).

If you stored your IP2Location database in a different directory than ~/domovoi with a different name than IP2LOCATION-LITE-DB1.BIN, then you can specify your custom directory using `export IP2LOCATION_BIN_FILE_PATH=<your_location>`. Similarly, to specify a port for your geolocation filter process to use, run `export INTERCEPTOR_PORT=<some_other_port_number>`. This is required if port 47786 is not available for use. To set the upstream DNS server's IP address and port, use `export INTERCEPTOR_UPSTREAM_DNS_SERVER_IP='<your_dns_server_ip>'` and `export INTERCEPTOR_UPSTREAM_DNS_SERVER_PORT='<your_dns_server_port>'`, respectively. 

Next, you will need to ensure virtualenv is installed. On Raspbian, this can be done by running `sudo apt install virtualenv -y`

Once virtualenv is installed, run `./setup_crontab.sh`. This may take some time since there is some one-time setup that needs to happen. Once this command finishes, there should be a 'windower_whitelist.bin' and 'windower_blacklist.bin' file in your ~/domovoi directory.

Once you've verified that the two .bin files exist, visit a website you have not visited in the last month and wait until the cron job runs at least once. It should run every 5 minutes. First it runs at the top of the hour, then five minutes past the hour, then 10 minutes past the hour, etc, if you set it up using `setup_crontab.sh`. After the first run (or second run, depending upon how close to the five-minute mark you visited the website), you should get a text at your twilio number saying that you visited at least one new domain. If you don't get the text after two runs, check the run_domain_alert.sh.log file for errors.

Once you've done this, change your DNS server entry in your Pi-Hole admin console to point at 127.0.0.1#47786 for DNS query resolution. Try visiting a website in a blocked country, either using the `ping` utility or a web browser. weibo.com, which is hosted in Communist China, is one website that should be blocked using the default block list.

## Terms of Use ##

This software relies on Twilio for sending texts. You must provide, fund, and maintain your own Twilio account, Twilio phone number, and Twilio account credentials. The maintainers of this software are not responsible for any costs incurred or damage caused by creating or using a Twilio account. The maintainers of this software make no guarantees regarding the Twilio platform, including its reliability or its availability. This software is licensed under the GNU GPL v3.0 license. Use of this software implies acceptance of the terms specified in that license, these terms of use, and the privacy section of this README.

This software uses IP2Location. Use of this software implies acceptance of all licenses and terms put forth by IP2Location.

## Privacy ##

The maintainers of this software do not collect or have access to the data this software collects. The contents of text messages sent by this software may be accessed via Twilio's web interface or by other methods. The maintainers of this software make no guarantees about the use or misuse of any data sent to Twilio, nor do the maintainers of this software make any guarantees regarding Twilio's security or privacy.

## Acknowledgements ##
This site or product includes IP2Location LITE data available from [https://lite.ip2location.com](https://lite.ip2location.com)
