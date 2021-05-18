import os
import sys
import yaml
import json
import traceback
import time
from globalvar import *
from echo import *
from utils import *


def typecho2md(data: dict):	
	try:
		# format time
		data['year'] = time.localtime(data['created']).tm_year
		data['mon'] = time.localtime(data['created']).tm_mon
		data['created'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(data['created']))
		data['modified'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(data['modified']))
		# format booleans
		if 'allowComment' in data.keys():
			if data['allowComment'] == '1':
				data['allowComment'] = True
			else: data['allowComment'] = False
		if 'allowPing' in data.keys():
			if data['allowPing'] == '1':
				data['allowPing'] = True
			else: data['allowPing'] = False
		if 'allowFeed' in data.keys():
			if data['allowFeed'] == '1':
				data['allowFeed'] = True
			else: data['allowFeed'] = False
		# format nulls
		for key in data.keys():
			if data[key] == None: data[key] = ''
		# format content
		if item['text'].startswith('<!--markdown-->'):
			item['text'] = item['text'][15:]
		return data
	except Exception as e:
		set_global('cmd_name', sys._getframe().f_code.co_name)
		cerr(f'error: {repr(e)}')
		traceback.print_exc()
		cexit(f'TYPECHO DATA CONVERTING FAILED')


def md2typecho(data: dict):
	try:
		# convert to timestamp
		data['created'] = int(time.mktime(time.strptime(data['created'], '%Y-%m-%d %H:%M:%S')))
		data['modified'] = int(time.mktime(time.strptime(data['modified'], '%Y-%m-%d %H:%M:%S')))
		data['year'] = time.localtime(data['created']).tm_year
		data['mon'] = time.localtime(data['created']).tm_mon
		# reformat boolean
		if 'allowComment' in data.keys():
			if data['allowComment']: data['allowComment'] = '1'
			else: data['allowComment'] = '0'
		if 'allowPing' in data.keys():
			if data['allowPing']: data['allowPing'] = '1'
			else: data['allowPing'] = '0'
		if 'allowFeed' in data.keys():
			if data['allowFeed']: data['allowFeed'] = '1'
			else: data['allowFeed'] = '0'
		# format nulls
		for key in data.keys():
			if data[key] == '': data[key] = None
		# format content
		if not item['text'].startswith('<!--markdown-->'):
			item['text'] = f"<!--markdown-->{item['text']}"
		return data
	except Exception as e:
		set_global('cmd_name', sys._getframe().f_code.co_name)
		cerr(f'error: {repr(e)}')
		traceback.print_exc()
		cexit(f'MARKDOWN DATA CONVERTING FAILED')
