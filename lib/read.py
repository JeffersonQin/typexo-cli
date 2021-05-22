import os
import sys
import yaml
import json
import traceback
import time
from globalvar import *
from echo import *
from utils import *
from converter import *


def read_markdown_file(dir: str):
	push_subroutine(sys._getframe().f_code.co_name)

	clog(f'reading: {dir}')
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
			res = md2typecho(res)
			return res
	except Exception as e:
		cerr(f'error occurred: {dir}')
		cerr(f'error: {repr(e)}')
		traceback.print_exc()
		cexit(f'MARKDOWN READING FAILED')
	finally:
		pop_subroutine()


def filter_markdown():
	push_subroutine(sys._getframe().f_code.co_name)

	clog('filtering markdown files...')
	try:
		res = []
		for dir in get_global('wp_essential_structure')['folders']:
			type_dir = os.path.join(get_global('wp_dir'), dir)
			if not os.path.exists(type_dir): continue
			for r, d, f in os.walk(type_dir):
				for file in f:
					if file.endswith('.md'):
						res.append(os.path.join(r, file))
		return res
	except Exception as e:
		cerr(f'error: {repr(e)}')
		traceback.print_exc()
		cexit(f'MAKRDOWN FILTERING FAILED')
	finally:
		pop_subroutine()


def read_local_contents():
	push_subroutine(sys._getframe().f_code.co_name)

	clog('reading local files...')
	try:
		res = []
		files = filter_markdown()
		for file in files:
			res.append(read_markdown_file(file))
		return res
	except Exception as e:
		cerr(f'error: {repr(e)}')
		traceback.print_exc()
		cexit(f'LOCAL FILES READING FAILED')
	finally:
		pop_subroutine()


def read_metas_in_posts():
	push_subroutine(sys._getframe().f_code.co_name)

	clog('reading metas in posts...')
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
		cerr(f'error: {repr(e)}')
		traceback.print_exc()
		cexit(f'METAS IN POSTS READING FAILED')
	finally:
		pop_subroutine()


def read_local_metas():
	push_subroutine(sys._getframe().f_code.co_name)

	clog('reading local metas...')
	try:
		local_metas = {}
		with open(os.path.join(get_global('wp_dir'), 'metas.json'), 'r', encoding='utf-8') as f:
			local_metas = json.load(f)
		return local_metas
	except Exception as e:
		cerr(f'error: {repr(e)}')
		traceback.print_exc()
		cexit(f'LOCAL METAS READING FAILED')
	finally:
		pop_subroutine()


def read_local_cids():
	push_subroutine(sys._getframe().f_code.co_name)

	clog('reading local cids-generated.json...')
	try:
		local_cids = {}
		with open(os.path.join(get_global('wp_dir'), 'cids-generated.json'), 'r', encoding='utf-8') as f:
			local_cids = json.load(f)
		return local_cids
	except Exception as e:
		cerr(f'error: {repr(e)}')
		traceback.print_exc()
		cexit(f'LOCAL CIDS READING FAILED')
	finally:
		pop_subroutine()
