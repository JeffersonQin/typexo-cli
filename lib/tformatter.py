import os
import sys
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
			if data[key] == '' and key != 'text': data[key] = None
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


def get_warped_mysql_value(element: str, content: str):
	if content == None: return 'NULL'
	if content == '': return 'NULL'
	if element in globalvar.get_global('typecho_type_string'): return f"{repr(content)}"
	if element in globalvar.get_global('typecho_type_int'): return int(content)
	return content


def get_content_essential(content: dict):
	res = {}
	for element in globalvar.get_global('content_check_essential'):
		if element in content.keys():
			res[element] = get_warped_mysql_value(element, content[element])
	return res


def get_meta_essential(meta: dict):
	res = {}
	for element in globalvar.get_global('meta_check_essential'):
		if element in meta.keys():
			res[element] = get_warped_mysql_value(element, meta[element])
	return res


def get_field_repr(field: dict):
	field['name'] = repr(field['name'])
	if 'type' in field.keys():
		if field['type'] == 'str':
			field['value'] = repr(field['value'])
		field['type'] = repr(field['type'])
	return field


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

