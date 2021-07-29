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
				if element in l_content.keys():
					# convert line ending
					if str(l_content[element]).replace('\r\n', '\n') != str(r_content[element]).replace('\r\n', '\n'):
						identical = False
						modify['data'][element] = tformatter.get_warped_mysql_value(element, l_content[element])
			if not identical:
				# add attribute: modified date
				# if 'modified' not in modify['data'].keys():
				# 	modify['data']['modified'] = int(time.time())
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
					deleted_names[str(remote_meta_data[remote_meta_name]['mid'])] = {
						'name': remote_meta_name, 
						'type': remote_meta_data[remote_meta_name]['type']
					}
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
		new_ret = new_tags + new_categories
		modified_ret = modified_tags + modified_categories
		deleted_ret = deleted_tags + deleted_categories
		deleted_name_ret = {**deleted_tags_name, **deleted_categories_name}
		# logging
		echo.clog('---------- DIFF: META SECTION START ----------')
		echo.clog(f'NEW (Untracked): {len(new_ret)} in total')
		for new_meta in new_ret:
			echo.csuccess(f'[U] [{new_meta["data"]["type"]}] hash: {new_meta["hash"]}, name: {new_meta["data"]["name"]}')
		echo.clog(f'MODIFIED (Unstaged): {len(modified_ret)} in total')
		for modified_meta in modified_ret:
			echo.csuccess(f'[M] [{modified_meta["data"]["type"]}] mid: {modified_meta["mid"]}, name: {modified_meta["data"]["name"]}')
		echo.clog(f'DELETED: {len(deleted_ret)} in total')
		for deleted_mid in deleted_ret:
			echo.cerr(f'[D] [{deleted_name_ret[str(deleted_mid)]["type"]}] mid: {deleted_mid}, name: {deleted_name_ret[str(deleted_mid)]["name"]}')
		echo.clog('---------- DIFF: META SECTION END ----------')
		return new_ret, modified_ret, deleted_ret, deleted_name_ret
	except Exception as e:
		echo.cerr(f'error: {repr(e)}')
		traceback.print_exc()
		echo.cexit('DIFFERING METAS FAILED')
	finally:
		echo.pop_subroutine()


def diff_relationships(local: list, remote: list):
	echo.push_subroutine(sys._getframe().f_code.co_name)

	echo.clog('differing relationships...')
	try:
		cid_dir = read.read_local_dirs()
		mid_data = read.read_local_meta_name()
		deleted_pairs = []
		for item in remote:
			if item not in local:
				deleted_pairs.append(item)
			else:
				local.remove(item)
		# log
		echo.clog('---------- DIFF: PAIR SECTION START ----------')
		echo.clog(f'NEW (Untracked): {len(local)} in total')
		for new_pair in local:
			cid = new_pair['cid']
			mid = new_pair['mid']
			c_dir = 'NOT_IN_DB'
			m_meta = 'NOT_IN_DB'
			if str(cid) in cid_dir.keys():
				c_dir = cid_dir[str(cid)]
			if str(mid) in mid_data.keys():
				m_meta = f'[{mid_data[str(mid)]["type"]}] {mid_data[str(mid)]["name"]}'
			echo.cerr(f'[U] [{cid}, {mid}] {c_dir} => {m_meta}')
		echo.clog(f'DELETED: {len(deleted_pairs)} in total')
		for deleted_pair in deleted_pairs:
			cid = deleted_pair['cid']
			mid = deleted_pair['mid']
			c_dir = 'NOT_IN_DB'
			m_meta = 'NOT_IN_DB'
			if str(cid) in cid_dir.keys():
				c_dir = cid_dir[str(cid)]
			if str(mid) in mid_data.keys():
				m_meta = f'[{mid_data[str(mid)]["type"]}] {mid_data[str(mid)]["name"]}'
			echo.cerr(f'[D] [{cid}, {mid}] {c_dir} => {m_meta}')
		echo.clog('---------- DIFF: PAIR SECTION END ----------')
		return local, deleted_pairs # new, deleted
	except Exception as e:
		echo.cerr(f'error: {repr(e)}')
		traceback.print_exc()
		echo.cexit('DIFFERING RELATIONSHIPS FAILED')
	finally:
		echo.pop_subroutine()


def diff_fields(local: list, remote: list):
	echo.push_subroutine(sys._getframe().f_code.co_name)

	echo.clog('differing fields...')
	try:
		cid_dir = read.read_local_dirs()
		new_fields = []
		deleted_fields = []
		for item in remote:
			e_item = {
				'cid': item['cid'],
				'name': item['name'],
				'type': item['type'],
				'value': item[f'{item["type"]}_value']
			}
			if e_item not in local:
				deleted_fields.append(tformatter.get_field_repr({
					'cid': item['cid'],
					'name': item['name']
				}))
			else:
				local.remove(e_item)
		for item in local:
			new_fields.append(tformatter.get_field_repr(item))
		# log
		echo.clog('---------- DIFF: FIELDS SECTION START ----------')
		echo.clog(f'NEW (Untracked): {len(new_fields)} in total')
		for new_field in new_fields:
			cid = new_field['cid']
			c_dir = 'NOT_IN_DB'
			if str(cid) in cid_dir.keys():
				c_dir = cid_dir[str(cid)]
			echo.cerr(f'[U] [{cid}] {c_dir} => {new_field["name"]}')
		echo.clog(f'DELETED: {len(deleted_fields)} in total')
		for deleted_field in deleted_fields:
			cid = deleted_field['cid']
			c_dir = 'NOT_IN_DB'
			if str(cid) in cid_dir.keys():
				c_dir = cid_dir[str(cid)]
			echo.cerr(f'[D] [{cid}] {c_dir} => {deleted_field["name"]}')
		echo.clog('---------- DIFF: FIELD SECTION END ----------')
		return new_fields, deleted_fields # new, deleted
	except Exception as e:
		echo.cerr(f'error: {repr(e)}')
		traceback.print_exc()
		echo.cexit('DIFFERING RELATIONSHIPS FAILED')
	finally:
		echo.pop_subroutine()


def calculate_count(local_pairs: list):
	echo.push_subroutine(sys._getframe().f_code.co_name)

	echo.clog('recalculating counts...')
	try:
		mid_data = read.read_local_meta_name()
		cnt = {}
		for pair in local_pairs:
			if str(pair['mid']) not in cnt.keys():
				cnt[str(pair['mid'])] = 1
			else:
				cnt[str(pair['mid'])] += 1
		res = []
		for mid in cnt.keys():
			res.append({
				'mid': int(mid),
				'data': {
					'count': cnt[mid]
				}
			})
			echo.clog(f'[meta count] [{mid_data[mid]["type"]}] {mid_data[mid]["name"]} = {cnt[mid]}')
		return res
	except Exception as e:
		echo.cerr(f'error: {repr(e)}')
		traceback.print_exc()
		echo.cexit('DIFFERING RELATIONSHIPS FAILED')
	finally:
		echo.pop_subroutine()
