import sys
import hashlib
import time
import traceback

import tformatter
import globalvar
import echo
import read


def diff_contents(local: list, remote: list):
	echo.push_subroutine(sys._getframe().f_code.co_name)

	echo.clog(f'differing contents...')
	try:
		# cids-generated.json
		local_cids = read.read_local_cids()
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
					'data': tformatter.get_content_essential(l_content)
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
			for element in globalvar.get_global('content_check_essential'):
				# convert line ending
				if str(l_content[element]).replace('\r\n', '\n') != str(r_content[element]).replace('\r\n', '\n'):
					identical = False
					modify['data'][element] = tformatter.get_warped_content_value(element, l_content[element])
			if not identical:
				# add attribute: modified date
				if 'modified' not in modify['data'].keys():
					modify['data']['modified'] = int(time.time())
				modified_files.append(modify)
		# logging
		echo.clog('---------- DIFF: CONTENT SECTION START ----------')
		echo.clog(f'NEW (Untracked): {len(new_files)} in total')
		for new_file in new_files:
			echo.csuccess(f'[U] hash: {new_file["hash"]}, dir: {new_file["dir"]}')
		echo.clog(f'MODIFIED (Unstaged): {len(modified_files)} in total')
		for modified_file in modified_files:
			echo.csuccess(f'[M] cid: {modified_file["cid"]}, dir: {modified_file["dir"]}')
		echo.clog(f'DELETED: {len(deleted_files)} in total')
		for deleted_cid in deleted_files:
			echo.cerr(f'[D] cid: {deleted_cid}, title: {deleted_titles[str(deleted_cid)]}')
		echo.clog('---------- DIFF: CONTENT SECTION END ----------')
		return new_files, modified_files, deleted_files, deleted_titles
	except Exception as e:
		echo.cerr(f'error: {repr(e)}')
		traceback.print_exc()
		echo.cexit('DIFFERING CONTENTS FAILED')
	finally:
		echo.pop_subroutine()


def diff_metas(local: list, remote: list):
	return


def diff_relationships(local: list, remote: list):
	return


def diff_fields(local: list, remote: list):
	return
