#!/usr/bin/env python

import logging
import subprocess


class Interface():
	''' Network Interface Manager Class. '''

	macchanger_filepath_cmd = f'which macchanger'
	macchanger_version_cmd = f'macchanger -V'

	
	def __init__(self, ifname):
		''' '''
		self.ifname = ifname
		self.macchanger_cmd = f"macchanger"
		self.setreg_cmd = f"iw reg set"
		self.iwconfig_tx_cmd = f"iwconfig {self.ifname} txpower"


	@classmethod
	def macchanger_filepath(cls):
		''' Return filepath:str '''

		cmdlst = cls.macchanger_filepath_cmd.split(' ')
		try:
			proc = subprocess.run(cmdlst,
				shell=False,
				check=True,
				capture_output=True,
				text=True 
				)
		except Exception as e:
			# Set check=True for the exception to catch.
			logging.exception(e)
			raise e
		else:
			# Debug print only.
			logging.debug(f'STDOUT:\n{proc.stdout}')
			logging.debug(f'STDERR:\n{proc.stderr}')
		
		return proc.stdout.strip()
	

	@classmethod
	def macchanger_version(cls):
		''' Return version:str '''

		cmdlst = cls.macchanger_version_cmd.split(' ')
		try:
			proc = subprocess.run(cmdlst,
				shell=False,
				check=False,
				capture_output=True,
				text=True
				)
		except Exception as e:
			# Set check=True for the exception to catch.
			logging.exception(e)
			raise e
		else:
			# Debug print only.
			logging.debug(f'STDOUT:\n{proc.stdout}')
			logging.debug(f'STDERR:\n{proc.stderr}')

			output = proc.stdout.split('\n')
		return output[0]

	
	def set_mac(self, *args):
		''' Launch MacChanger via subprocess wrapper '''

		cmdlst = self.macchanger_cmd.split()
		cmdlst.append(''.join(args))		
		cmdlst.append(self.ifname)
		try:
			proc = subprocess.run(cmdlst,
				shell=False,
				check=False,
				capture_output=True,
				text=True
				)
		except Exception as e:
			# Set check=True for the exception to catch.
			logging.exception(e)
		else:
			# Debug print only.
			logging.debug(f'STDOUT:\n{proc.stdout}')
			logging.debug(f'STDERR:\n{proc.stderr}')
			return cmdlst, proc.stdout, proc.stderr


	def set_reg(self, *args):
		''' Launch Reg set via subprocess wrapper '''

		cmdlst = self.setreg_cmd.split()
		cmdlst.append(''.join(args))
		try:
			proc = subprocess.run(cmdlst,
				shell=False,
				check=True,
				capture_output=True,
				text=True
				)
		except Exception as e:
			# Set check=True for the exception to catch.
			logging.exception(e)
			raise e
		else:
			# Debug print only.
			logging.debug(f'STDOUT:\n{proc.stdout}')
			logging.debug(f'STDERR:\n{proc.stderr}')
			return cmdlst, proc.stdout, proc.stderr

	
	def set_txpower(self, *args):
		''' Launch Txpower via subprocess wrapper '''

		cmdlst = self.iwconfig_tx_cmd.split()
		cmdlst.append(''.join(args))
		try:
			proc = subprocess.run(cmdlst,
				shell=False,
				check=False,
				capture_output=True,
				text=True
				)
		except Exception as e:
			# Set check=True for the exception to catch.
			logging.exception(e)
			raise e
		else:
			# Debug print only.
			logging.debug(f'STDOUT:\n{proc.stdout}')
			logging.debug(f'STDERR:\n{proc.stderr}')
			return cmdlst, proc.stdout, proc.stderr


	def set_active(self, activate=True):
		'''  Launch ifconfig via subprocess wrapper  '''
		
		if activate:
			cmdlst = f'ifconfig {self.ifname} up'.split()
		else:
			cmdlst = f'ifconfig {self.ifname} down'.split()	
		try:
			proc = subprocess.run(cmdlst,
				shell=False,
				check=True,
				capture_output=True,
				text=True
				)
		except Exception as e:
			# Set check=True for the exception to catch.
			logging.exception(e)
			raise e
		else:
			# Debug print only.
			logging.debug(f'STDOUT:\n{proc.stdout}')
			logging.debug(f'STDERR:\n{proc.stderr}')
			return proc.stderr