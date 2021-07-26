import os
import sys
import traceback
import json
import yaml


import globalvar
import utils
import echo
import tformatter


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
			
			item = tformatter.typecho2md(item)
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
			
			meta = yaml.dump(item, allow_unicode=True, default_flow_style=None)
			
			content = str(content).replace('\r\n', '\n')
			meta = str(meta).replace('\r\n', '\n')
			
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
	except Exception as e:
		echo.cerr(f'error: /{ctype}/{create_year}/{create_month}/{file_name}.md')
		echo.cerr(f'error: {repr(e)}')
		traceback.print_exc()
		echo.cexit('CONTENT DUMPING FAILED')
	finally:
		echo.pop_subroutine()


def dump_contents_raw(content_data: dict):
	echo.push_subroutine(sys._getframe().f_code.co_name)
	
	echo.clog('dumping contents (raw)...')
	try:
		for dir in content_data.keys():
			meta = content_data[dir]
			content = meta['text']
			meta.pop('text')
			meta = yaml.dump(meta, allow_unicode=True, default_flow_style=None)

			content = str(content).replace('\r\n', '\n')
			meta = str(meta).replace('\r\n', '\n')
			
			with open(dir, 'w', encoding='utf8') as f:
				f.write('---\n')
				f.write(meta)
				f.write('---\n')
				f.write(content)
			echo.csuccess(f'success: {dir}')
		echo.csuccess(f'success: dumping (raw) finished.')
	except Exception as e:
		echo.cerr(f'error: {repr(e)}')
		traceback.print_exc()
		echo.cexit('CONTENT DUMPING FAILED')
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

