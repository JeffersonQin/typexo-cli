import os
import sys
import yaml
import json
import traceback
import time

import globalvar
import utils
import echo


def typecho2md(data: dict):	
	echo.push_subroutine(sys._getframe().f_code.co_name)
	
	try:
		# format time
		data['year'] = time.localtime(int(data['created'])).tm_year
		data['mon'] = time.localtime(int(data['created'])).tm_mon
		data['created'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(data['created']))
		data['modified'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(data['modified']))
		# add dir
		data['dir'] = f'/{data["type"]}s/{data["year"]}/{data["mon"]}/{utils.slugify(data["title"])}.md'
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
		if data['text'].startswith('<!--markdown-->'):
			data['text'] = data['text'][15:]
		return data
	except Exception as e:
		echo.cerr(f'error: {repr(e)}')
		traceback.print_exc()
		echo.cexit(f'TYPECHO DATA CONVERTING FAILED')
	finally:
		echo.pop_subroutine()


def md2typecho(data: dict):
	echo.push_subroutine(sys._getframe().f_code.co_name)
	
	try:
		# convert to timestamp
		data['created'] = int(time.mktime(time.strptime(data['created'], '%Y-%m-%d %H:%M:%S')))
		data['modified'] = int(time.mktime(time.strptime(data['modified'], '%Y-%m-%d %H:%M:%S')))
		data['year'] = time.localtime(data['created']).tm_year
		data['mon'] = time.localtime(data['created']).tm_mon
		# add dir
		data['dir'] = f'/{data["type"]}s/{data["year"]}/{data["mon"]}/{utils.slugify(data["title"])}.md'
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
		if not data['text'].startswith('<!--markdown-->'):
			data['text'] = f"<!--markdown-->{data['text']}"
		return data
	except Exception as e:
		echo.cerr(f'error: {repr(e)}')
		traceback.print_exc()
		echo.cexit(f'MARKDOWN DATA CONVERTING FAILED')
	finally:
		echo.pop_subroutine()


def get_warped_content_value(element: str, content: str):
	if content == None: return 'NULL'
	if content == '': return 'NULL'
	if element in globalvar.get_global('content_meta_string'): return f"{repr(content)}"
	if element in globalvar.get_global('content_meta_int'): return int(content)
	return content


def get_content_essential(content: dict):
	res = {}
	for element in globalvar.get_global('content_check_essential'):
		if element in content.keys():
			res[element] = get_warped_content_value(element, content[element])
	return res


def dump_contents(content_data: list, meta_data: list, pair_data: dict, field_data: dict):
	echo.push_subroutine(sys._getframe().f_code.co_name)
	
	echo.clog('dumping contents...')
	
	ctype = None
	create_year = None
	create_month = None
	file_name = None

	dir_cid_pair = {}

	try:
		for item in content_data:
			cid = item['cid']
			
			item = typecho2md(item)
			# obtain content	
			content = str(item['text'])
			# format the metas for yml
			ctype = f"{item['type']}s"
			# obtain essential meta data
			create_year = str(item['year'])
			create_month = str(item['mon'])
			file_name = utils.slugify(item['title'])
			# dealing with directories
			base_dir = os.path.join(globalvar.get_global('wp_dir'), ctype)
			year_dir = os.path.join(base_dir, create_year)
			mon_dir = os.path.join(year_dir, create_month)
			# create if not exist
			if not os.path.exists(year_dir): os.mkdir(year_dir)
			if not os.path.exists(mon_dir): os.mkdir(mon_dir)
			# exclude some unneeded meta data
			for exclude in globalvar.get_global('content_meta_exclude'):
				if exclude in item.keys():
					item.pop(exclude)
			# create key if not exist
			if str(cid) not in pair_data.keys():
				pair_data[str(cid)] = {'mids': []}
			# match cid with path
			dir_cid_pair[f'/{ctype}/{create_year}/{create_month}/{file_name}.md'] = cid
			# get tags & categories
			tags = []
			categories = []
			for mid in pair_data[str(cid)]['mids']:
				mid_meta = meta_data[str(mid)]
				if mid_meta['type'] == 'tag': tags.append(mid_meta['name'])
				if mid_meta['type'] == 'category': categories.append(mid_meta['name'])
			tags.sort()
			categories.sort()
			item['tags'] = tags
			item['categories'] = categories
			# dump fields
			if str(cid) in field_data.keys():
				item['fields'] = field_data[str(cid)]
			
			meta = yaml.dump(item, allow_unicode=True)
			# start dumping
			with open(os.path.join(mon_dir, f'{file_name}.md'), 'w+', encoding='utf8') as f:
				f.write('---\n')
				f.write(meta)
				f.write('---\n')
				f.write(content)
			echo.csuccess(f'success: /{ctype}/{create_year}/{create_month}/{file_name}.md')
		echo.clog('start dumping cids...')
		json.dump(dir_cid_pair, open(os.path.join(globalvar.get_global('wp_dir'), 'cids-generated.json'), 'w+', encoding='utf8'),
								sort_keys=True,
								indent='\t',
								ensure_ascii=False,
								separators=(',', ': '))
		echo.csuccess(f'success: dumping finished.')
		echo.csuccess(f'success: pulling finished.')
	except Exception as e:
		echo.cerr(f'error: /{ctype}/{create_year}/{create_month}/{file_name}.md')
		echo.cerr(f'error: {repr(e)}')
		traceback.print_exc()
		echo.cexit('CONTENT DUMPING FAILED')
	finally:
		echo.pop_subroutine()


def format_metas_for_contents(meta_data: list):
	echo.push_subroutine(sys._getframe().f_code.co_name)
	
	echo.clog('formatting metadata for contents...')
	res = {}
	try:
		for meta in meta_data:
			# get & pop mid attribute
			mid = meta['mid']
			meta.pop('mid')
			# exclude some unneeded meta data
			for exclude in globalvar.get_global('meta_meta_exclude'):
				if exclude in meta.keys():
					meta.pop(exclude)
			# reorganize data structure
			res[str(mid)] = meta
			echo.csuccess(f'read {meta["type"]}: {meta["name"]}')
		echo.csuccess('success: metadata formatted for CONTENTS.')
		return res
	except Exception as e:
		echo.cerr(f'error: {repr(e)}')
		traceback.print_exc()
		echo.cexit('META FORMATTING FOR CONTENTS FAILED')
	finally:
		echo.pop_subroutine()


def format_metas(meta_data: list):
	echo.push_subroutine(sys._getframe().f_code.co_name)
	
	echo.clog('formatting metadata...')
	res = {'tag': {}, 'category': {}}
	try:
		for meta in meta_data:
			name = meta['name']
			meta_type = meta['type']
			meta.pop('name')
			for exclude in globalvar.get_global('meta_meta_exclude'):
				if exclude in meta.keys():
					meta.pop(exclude)
			res[meta_type][name] = meta
		echo.csuccess('success: metadata formatted.')
		return res
	except Exception as e:
		echo.cerr(f'error: {repr(e)}')
		traceback.print_exc()
		echo.cexit('META FORMATTING FAILED')
	finally:
		echo.pop_subroutine()


def dump_metas(meta_data: dict):
	echo.push_subroutine(sys._getframe().f_code.co_name)
	
	echo.clog('dumping metadata...')
	try:
		# dump metadata to file
		json.dump(meta_data, open(os.path.join(globalvar.get_global('wp_dir'), 'metas.json'), 'w+', 
						encoding='utf8'),
						sort_keys=True,
						indent='\t',
						ensure_ascii=False,
						separators=(',', ': '))
		echo.csuccess('success: metadata dumped.')
	except Exception as e:
		echo.cerr(f'error: {repr(e)}')
		traceback.print_exc()
		echo.cexit('META DUMPING FAILED')
	finally:
		echo.pop_subroutine()


def format_relationships(pair_data: list):
	echo.push_subroutine(sys._getframe().f_code.co_name)
	
	try:
		res = {}
		for pair in pair_data:
			cid = pair['cid']
			if str(cid) not in res.keys():
				res[str(cid)] = {'mids': []}
			res[str(cid)]['mids'].append(pair['mid'])
		return res
	except Exception as e:
		echo.cerr(f'error: {repr(e)}')
		traceback.print_exc()
		echo.cexit('RELATIONSHIP FORMATTING FAILED')
	finally:
		echo.pop_subroutine()


def format_fields(field_data: list):
	echo.push_subroutine(sys._getframe().f_code.co_name)
	
	try:
		res = {}
		for field in field_data:
			cid = field['cid']
			if str(cid) not in res.keys():
				res[str(cid)] = {}
			res[str(cid)][field['name']] = field[f'{field["type"]}_value']
		return res
	except Exception as e:
		echo.cerr(f'error: {repr(e)}')
		traceback.print_exc()
		echo.cexit('FIELD FORMATTING FAILED')
	finally:
		echo.pop_subroutine()

