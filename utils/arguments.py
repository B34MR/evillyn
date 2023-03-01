#!/usr/bin/env python3

import sys
import argparse
from argparse import RawTextHelpFormatter

# Custom usage / help menu.
class HelpFormatter(argparse.HelpFormatter):
    def add_usage(self, usage, actions, groups, prefix=None):
        if prefix is None:
            prefix = ''
        return super(HelpFormatter, self).add_usage(
            usage, actions, groups, prefix)


# Custom help menu.
custom_usage = f"""
  
Evil-Lyn
{'-'*100}\n
Usage Examples: 
  python evillyn.py -i wlan0 -e 'Contoso' -m AA:AA:AA:FF:FF:FF -c 4 --company 'Contoso, Ltd.' --band b
  
"""

# Define parser
parser = argparse.ArgumentParser(formatter_class=HelpFormatter, description='', usage=custom_usage, add_help=False)

# Mode-Select Options.
# mode_group = parser.add_argument_group('Modes')
# mode_group.add_argument('mode', type=str.lower, default='eviltwin', choices=['eviltwin'], metavar='{eviltwin, scan}', help='Set mode [eviltwin]')

# Interface Options.
interface = parser.add_argument_group('Interface Arguments')
interface.add_argument('-i', dest='interface', type=str, required=True, default='wlan0', metavar='', help='Set interface [wlan0]')
interface.add_argument('-m', dest='interface_mac', type=str, default='', metavar='', help='Set interface MAC [FF:FF:FF:00:00:00]')
interface.add_argument('--reg', dest='interface_reg', type=str.upper, default='US', choices=['US', 'GY'], metavar='', help='Set inteface Regulatory Domain [US]')
interface.add_argument('--txpower', dest='interface_txpower', type=int, default='30', metavar='', help='Set interface TX Power [30]')

# Hostapd Options.
hostpad_group = parser.add_argument_group('Hostapd Arguments')
hostpad_group.add_argument('-c', dest='hostapd_channel', type=int, default=4, metavar='', help='Set Hostapd Channel [4]')
hostpad_group.add_argument('-e', dest='hostapd_essid', type=str, default='Contoso wireless', metavar='', help='Set Hostapd ESSID [Contoso, Ltd.]')
hostpad_group.add_argument('--band', dest='hostapd_band', type=str.upper, default='B', choices=['A', 'B', 'G'], metavar='{A, B, G}', help='Set Hostpad wireless band [B]')
hostpad_group.add_argument('--cc', dest='hostapd_cc', type=str.upper, default='US', choices=['US', 'GY'], metavar='', help='Set Hostapd Country Code [US]')

# Hostapd Adv Options
# hostpad_group.add_argument('--server_cert', type=str, metavar='Default [data/certs/server_cert.pem]', default='data/certs/server_cert.pem', help='')
# hostpad_group.add_argument('--private_key', type=str, metavar='Default [data/certs/private_key.pem]', default='data/certs/private_key.pem', help='')
# hostpad_group.add_argument('--debug', action='store_true', default ='', help='Set Hostapd debug output on/off') # Dev - implement.

# OpenSSL Options.
openssl_group = parser.add_argument_group('OpenSSL Arguments')
openssl_group.add_argument('--country', dest='openssl_country', type=str, default='US', metavar='', help='Set certificate Country [US]')
openssl_group.add_argument('--state', dest='openssl_state', type=str, default='CA', metavar='',  help='Set certificate State [CA]')
openssl_group.add_argument('--city',dest='openssl_city', type=str,  default='San Diego', metavar='', help='Set certificate City [San Diego]')  
openssl_group.add_argument('--company', dest='openssl_company', type=str,  default='Contoso', metavar='',help='Set certificate Company Name [Contoso]')
openssl_group.add_argument('--ou', dest='openssl_ou', type=str, default='Contoso, Ltd.', metavar='',  help='Set certificate Organizational Unit (OU) [Contoso, Ltd.]')
openssl_group.add_argument('--email', dest='openssl_email', type=str, default='info@contoso.com', metavar='', help='Set certificate Email [info@contoso.com]')

# Global Options.
group1 = parser.add_argument_group('Global Arguments')
group1.add_argument('--database', dest='database',  type=str, default='.evillyn.db', help='Specifty database filepath [.evillyn.db]')
group1.add_argument('--debug', dest='loglevel', action='store_true', help='Set logging level [DEBUG]')
group1.add_argument('--droptables', dest='droptables', action='store_true', help='Drop all database tables')
group1.add_argument('--minimal', dest='minimal', action='store_true', help='Disable DBmanager and Prettify mode')
group1.add_argument('--runtime', dest='runtime', type=int, default=float("inf"), help='Set Runtime duration in seconds')


# Print 'help' if no options are defined.
if len(sys.argv) == 1 \
or sys.argv[1] == '-h' \
or sys.argv[1] == '--help':
  parser.print_help(sys.stderr)
  sys.exit(1)


if __name__ == "__main__":
    main()