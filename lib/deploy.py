import os
import sys
import yaml
import json
import traceback
import time
import hashlib
from globalvar import *
from echo import *
from utils import *
from read import *


def get_warped_content_value(element: str, content: str):
	if content == None: return 'NULL'
	if content == '': return 'NULL'
	if element in get_global('content_meta_string'): return f"'{content}'"
	if element in get_global('content_meta_int'): return int(content)
	return content


def get_content_essential(content: dict):
	res = {}
	for element in get_global('content_check_essential'):
		if element in content.keys():
			res[element] = get_warped_content_value(element, content[element])
	return res


def diff_contents(local: list, remote: list):
	push_subroutine(sys._getframe().f_code.co_name)

	clog(f'differing contents...')
	try:
		# cids-generated.json
		local_cids = read_local_cids()
		# post data: [{<dir>, <dir_hash>, <data>}]
		new_files = []
		# post data: [{<dir>, <cid>, <data>}]
		modified_files = []
		# post data: [cid]
		deleted_files = []
		# record cids
		local_with_cids = {}
		for l_content in local:
			# record cid if exist
			if l_content['dir'] in local_cids.keys():
				local_with_cids[str(local_cids[l_content['dir']])] = l_content
			# add to `new` files if not exist
			else:
				new_files.append({
					'dir': l_content['dir'],
					'hash': hashlib.md5(l_content['dir'].encode()).hexdigest(), 
					'data': get_content_essential(l_content)
				})
		# compare with remote
		for r_content in remote:
			# check whether deleted
			if str(r_content['cid']) not in local_with_cids.keys():
				deleted_files.append(str(r_content['cid']))
				continue
			# start comparing, check whether identical
			l_content = local_with_cids[str(r_content['cid'])]
			identical = True
			modify = {
				'dir': l_content['dir'],
				'cid': int(r_content['cid']),
				'data': {}
			}
			# compare every attribute
			for element in get_global('content_check_essential'):
				# convert line ending
				if str(l_content[element]).replace('\r\n', '\n') != str(r_content[element]).replace('\r\n', '\n'):
					identical = False
					modify['data'][element] = get_warped_content_value(element, l_content[element])
			if not identical:
				if 'modified' not in modify['data'].keys():
					modify['data']['modified'] = int(time.time())
				modified_files.append(modify)
		return new_files, modified_files, deleted_files
	except Exception as e:
		cerr(f'error: {repr(e)}')
		traceback.print_exc()
		cexit('DIFFERING CONTENTS FAILED')
	finally:
		pop_subroutine()


def diff_metas(local: list, remote: list):
	return


def diff_relationships(local: list, remote: list):
	return


def diff_fields(local: list, remote: list):
	return
