import os
import sys
import yaml
import json
import traceback

import globalvar
import echo
import tformatter


def read_markdown_file(dir: str, silent=True):
	'''
	read everything in markdown file, including dir
	'''
	echo.push_subroutine(sys._getframe().f_code.co_name)

	if not silent:
		echo.clog(f'reading: {dir}')
	try:
		with open(dir, 'r') as f:
			# front matter
			if f.readline() != '---\n':
				raise Exception('broken format: front matter detection error.')
			config = ''
			new_line = f.readline()
			while new_line != '---\n':
				config = f'{config}{new_line}'
				new_line = f.readline()
			res = yaml.load(config, Loader=yaml.FullLoader)
			# content
			res['text'] = f.read()
			res = tformatter.md2typecho(res)
			return res
	except Exception as e:
		echo.cerr(f'error occurred: {dir}')
		echo.cerr(f'error: {repr(e)}')
		traceback.print_exc()
		echo.cexit(f'MARKDOWN READING FAILED')
	finally:
		echo.pop_subroutine()


def filter_markdown():
	'''
	filter out markdown files in the workspace
	'''
	echo.push_subroutine(sys._getframe().f_code.co_name)

	echo.clog('filtering markdown files...')
	try:
		res = []
		for dir in globalvar.get_global('wp_essential_structure')['folders']:
			type_dir = os.path.join(globalvar.get_global('wp_dir'), dir)
			if not os.path.exists(type_dir): continue
			for r, d, f in os.walk(type_dir):
				for file in f:
					if file.endswith('.md'):
						res.append(os.path.join(r, file))
		return res
	except Exception as e:
		echo.cerr(f'error: {repr(e)}')
		traceback.print_exc()
		echo.cexit(f'MAKRDOWN FILTERING FAILED')
	finally:
		echo.pop_subroutine()


def read_local_contents():
	'''
	filter_markdown + read_markdown_file
	'''
	echo.push_subroutine(sys._getframe().f_code.co_name)

	echo.clog('reading local files...')
	try:
		res = []
		files = filter_markdown()
		for file in files:
			res.append(read_markdown_file(file))
		return res
	except Exception as e:
		echo.cerr(f'error: {repr(e)}')
		traceback.print_exc()
		echo.cexit(f'LOCAL FILES READING FAILED')
	finally:
		echo.pop_subroutine()


def read_metas_in_posts():
	'''
	read metas in posts, return {'tag': [<tag>], 'category': [<category>]}
	'''
	echo.push_subroutine(sys._getframe().f_code.co_name)

	echo.clog('reading metas in posts...')
	try:
		res = {'tag': [], 'category': []}
		files = filter_markdown()
		for file in files:
			md_file = read_markdown_file(file)
			if 'tags' in md_file.keys():
				res['tag'] = list(set(res['tag'] + md_file['tags']))
			if 'categories' in md_file.keys():
				res['category'] = list(set(res['category'] + md_file['categories']))
		return res
	except Exception as e:
		echo.cerr(f'error: {repr(e)}')
		traceback.print_exc()
		echo.cexit(f'METAS IN POSTS READING FAILED')
	finally:
		echo.pop_subroutine()


def read_local_metas():
	'''
	read metas in `metas.json`
	'''
	echo.push_subroutine(sys._getframe().f_code.co_name)

	echo.clog('reading local metas...')
	try:
		local_metas = {}
		with open(os.path.join(globalvar.get_global('wp_dir'), 'metas.json'), 'r', encoding='utf-8') as f:
			local_metas = json.load(f)
		return local_metas
	except Exception as e:
		echo.cerr(f'error: {repr(e)}')
		traceback.print_exc()
		echo.cexit(f'LOCAL METAS READING FAILED')
	finally:
		echo.pop_subroutine()


def read_local_cids():
	'''
	read cids in `cids-generated.json`
	'''
	echo.push_subroutine(sys._getframe().f_code.co_name)

	echo.clog('reading local cids-generated.json...')
	try:
		local_cids = {}
		with open(os.path.join(globalvar.get_global('wp_dir'), 'cids-generated.json'), 'r', encoding='utf-8') as f:
			local_cids = json.load(f)
		return local_cids
	except Exception as e:
		echo.cerr(f'error: {repr(e)}')
		traceback.print_exc()
		echo.cexit(f'LOCAL CIDS READING FAILED')
	finally:
		echo.pop_subroutine()


def read_local_dirs():
	'''
	return {<cid>: <dir>}
	'''
	echo.push_subroutine(sys._getframe().f_code.co_name)

	echo.clog('reading local dirs...')
	try:
		res = {}
		local_cids = read_local_cids()
		for key in local_cids.keys():
			res[str(local_cids[key])] = key
		return res
	except Exception as e:
		echo.cerr(f'error: {repr(e)}')
		traceback.print_exc()
		echo.cexit(f'LOCAL DIRS READING FAILED')
	finally:
		echo.pop_subroutine()


def read_local_meta_name():
	'''
	return {<mid>: {name: <name>, type: <type>}}
	'''
	echo.push_subroutine(sys._getframe().f_code.co_name)

	echo.clog('reading local meta names...')
	try:
		res = {}
		metas = read_local_metas()
		for key in metas['tag'].keys():
			res[str(metas['tag'][key]['mid'])] = {
				'name': key,
				'type': 'tag'
			}
		for key in metas['category'].keys():
			res[str(metas['category'][key]['mid'])] = {
				'name': key,
				'type': 'category'
			}
		return res
	except Exception as e:
		echo.cerr(f'error: {repr(e)}')
		traceback.print_exc()
		echo.cexit(f'LOCAL DIRS READING FAILED')
	finally:
		echo.pop_subroutine()


def read_pairs_in_posts():
	'''
	read pairs of metas with posts
	'''
	echo.push_subroutine(sys._getframe().f_code.co_name)

	echo.clog('reading pairs in posts...')
	try:
		res = []
		cids = read_local_cids() # {'dir': 'cid'}
		metas = read_local_metas() # {'category': {<name>: {<data>}}, 'tag': {<name>: {<data>}}}
		files = filter_markdown()
		for file in files:
			md_file = read_markdown_file(file)
			index_dir = md_file['dir']
			cid = cids[index_dir]
			if 'tags' in md_file.keys():
				for tag in md_file['tags']:
					res.append((cid, metas['tag'][tag]['mid']))
			if 'categories' in md_file.keys():
				for category in md_file['categories']:
					res.append((cid, metas['category'][category]['mid']))
		return res
	except Exception as e:
		echo.cerr(f'error: {repr(e)}')
		traceback.print_exc()
		echo.cexit(f'LOCAL PAIRS READING FAILED')
	finally:
		echo.pop_subroutine()
