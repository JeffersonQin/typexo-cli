import sys
import requests
import unicodedata
import re
import click
import traceback

import echo
import globalvar


def _download_file(url, dir, headers):
	echo.clog(f'start downloading: {url} => {dir}')
	ret = 0
	try:
		# start and block request
		r = requests.get(url, stream=True, headers=headers, verify=globalvar.get_global('conf')['verify'])
		# obtain content length
		length = int(r.headers['content-length'])
		echo.clog(f'file size: {size_description(length)}')
		# start writing
		f = open(dir, 'wb+')
		# show in progressbar
		with click.progressbar(label="Downloading from remote: ", length=length) as bar:
			for chunk in r.iter_content(chunk_size = 512):
				if chunk:
					f.write(chunk)
					bar.update(len(chunk))
		echo.csuccess('Download Complete.')
		f.close()
	except Exception as err:
		echo.cerr(f'Error: {repr(err)}')
		traceback.print_exc()
		ret = 1
	finally:
		return ret


def download_file(url, dir, headers={'Proxy-Connection':'keep-alive'}, trial=5):
	echo.push_subroutine(sys._getframe().f_code.co_name)
	fail_count = 0
	while True:
		ret = _download_file(url, dir, headers)
		if ret == 0:
			echo.pop_subroutine()
			return
		if fail_count < trial:
			fail_count += 1
			echo.cerr(f'Download failed, Trial {fail_count}/{trial}')
		else:
			echo.cexit('Download failed. Exceeded trial limit.')


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
