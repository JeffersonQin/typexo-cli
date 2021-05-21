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
	if element in get_global('content_meta_string'): return f"{repr(content)}"
	if element in get_global('content_meta_int'): return int(content)
	return content


def get_content_essential(content: dict):
	res = {}
	for element in get_global('content_check_essential'):
		if element in content.keys():
			res[element] = get_warped_content_value(element, content[element])
	return res


def post_data(item: str, target: str, add: list, update: list, delete: list):
	push_subroutine(sys._getframe().f_code.co_name)

	clog(f'posting data to {target} server...')
	try:
		url = f"{get_global('conf')[target]['url']}/push_{item}"
		data = {
			'token': get_global('conf')[target]['token'],
			'add': add,
			'update': update,
			'delete': delete
		}
		res = requests.post(url=url, data=json.dumps(data)).json()
		if res['code'] == -1:
			cerr(f'POST ERROR: {res["message"]}')
			raise Exception('POST REQUEST FAILED')
		if res['code'] == 1:
			csuccess(f'POST {item} TO {target} SUCCESS, message: {res["message"]}')
			return res['add'], res['update'], res['delete']
		raise Exception(f'UNKNOWN STATUS CODE {res["code"]}, message: {res["message"]}')
	except Exception as e:
		cerr(f'error: {repr(e)}')
		traceback.print_exc()
		cexit('POSTING DATA FAILED')
	finally:
		pop_subroutine()


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
		# record titles of delete_files
		deleted_titles = {}
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
				deleted_files.append(int(r_content['cid']))
				deleted_titles[str(r_content['cid'])] = r_content['title']
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
				# add attribute: modified date
				if 'modified' not in modify['data'].keys():
					modify['data']['modified'] = int(time.time())
				modified_files.append(modify)
		# logging
		clog('---------- DIFF: CONTENT SECTION START ----------')
		clog('NEW (Untracked): ')
		for new_file in new_files:
			csuccess(f'[U] hash: {new_file["hash"]}, dir: {new_file["dir"]}')
		clog('MODIFIED (Unstaged): ')
		for modified_file in modified_files:
			csuccess(f'[M] cid: {modified_file["cid"]}, dir: {modified_file["dir"]}')
		clog('DELETED: ')
		for deleted_cid in deleted_files:
			cerr(f'[D] cid: {deleted_cid}, title: {deleted_titles[str(deleted_cid)]}')
		clog('---------- DIFF: CONTENT SECTION END ----------')
		return new_files, modified_files, deleted_files, deleted_titles
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
