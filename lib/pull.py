import os
import sys
import yaml
import json
import traceback
import time
from globalvar import *
from echo import *
from utils import *


def check_dirs():
	set_global('cmd_name', sys._getframe().f_code.co_name)

	clog('checking essential structure...')
	try:
		for dir in get_global('wp_essential_structure')['folders']:
			if not os.path.exists(os.path.join(get_global('wp_dir'), dir)):
				os.mkdir(os.path.join(get_global('wp_dir'), dir))
		csuccess('checking finished.')
	except Exception as e:
		cerr(f'error: {repr(e)}')
		traceback.print_exc()
		cexit('INVALID FILE STRUCTURE')
		


def fetch_resource(source: str, resource: str):
	set_global('cmd_name', sys._getframe().f_code.co_name)

	clog(f'fetching {resource}')

	cache_dir = os.path.join(get_global('root_dir'), 'cache/')
	file_dir = os.path.join(cache_dir, f'{resource}.json')

	if not os.path.exists(cache_dir): os.mkdir(cache_dir)

	download_file(f"{get_global('conf')[source]['url']}/fetch_{resource}?token={get_global('conf')[source]['token']}", file_dir)
	
	try:
		with open(file_dir, 'r', encoding='utf8') as f:
			res = json.load(f)
			if res['code'] == 1: 
				csuccess(f'connectivity test passed, message: {res["message"]}')
				return res['data']
			else: 
				cerr(f'fetch contents failed, message: {res["message"]}')
				raise Exception(f'fetch contents failed, message: {res["message"]}')
	except Exception as e:
		cerr(f'error: {repr(e)}')
		traceback.print_exc()
		cexit(f'{source}/{resource} FETCHING FAILED')


def dump_contents(content_data: list, meta_data: list, pair_data: dict):
	set_global('cmd_name', sys._getframe().f_code.co_name)
	
	clog('dumping contents...')
	
	create_year = None
	create_month = None
	file_name = None

	dir_cid_pair = {}

	try:
		for item in content_data:
			cid = item['cid']
			# obtain content			
			content = str(item['text'])
			# format content
			if content.startswith('<!--markdown-->'):
				content = content[15:]
			# obtain essential meta data
			type = f"{item['type']}s"
			create_local_time = time.localtime(item['created'])
			create_year = str(create_local_time.tm_year)
			create_month = str(create_local_time.tm_mon)
			file_name = slugify(item['title'])
			# dealing with directories
			base_dir = os.path.join(get_global('wp_dir'), type)
			year_dir = os.path.join(base_dir, create_year)
			mon_dir = os.path.join(year_dir, create_month)
			# create if not exist
			if not os.path.exists(year_dir): os.mkdir(year_dir)
			if not os.path.exists(mon_dir): os.mkdir(mon_dir)
			# exclude some unneeded meta data
			for exclude in get_global('content_meta_exclude'):
				if exclude in item.keys():
					item.pop(exclude)
			# format the metas for yml
			# format time
			item['created'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(item['created']))
			item['modified'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(item['modified']))
			# format booleans
			if 'allowComment' in item.keys():
				if item['allowComment'] == '1':
					item['allowComment'] = True
				else: item['allowComment'] = False
			if 'allowPing' in item.keys():
				if item['allowPing'] == '1':
					item['allowPing'] = True
				else: item['allowPing'] = False
			if 'allowFeed' in item.keys():
				if item['allowFeed'] == '1':
					item['allowFeed'] = True
				else: item['allowFeed'] = False
			# format nulls
			for key in item.keys():
				if item[key] == None: item[key] = ''
			# create key if not exist
			if str(cid) not in pair_data.keys():
				pair_data[str(cid)] = {'mids': []}
			# match cid with path
			dir_cid_pair[f'/{type}/{create_year}/{create_month}/{file_name}.md'] = cid
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
			
			meta = yaml.dump(item, allow_unicode=True)
			# start dumping
			with open(os.path.join(mon_dir, f'{file_name}.md'), 'w+', encoding='utf8') as f:
				f.write('---\n')
				f.write(meta)
				f.write('---\n')
				f.write(content)
			csuccess(f'success: /{type}/{create_year}/{create_month}/{file_name}.md')
		clog('start dumping cids...')
		json.dump(dir_cid_pair, open(os.path.join(get_global('wp_dir'), 'cids-generated.json'), 'w+', encoding='utf8'),
								sort_keys=True,
								indent='\t',
								ensure_ascii=False,
								separators=(',', ': '))
		csuccess(f'success: dumping finished.')
		csuccess(f'success: pulling finished.')
	except Exception as e:
		cerr(f'error: /{type}/{create_year}/{create_month}/{file_name}.md')
		cerr(f'error: {repr(e)}')
		traceback.print_exc()
		cexit('CONTENT DUMPING FAILED')


def format_metas(meta_data: list):
	set_global('cmd_name', sys._getframe().f_code.co_name)
	
	clog('formating metadata...')
	res = {}
	try:
		for meta in meta_data:
			# get & pop mid attribute
			mid = meta['mid']
			meta.pop('mid')
			# exclude some unneeded meta data
			for exclude in get_global('meta_meta_exclude'):
				if exclude in meta.keys():
					meta.pop(exclude)
			# reorganize data structure
			res[str(mid)] = meta
			csuccess(f'read {meta["type"]}: {meta["name"]}')
		csuccess('success: metadata formatted.')
		return res
	except Exception as e:
		cerr(f'error: {repr(e)}')
		traceback.print_exc()
		cexit('META FORMATTING FAILED')


def dump_metas(meta_data: list):
	set_global('cmd_name', sys._getframe().f_code.co_name)
	
	clog('dumping metadata...')
	res = {'tag': {}, 'category': {}}
	try:
		for meta in meta_data:
			name = meta['name']
			meta_type = meta['type']
			meta.pop('name')
			for exclude in get_global('meta_meta_exclude'):
				if exclude in meta.keys():
					meta.pop(exclude)
			res[meta_type][name] = meta
		# dump metadata to file
		json.dump(res, open(os.path.join(get_global('wp_dir'), 'metas.json'), 'w+', 
						encoding='utf8'),
						sort_keys=True,
						indent='\t',
						ensure_ascii=False,
						separators=(',', ': '))
		csuccess('success: metadata dumped.')
	except Exception as e:
		cerr(f'error: {repr(e)}')
		traceback.print_exc()
		cexit('META DUMPING FAILED')
		

def format_relationships(pair_data: list):
	set_global('cmd_name', sys._getframe().f_code.co_name)
	
	try:
		res = {}
		for pair in pair_data:
			cid = pair['cid']
			if str(cid) not in res.keys():
				res[str(cid)] = {'mids': []}
			res[str(cid)]['mids'].append(pair['mid'])
		return res
	except Exception as e:
		cerr(f'error: {repr(e)}')
		traceback.print_exc()
		cexit('RELATIONSHIP FORMATTING FAILED')

