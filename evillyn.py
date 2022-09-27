#!/usr/bin/env python3

from utils import arguments
from utils import channels
from utils import hostapd
from utils import interface
from utils import mkdir
from utils import openssl
from configparser import ConfigParser, ExtendedInterpolation
import asyncio
import os
import sys
import re
import logging
import time


# Argparse - Init and parse.
args = arguments.parser.parse_args()

# Argparse - runtime.
# DEV - may move this into config.ini
args_runtime = args.runtime
args_rounds = args.rounds
args_sleep = args.sleep

# Rich - enabled/disable graphical mode. # DEV
if not args.nographic:
	from utils import richard as r

# ConfigParser - init and defined instance options.
config_obj = ConfigParser(
	allow_no_value=True,
	delimiters='=',
	interpolation=ExtendedInterpolation(),
	)
# ConfigParser - enabled case sensitive.
config_obj.optionxform = str

# Application - directories and filepaths.
APPLICATION_FP = __file__
APPLICATION_DIR = os.path.dirname(__file__)

# Relative directories and filepaths.
CONFIGS_DIR = 'configs'
TEMPLATES_DIR = 'templates'
TEMPLATE_HOSTAPD_FP = os.path.join(TEMPLATES_DIR, 'hostapd-wpe.conf')
OPENSSL_CERTS_DIR = os.path.join(CONFIGS_DIR, 'openssl_certificates')
HOSTAPD_CONF_DIR = os.path.join(CONFIGS_DIR, 'hostapd_conf')
RESULTS_DIR = 'results'
# HOSTAPD_CONF_FP = os.path.join(HOSTAPD_CONF_DIR, '') # DEV - may change this to a static filename convention.
# HOSTAPD_EAPUSER_TEMPLATE = f'configs/.hostapd_conf_source/eapuser_default' # DEV - research this.

# Absolute directories and filepaths.
configini_fp = os.path.join(CONFIGS_DIR, f'config.ini')
hostapd_log_fp = os.path.join(APPLICATION_DIR, RESULTS_DIR, '')
hostapd_servercert_fp = os.path.join(APPLICATION_DIR, OPENSSL_CERTS_DIR, 'cert.pem')
hostapd_privatekey_fp = os.path.join(APPLICATION_DIR, OPENSSL_CERTS_DIR, 'cert.key')

# Application - create required dirs.
directories = [CONFIGS_DIR, OPENSSL_CERTS_DIR, HOSTAPD_CONF_DIR, RESULTS_DIR, TEMPLATES_DIR]
dirs = [mkdir.mkdir(directory) for directory in directories]
if args.loglevel == 'info'.upper():
	[print(f'[*] Created directory: {d}') for d in dirs if d is not None]

# Third Party application versions.
hostapd.Hostapd.get_version()
openssl.OpenSSL.get_version()
interface.Interface.macchanger_version()

# Third Party application filepaths.
hostapd.Hostapd.get_filepath()
openssl.OpenSSL.get_filepath()
interface.Interface.macchanger_filepath()


def update_config_obj():
	''' Update ConfigParser's 'config_obj' object from cmdline argument values. '''

	# ConfigParser - default dict.
	config_obj['Main'] = {
		'hostapd_filepath':HOSTAPD_CONF_DIR + '/${Hostapd:essid}.conf'
		}
	# ConfigParser - interface dict.
	config_obj['Interface'] = {	
		'interface':f'{args.interface}',
		'bssid':f'{args.interface_mac}',
		'tx_power':f'{args.interface_txpower}',
		'regulatory_domain':f'{args.interface_reg}'
		}
	# ConfigParser - openssl dict.
	config_obj['OpenSSL'] = {
		'country':f'{args.openssl_country}',
		'state':f'{args.openssl_state}',
		'city':f'{args.openssl_city}',
		'company':f'{args.openssl_company}',
		'ou':f'{args.openssl_ou}',
		'email':f'{args.openssl_email}',
		'cert_pem_filepath':f'{hostapd_servercert_fp}',
		'cert_key_filepath':f'{hostapd_privatekey_fp}'
		}
	# ConfigParser - hostapd dict.
	config_obj['Hostapd'] = {
		'interface':f'{args.interface}',
		'channel':f'{args.hostapd_channel}',
		'band':f'{args.hostapd_band.lower()}',
		'essid':f'{args.hostapd_essid}',
		'country_code':f'{args.hostapd_cc}',
		'logfile':f'{hostapd_log_fp}' + '${Hostapd:essid}.log',
		'cert_pem_filepath':f'{hostapd_servercert_fp}',
		'cert_key_filepath':f'{hostapd_privatekey_fp}',
		# 'eap_user_file':f'{eapuser_template}' # DEV
		}
	return config_obj


def write_config_obj_to_file(config_obj, output_file):
	''' Write ConfigParser's 'config_obj' object to a file. 
		arg(s) config_obj:ConfigParser-Object, filename:str
		Return config.ini filename. '''

	with open(output_file, 'w') as f1:
		config_obj.write(f1)
	return f1.name


def write_hostapd(config_obj, input_file, output_file):
	''' DEV '''
	
	# ConfigParser - read Hostpad dict
	hostapd_dic = {k: v for k, v in config_obj['Hostapd'].items()}

	with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
		lines = infile.readlines()
		lines[3] = f"interface={hostapd_dic['interface']}\n"
		# lines[6] = f"eap_user_file={hostapd_dic['eap_user_file']}\n"
		lines[8] = f"server_cert={hostapd_dic['cert_pem_filepath']}\n"
		lines[9] = f"private_key={hostapd_dic['cert_key_filepath']}\n"
		lines[14] = f"ssid={hostapd_dic['essid']}\n"
		lines[15] = f"channel={hostapd_dic['channel']}\n"
		lines[19] = f"wpe_logfile={hostapd_dic['logfile']}\n"
		lines[146] = f"country_code={hostapd_dic['country_code']}\n"
		lines[183] = f"hw_mode={hostapd_dic['band']}\n"
		outfile.writelines(lines)
	return outfile.name


def main():

	# Evil-lyn - write ConfigParser 'config.ini' file.
	print('\n')
	print('-'*100)

	# Evil-lyn - update ConfigParser object.
	try:
		config_obj = update_config_obj()
	except Exception as e:
		logging.error(f'{e}')
		sys.exit(1)
	else:
		# Main
		hostapd_conf_fp = config_obj['Main']['hostapd_filepath']
		# Inteface
		ifname_01 = config_obj['Interface']['interface']
		bssid = config_obj['Interface']['bssid']
		regulatory_domain = config_obj['Interface']['regulatory_domain']
		tx_power = config_obj['Interface']['tx_power']
		# OpenSSL
		openssl_country = config_obj['OpenSSL']['country']
		openssl_state = config_obj['OpenSSL']['state']
		openssl_city = config_obj['OpenSSL']['city']
		openssl_company = config_obj['OpenSSL']['company']
		openssl_ou = config_obj['OpenSSL']['ou']
		openssl_email = config_obj['OpenSSL']['email']
		openssl_certpem_fp = config_obj['OpenSSL']['cert_pem_filepath']
		openssl_certkey_fp = config_obj['OpenSSL']['cert_key_filepath']
		# Hostapd
		if args.loglevel == 'info'.upper():
			print(f'[*] Updated ConfigParser Object from cmdline arguments:')

	# Evil-lyn - write ConfigParser 'config.ini' file.
	try:
		results = write_config_obj_to_file(config_obj, configini_fp)
	except Exception as e:
		logging.error(f'{e}')
		sys.exit(1)
	else:
		if args.loglevel == 'info'.upper():
			print(f'[*] Created ConfigParser ini file: {results}')

	# Evil-lyn - write hostapd.conf file.
	try:
		results = write_hostapd(config_obj, TEMPLATE_HOSTAPD_FP, hostapd_conf_fp)
	except Exception as e:
		logging.error(f'{e}')
		sys.exit(1)
	else:
		if args.loglevel == 'info'.upper():
			print(f'[*] Created Hostapd Configuration file: {results}\n')

	# OpenSSL - write certficate files.
	print('-'*100)
	try:
		create_certificate = openssl.OpenSSL(openssl_country, openssl_state, openssl_city, openssl_company, 
			openssl_ou, openssl_email, openssl_certpem_fp, openssl_certkey_fp)
		openssl_results = create_certificate.run()
	except Exception as e:
		logging.error(f'{e}')
		sys.exit(1)
	else:
		openssl_cmd = ' '.join(openssl_results[0])
		openssl_stderr = openssl_results[2]
		# OpenSSL - clean stderr output.
		openssl_dotted = openssl_stderr.split('+')[0]
		openssl_text = openssl_stderr.split('+')[10]
		if args.loglevel == 'info'.upper():
			print(f'[*] OpenSSL Command: {openssl_cmd}')
			print(f'[*] OpenSSL Output:\n{openssl_dotted}{openssl_text}')

	# Interface - set MAC address.
	print('-'*100)
	try:
		interface_01 = interface.Interface(ifname_01) # DEV - may want to move this above.
		interface_01.set_active(activate=False)
		if not bssid:
			print(f'[*] Set interface MAC argument "-m" not found')
			set_mac_results = interface_01.set_mac(f'-s')
		else:
			set_mac_results = interface_01.set_mac(f'--mac={bssid}')
		interface_01.set_active(activate=True)
	except Exception as e:
		logging.error(f'{e}')
		sys.exit(1)
	else:
		set_mac_cmd = ' '.join(set_mac_results[0])
		set_mac_stdout = set_mac_results[1]
		set_mac_stderr = set_mac_results[2]
		if args.loglevel == 'info'.upper():
			print(f'[*] Macchanger Command: {set_mac_cmd}')
			print(f'[*] Macchanger Output:\n{set_mac_stdout}')
			print(f'{set_mac_stderr}')

	# Interface - set Regulatory Domain.
	print('-'*100)
	try:
		# interface_01 = interface.Interface(ifname_01) # DEV - may want to move this above.
		interface_01.set_active(activate=False)
		set_reg_results = interface_01.set_reg(f'{regulatory_domain}')
		interface_01.set_active(activate=True)
	except Exception as e:
		logging.error(f'{e}')
		sys.exit(1)
	else:
		set_reg_cmd = ' '.join(set_reg_results[0])
		set_reg_stdout = set_reg_results[1]
		if args.loglevel == 'info'.upper():
			print(f'[*] Regulatory Domain Command: {set_reg_cmd}')
			print(f'[*] Regulatory Domain Output:\n{set_reg_stdout}')

	# Interface - set TX Power.
	print('-'*100)
	try:
		# interface_01 = interface.Interface(ifname_01) # DEV - may want to move this above.
		interface_01.set_active(activate=False)
		set_txpower_results = interface_01.set_txpower(f'{tx_power}')
		interface_01.set_active(activate=True)
	except Exception as e:
		logging.error(f'{e}')
		sys.exit(1)
	else:
		set_txpower_cmd = ' '.join(set_txpower_results[0])
		set_txpower_stdout = set_txpower_results[1]
		if args.loglevel == 'info'.upper():
			print(f'[*] TX Power Command: {set_txpower_cmd}')
			print(f'[*] TX Power Output:\n{set_txpower_stdout}')

	# Hostapd-wpe - Create instance and launch.
	print('-'*100)
	try:
		eviltwin = hostapd.Hostapd
		asyncio.run(eviltwin(hostapd_conf_fp, args_runtime).run())
		# input('Press enter to exit:')
	except KeyboardInterrupt:
		print(f'\nQuit: detected [CTRL-C] ')
		sys.exit(0)


if __name__ == '__main__':
	for _ in range(args_rounds):
		print(f'[*] Round: {_ + 1} / {args_rounds}')
		main()
		if args_rounds > 1 and args_rounds is not _ + 1:
			print(f'[*] Sleeping: {args_sleep}')
			time.sleep(args_sleep)
		
