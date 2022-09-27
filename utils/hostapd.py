#!/usr/bin/env python3

import logging
import subprocess
# DEV
from asyncio import CancelledError
from asyncio.exceptions import TimeoutError
import asyncio
import time

class Hostapd():
	''' Hostapd-wpe class wrapper '''

	filepath_cmd = f'which hostapd-wpe'
	version_cmd = f'hostapd-wpe -v'

	
	def __init__(self, conf_arg, runtime):
		''' '''
		self.cmd = f'hostapd-wpe'
		self.conf_arg = conf_arg
		self.runtime = runtime


	# def __del__(self):
	# 	print(f'Instance deleted: {self}')


	@classmethod
	def get_filepath(cls):
		''' Return filepath:str '''

		cmdlst = cls.filepath_cmd.split(' ')
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
	def get_version(cls):
		''' Return version:str '''

		cmdlst = cls.version_cmd.split(' ')
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

			output = proc.stderr.split('\n')
		return output[0]


	async def read_stream(self, proc_stream, proc_returncode):
		''' '''

		while True:
			output = await proc_stream.readline()
			output_decoded = output.decode('UTF-8').rstrip()
			if output_decoded:
				print(f'{output_decoded}')
			elif proc_returncode is not None:
				print(f'{proc_returncode}')
				break
			else:
				pass

	
	async def run(self):
		''' '''

		cmdlst = self.cmd.split(' ')
		cmdlst.append(self.conf_arg)

		proc = await asyncio.create_subprocess_exec(
			# Permit lst with '*'.
			* cmdlst, 
			stdout=asyncio.subprocess.PIPE, 
			stderr=asyncio.subprocess.PIPE
			)
		# Print
		print(f'[*] Hostapd Runtime: {self.runtime}')
		print(f'[*] Hostapd Command: {" ".join(cmdlst)}')
		print(f'[*] Hostapd PID: {proc.pid}')
		print(f'[*] Hostapd Output: ')
		
		# Timer - start
		start = time.perf_counter()

		# Asyncio - create and name tasks.
		task_stdout = asyncio.create_task(self.read_stream(proc.stdout, proc.returncode), name='STREAM STDOUT')
		task_stderr = asyncio.create_task(self.read_stream(proc.stderr, proc.returncode), name='STREAM STDERR')

		# Asyncio - concurrently run stdout/stderr streams. Used asyncio.wait() for 'timeout'.
		try:
			done, pending = await asyncio.wait([task_stdout, task_stderr],
				# return_when=asyncio.FIRST_EXCEPTION
				timeout=self.runtime
				)
			# Terminate proc, executes after 'asyncio.wait.timeout' timeout.
			proc.terminate()
			print(f'\n[*] Runtime Expired: {self.runtime} seconds') 
			print(f'[*] Terminated PID: {proc.pid}')
			
			# Asyncio - cancel pending Tasks.
			for task in pending:
				if task.cancel():
					print(f'[*] Asyncio - Task Canceled: "{task.get_name()}"')
				# Required to cancel tasks successfullly, else. runtime error will occur.
				time.sleep(.25)

			# Asyncio - print completed Tasks.
			for task in done:
				print(f'[*] Asyncio - Task Completed/Done: "{task.get_name()}"')
				print(f'[*] Asyncio - Task Result: "{task.result()}"')
				# Required to cancel tasks successfullly, else. runtime error will occur.
				time.sleep(.25)
		except Exception as e:
			print(f'Exception: {e}')
		
		# Timer - finish
		end = time.perf_counter()
		print(f'[*] Completed in: {round(end-start,0)} second(s).\n')
		return None


	# def run(self):
	#   ''' Launch Hostapd-wpe via subprocess wrapper '''
		
	#   cmdlst = self.cmd.split(' ')
	#   cmdlst.append(self.conf_arg)
	#   try:
	#       # Popen was used in place of subprocess.run() to allow live stream.
	#       proc = subprocess.Popen(cmdlst,
	#           shell=False,
	#           stdout=subprocess.PIPE,
	#           stderr=subprocess.PIPE
	#           )
	#   except Exception as e:
	#       # Set check=True for the exception to catch.
	#       logging.exception(e)
	#       raise e
	#   else:
	#       # Poll proc.stdout to show stdout live stream.
	#       cmd = ' '.join(cmdlst)
	#       print(f'[*] Hostapd Command: {cmd}')
	#       print(f'[*] Hostapd Output:')

	#       # DEV
	#       import time

	#       stoptime = 32
	#       cooldown = 10
	#       current_time = time.time()
	#       count = 0

	#       runtime = current_time + stoptime

	#       print(f'[*] Current Time: {round(time.time())}')
	#       while True:
	#           # Hostapd - timer loop.
	#           time.sleep(.25)
	#           count +=1

	#           # if time.time() >= runtime + 1:
	#           #   print(f'[*] Runtime Expired: {round(time.time())}')
	#           #   proc.terminate()
					
	#           #   print(f'[*] Sleeping for: {cooldown}')
	#           #   time.sleep(cooldown)
					
	#           #   print(f'[*] Waking up!')
	#           #   self.run()
	#           #   # break
				
	#           # Hostapd - main loop.
	#           output = proc.stdout.readline()
	#           output_decoded = output.decode('UTF-8')
	#           if proc.poll() is not None:
	#               print('break')
	#               break
	#           if output:
	#               print(f'{output_decoded.strip()}')

	#           print(count)
	#           proc.wait(timeout=30)
	#       rc = proc.poll()
		
	#   return None
