import sys
import hashlib
import time
import traceback

import tformatter
import globalvar
import echo
import read
import utils


def diff_contents(local: list, local_cids: dict, remote: list):
	echo.push_subroutine(sys._getframe().f_code.co_name)

	echo.clog(f'differing contents...')
	try:
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
					modify['data'][element] = tformatter.get_warped_mysql_value(element, l_content[element])
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


def diff_metas(local_metas: list, post_metas: list, remote_metas: list):
	echo.push_subroutine(sys._getframe().f_code.co_name)

	echo.clog('differing metas...')
	try:
		
		def classify_diff_for_meta(metatype: str):
			# post data: [{<type_name_hash>, <data>}]
			new_metas = []
			# post data: [{<mid>, <data>}]
			modified_metas = []
			# post data: [mid]
			deleted_metas = []
			# record names of deleted_metas: {'mid': <name>}
			deleted_names = {}
			# local data
			local_meta_data = local_metas[metatype]
			# all names of local
			local_meta_names = set(post_metas[metatype] + list(local_meta_data.keys()))
			# remote data
			remote_meta_data = remote_metas[metatype]
			remote_meta_names = remote_meta_data.keys()

			local_meta_processed = set([])
			for remote_meta_name in remote_meta_names:
				if remote_meta_name not in local_meta_names:
					# deleted metas
					deleted_metas.append(int(remote_meta_data[remote_meta_name]['mid']))
					deleted_names[str(remote_meta_data[remote_meta_name]['mid'])] = remote_meta_name
				else:
					if not remote_meta_data[remote_meta_name] == local_meta_data[remote_meta_name]:
						# define modified data
						modified_data = local_meta_data[remote_meta_name]
						# define post data
						modify = {
							'mid': int(modified_data['mid']),
							'data': {}
						}
						# configure modified data
						modified_data['name'] = remote_meta_name
						# configure post data
						modify['data'] = tformatter.get_meta_essential(modified_data)
						modified_metas.append(modify)
					# pop from local
					if remote_meta_name in local_meta_data.keys():
						local_meta_data.pop(remote_meta_name)
					local_meta_processed.add(remote_meta_name)
			
			for remain_local_meta_name in (local_meta_names - local_meta_processed):
				new_ = {
					'hash': hashlib.md5(f'{metatype}{remain_local_meta_name}'.encode()).hexdigest(), 
					'data': {}
				}
				new_data = {'name': remain_local_meta_name}
				# data specified
				if remain_local_meta_name in local_meta_data.keys():
					new_data = {**new_data, **local_meta_data[remain_local_meta_name]}
				# if data specified in `metas.json`
				else:
					new_data['slug'] = utils.slugify(remain_local_meta_name)
					new_data['type'] = metatype
					new_data['description'] = None
					new_data['parent'] = 0
				# reformat the data
				new_data = tformatter.get_meta_essential(new_data)
				# add to post data
				new_['data'] = new_data
				new_metas.append(new_)

			return new_metas, modified_metas, deleted_metas, deleted_names
		
		new_tags, modified_tags, deleted_tags, deleted_tags_name = classify_diff_for_meta('tag')
		new_categories, modified_categories, deleted_categories, deleted_categories_name = classify_diff_for_meta('category')
		# logging
		
		return (new_tags + new_categories), (modified_tags + modified_categories), (deleted_tags + deleted_categories), {**deleted_tags_name, **deleted_categories_name}
	except Exception as e:
		echo.cerr(f'error: {repr(e)}')
		traceback.print_exc()
		echo.cexit('DIFFERING METAS FAILED')
	finally:
		echo.pop_subroutine()


def diff_relationships(local: list, remote: list):
	return


def diff_fields(local: list, remote: list):
	return
