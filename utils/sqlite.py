#!/usr/bin/env python3

import sqlite3
from utils import arguments

# Argparse - init and parse.
args = arguments.parser.parse_args()
if args.database:
	database_file = args.database
else:
	database_file = './evillyn.db'

# Database init.
conn = sqlite3.connect(database_file)
# Cursor init.
c = conn.cursor()
# Cursor results in datatype dict, default is tuple.
c.row_factory = sqlite3.Row


# Identity Table
def create_table_identity():
	''' Create table identity '''

	try:
		with conn:
			c.execute("""CREATE TABLE Identity(
				identity text,
				macaddress text
				)""")
	except sqlite3.OperationalError:
		pass

# Identity Table
def insert_identity(id, macaddress):
	''' Insert result [(id, MACAddress)] '''
	
	with conn:
		c.execute("INSERT INTO identity VALUES (:id, :macaddress)",
		 {'id': id, 'macaddress': macaddress})

# Identity Table
def get_identity():
	''' Get all unique identities.'''

	c.execute("SELECT * FROM identity")
	return  {f"{dic['identity']} {dic['macaddress']}" for dic in c.fetchall()}

# Identity Table
def isrecord_identity():
	''' Check if the table has any existing records. '''

	try:
		c.execute("SELECT EXISTS(SELECT 1 FROM identity WHERE 'identity'=? LIMIT 1)", ('identity',))
		record = c.fetchone()
		if record[0] == 1:
			# Debug print
			# print(f'[*] Identity Table: Found existing record(s).')
			return True
		else:
			# Debug print
			# print(f'[*] Identity Table exists, but no records found.')
			return False
	except sqlite3.OperationalError as e:
		# print(f'{e}')
		return False


# NetNTLM Table
def create_table_netntlm():
	''' Create table NetNTLM '''

	try:
		with conn:
			c.execute("""CREATE TABLE NetNTLM(
				username text,
				hashcat text,
				jtr text
				)""")
	except sqlite3.OperationalError:
		pass

# NetNTLM Table
def insert_netntlm(username, hashcat, jtr):
	''' Insert result [(Useranem, Hashcat, JTR)] '''
	
	with conn:
		c.execute("INSERT INTO netntlm VALUES (:username, :hashcat, :jtr)",
		 {'username': username, 'hashcat': hashcat, 'jtr': jtr})

# NetNTLM Table
def get_hashcat_hash():
	''' Get all Hashcat NetNTLM Hashes.'''

	c.execute("SELECT * FROM netntlm")
	return  {f"{dic['hashcat']}" for dic in c.fetchall()}

# NetNTLM Table
def get_hashcat_by_username(username):
	''' Get Hashcat-Hash column by filtering the username value.'''

	c.execute("SELECT hashcat FROM netntlm WHERE username=:username", {'username': username})
	return  {f"{dic['hashcat']}" for dic in c.fetchall()}

# NetTNTLM Table
def get_jtr_by_username(username):
	''' Get JTR-Hash column by filtering the username value.'''

	c.execute("SELECT jtr FROM netntlm WHERE username=:username", {'username': username})
	return  {f"{dic['jtr']}" for dic in c.fetchall()}

# NetTNTLM Table
def isrecord_netntlm():
	''' Check if the table has any existing records. '''

	try:
		c.execute("SELECT EXISTS(SELECT 1 FROM NetNTLM WHERE 'username'=? LIMIT 1)", ('username',))
		record = c.fetchone()
		if record[0] == 1:
			# Debug print
			# print(f'[*] NetNTLM Table: Found existing record(s).')
			return True
		else:
			# Debug print
			# print(f'[*] NetNTLM table exists, but no records found.')
			return False
	except sqlite3.OperationalError as e:
		# print(f'{e}')
		return False


# General
def get_tables():
	''' Get a list of tables in the database.'''

	tables = []
	res = c.execute("SELECT name FROM sqlite_master WHERE type='table';")
	for name in res.fetchall():
		tables.append(name[0])
		
	return tables

# General
def get_table_row_count(tablename):
	''' Get row count from table.'''

	row_count = []
	res = c.execute(f"SELECT count(*) FROM {tablename}")
	for rows in res.fetchall():
		row_count.append(rows[0])
		
	return row_count

# General
def drop_table(tablename):
	''' Drop table. '''
	
	try:
		with conn:
			c.execute(f"DROP TABLE {tablename}")
	except sqlite3.OperationalError as e:
		pass
