import sys
import requests
import unicodedata
import re
import click
import os
import traceback
from globalvar import *
from echo import *

def download_file(url, dir):
	set_global('cmd_name', sys._getframe().f_code.co_name)

	clog(f'start downloading: {url} => {dir}')
	try:
		# define request headers
		headers = {'Proxy-Connection':'keep-alive'}
		# start and block request
		r = requests.get(url, stream=True, headers=headers)
		# obtain content length
		length = int(r.headers['content-length'])
		clog(f'file size: {size_description(length)}')
		# start writing
		f = open(dir, 'wb+')
		# show in progressbar
		with click.progressbar(label="Downloading from remote: ", length=length) as bar:
			for chunk in r.iter_content(chunk_size = 512):
				if chunk:
					f.write(chunk)
					bar.update(len(chunk))
		csuccess('Download Complete.')
		f.close()
	except Exception as err:
		cerr(f'error: {repr(err)}')
		traceback.print_exc()
		cexit('DOWNLOAD FAILED')


def size_description(size):
	'''
	Taken and modified from https://blog.csdn.net/wskzgz/article/details/99293181
	'''
	def strofsize(integer, remainder, level):
		if integer >= 1024:
			remainder = integer % 1024
			integer //= 1024
			level += 1
			return strofsize(integer, remainder, level)
		else:
			return integer, remainder, level

	units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
	integer, remainder, level = strofsize(size, 0, 0)
	if level + 1 > len(units):
		level = -1
	return ( '{}.{:>03d} {}'.format(integer, remainder, units[level]) )


def slugify(value, allow_unicode=True):
	'''
	Taken and modified from django/utils/text.py
	Copyright (c) Django Software Foundation and individual contributors.
	All rights reserved.
	Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
	dashes to single dashes. Remove characters that aren't alphanumerics,
	underscores, or hyphens. Convert to lowercase. Also strip leading and
	trailing whitespace, dashes, and underscores.
	'''
	value = str(value)
	if allow_unicode:
		value = unicodedata.normalize('NFKC', value)
	else:
		value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
	value = re.sub(r'[^\w\s-]', '', value)
	return re.sub(r'[-\s]+', '-', value).strip('-_')
