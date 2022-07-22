import yaml
import os
import click
import requests
import json
import sys
import shutil
import time
import traceback
import copy
import subprocess


# initialize paths & caches
root_dir = os.path.split(os.path.abspath(__file__))[0]
lib_dir = os.path.join(root_dir, './lib/')
config_dir = os.path.join(root_dir, 'config.yml')
wp_dir = os.path.join(root_dir, '../workplace/')
site_dir = os.path.join(root_dir, './site/')
readme_dir = os.path.join(wp_dir, 'README.md')

# import lib
sys.path.insert(0, lib_dir)

import tdiff
import echo
import globalvar
import messenger
import read
import structure
import tdump
import tformatter
import utils
from warp_git import *

# initialize subroutine
echo.init_subroutine()

# initialize global var
globalvar.global_init()

# configure structure
wp_essential_structure = {
	'folders': [
		'posts', 'pages', 'post_drafts', 'page_drafts'
	],
	'files': [
		'metas.json', 'relationships-generated.json'
	]
}

# configure items exclude in metadata
content_meta_exclude = ['cid', 'order', 'commentsNum', 'text', 'views', 'year', 'mon', 'dir']
meta_meta_exclude = ['count', 'order']

content_check_essential = ['title', 'slug', 'created', 'modified', 'text', 'authorId', 'template', 'type', 'status', 'password', 'allowComment', 'allowPing', 'allowFeed']
meta_check_essential = ['name', 'slug', 'type', 'description', 'parent']

typecho_type_string = ['title', 'slug', 'text', 'template', 'type', 'status', 'password', 'allowComment', 'allowPing', 'allowFeed', 'description', 'mid', 'cid', 'name']
typecho_type_int = ['created', 'modified', 'authorId', 'parent']

# globalize other variable
globalvar.set_global('conf', {})
globalvar.set_global('cmd_name', 'main')
globalvar.set_global('wp_dir', wp_dir)
globalvar.set_global('site_dir', site_dir)
globalvar.set_global('root_dir', root_dir)
globalvar.set_global('lib_dir', lib_dir)
globalvar.set_global('config_dir', config_dir)
globalvar.set_global('wp_essential_structure', wp_essential_structure)
globalvar.set_global('content_meta_exclude', content_meta_exclude)
globalvar.set_global('meta_meta_exclude', meta_meta_exclude)
globalvar.set_global('content_check_essential', content_check_essential)
globalvar.set_global('meta_check_essential', meta_check_essential)
globalvar.set_global('typecho_type_string', typecho_type_string)
globalvar.set_global('typecho_type_int', typecho_type_int)

def read_conf():
	# Read configuration
	with open(config_dir, 'r', encoding='utf8') as f:
		contents = f.read()
		globalvar.set_global('conf', yaml.load(contents, Loader=yaml.FullLoader))

#### Command Line Interface (CLI) Start ####

@click.group()
def cli():
	pass


@cli.command()
def init():
	'''
	✅ Initialize a git version control workplace from nothing
	'''
	echo.push_subroutine(sys._getframe().f_code.co_name)

	echo.clog('initializing workplace...')
	if not os.path.exists(wp_dir): os.mkdir(wp_dir)
	if os.listdir(wp_dir) != []:
		echo.cerr('workplace folder is not empty. Try "rm" command first.')
		return
	try:
		git_init_subprocess()
		echo.csuccess('git initialization success.')
		with open(readme_dir, 'w+', encoding='utf8') as f:
			f.write('This file is created automatically by [typexo-cli](https://github.com/JeffersonQin/typexo-cli)\n')
		echo.csuccess('write file test success.')
		add_res = git_repo().index.add(items=['README.md'])
		echo.clog(f'add README.md: \n{add_res}')
		commit_res = git_repo().index.commit('Initial auto commit by typexo.')
		echo.clog(f'commit (initial auto): \n{commit_res}')
		echo.clog(f'branch info: \n{git_branch_native()}')
	except Exception as e:
		echo.cerr(f'error: {repr(e)}')
		traceback.print_exc()
		echo.cexit('INIT FAILED')
	finally:
		echo.pop_subroutine()


@cli.command()
def rm():
	'''
	✅ Delete the whole workplace
	'''
	echo.push_subroutine(sys._getframe().f_code.co_name)

	if not os.path.exists(wp_dir):
		echo.cerr('workplace folder does not exist.')
		return

	echo.clog('triggered to delete')
	click.echo('IMPORTANT: this command will delete everything in the workplace folder. Are you sure to continue? [y/n] ', nl=False)
	user_in = input()
	if (user_in != 'y' and user_in != 'Y'):
		echo.cexit('REJECTED')
	try:
		shutil.rmtree(wp_dir)
		echo.csuccess('delete success.')
	except Exception as e:
		echo.cerr(f'error: {repr(e)}')
		traceback.print_exc()
		echo.cexit('REMOVE WP FAILED')
	finally:
		echo.pop_subroutine()


@cli.command()
def clone():
	'''
	✅ Clone the workplace from remote repo
	'''
	echo.push_subroutine(sys._getframe().f_code.co_name)

	echo.clog('cloning workplace from remote...')
	if not os.path.exists(wp_dir): os.mkdir(wp_dir)
	if os.listdir(wp_dir) != []:
		echo.cerr('workplace folder is not empty. Try "rm" command first.')
		return
	try:
		git_clone_from_remote()
		structure.check_dirs()
	except Exception as e:
		echo.cerr(f'error: {repr(e)}')
		traceback.print_exc()
		echo.cexit('CLONE FAILED')
	finally:
		echo.pop_subroutine()


@cli.command()
@click.argument('source', type=click.Choice(['prod', 'test']))
def pull(source: str):
	'''
	✅ Pull the workplace from prod / test environment
	'''
	echo.push_subroutine(sys._getframe().f_code.co_name)

	echo.clog(f'pulling from {source} environment...')
	try:
		# safe switch to `source` branch
		git_safe_switch(source)
		# ---------------------------- #
		# fetching data
		meta_data = messenger.fetch_database(source, 'metas')
		# relationships
		pair_data = messenger.fetch_database(source, 'relationships')
		pair_data = tformatter.format_relationships(pair_data)
		# fields
		field_data = messenger.fetch_database(source, 'fields')
		field_data = tformatter.format_fields(field_data)
		# content
		content_data = messenger.fetch_database(source, 'contents')
		# ---------------------------- #
		# delete all files except `.git`
		for sub_dir in os.listdir(wp_dir):
			if os.path.isdir(os.path.join(wp_dir, sub_dir)) and (sub_dir in wp_essential_structure['folders']): 
				shutil.rmtree(os.path.join(wp_dir, sub_dir))
			if os.path.isfile(os.path.join(wp_dir, sub_dir)) and (sub_dir in wp_essential_structure['files']):
				os.remove(os.path.join(wp_dir, sub_dir))
		# ---------------------------- #
		# check structure
		res = structure.check_dirs()
		# dumping data
		tdump.dump_metas(tformatter.format_metas(copy.deepcopy(meta_data)))
		meta_data = tformatter.format_metas_for_contents(meta_data)
		res = tdump.dump_contents(content_data, meta_data=meta_data, pair_data=pair_data, field_data=field_data)
		# ---------------------------- #
		echo.clog('git status')
		git_status_subprocess()
		echo.clog('git add .')
		git_add_all_subprocess()
		echo.clog('git commit')
		git_commit_subprocess(f'Pull from "{source}": {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}')
		git_safe_merge_to_master(source)
	except Exception as e:
		echo.cerr(f'pulling failed. error: {repr(e)}')
		traceback.print_exc()
		echo.cexit(f'PULL FROM {source} FAILED')
	finally:
		echo.pop_subroutine()


@cli.command()
@click.argument('source', type=click.Choice(['prod', 'test']))
def diff(source: str):
	'''
	🚧 Show difference between local workplace and prod / test
	'''
	echo.push_subroutine(sys._getframe().f_code.co_name)

	echo.clog(f'differing with {source}...')
	try:
		# safe checkout to master
		git_safe_switch('master')
		# content
		# get remote contents
		remote_contents = messenger.fetch_database(source, 'contents')
		# read local contents
		local_contents = read.read_local_contents()
		# read local cids-generated.json
		local_cids = read.read_local_cids()
		# diff contents between local and remote 
		tdiff.diff_contents(local_contents, local_cids, remote_contents)
	except Exception as e:
		echo.cerr(f'differing with {source} failed. error: {repr(e)}')
		traceback.print_exc()
		echo.cexit(f'DIFFERING WITH {source} FAILED')
	finally:
		echo.pop_subroutine()


@cli.command()
@click.pass_context
@click.argument('source', type=click.Choice(['prod', 'test']))
def deploy(ctx, source):
	'''
	✅ Deploy the local workspace to a server
	'''
	echo.push_subroutine(sys._getframe().f_code.co_name)

	echo.clog(f'deploying to server...')
	try:
		# safe checkout to master
		git_safe_switch('master')
		# pull from server (in which will safe checkout to source)
		ctx.invoke(pull, source=source)
		# content
		# get remote contents
		remote_contents = messenger.fetch_database(source, 'contents')
		# read local contents
		local_contents = read.read_local_contents()
		# read local cids-generated.json
		local_cids = read.read_local_cids()
		# diff contents between local and remote 
		new_contents, modified_contents, deleted_contents, deleted_titles = tdiff.diff_contents(local_contents, local_cids, remote_contents)
		# format the new & modified contents
		new_contents_dict = { new_content['hash']: new_content for new_content in new_contents }
		modified_contents_dict = { modified_content['cid']: modified_content for modified_content in modified_contents }
		# post content to server
		res_add, res_update, res_delete = messenger.post_data('contents', source, new_contents, modified_contents, deleted_contents)
		# log post response
		# log add content
		for res in res_add:
			if res['code'] == -1:
				echo.cerr(f'POST RESULT ERROR: {res["message"]}')
				raise Exception(f'POST REQUEST (ADD CONTENT) FAILED FOR hash: {res["hash"]}, dir: {new_contents_dict[res["hash"]]["dir"]}')
			elif res['code'] == 1:
				echo.csuccess(f'POST SUCCESS: ADD CONTENT hash: {res["hash"]}, cid: {res["cid"]}, dir: {new_contents_dict[res["hash"]]["dir"]}')
				local_cids[new_contents_dict[res["hash"]]["dir"]] = res["cid"]
			else: raise Exception(f'UNKNOWN STATUS CODE {res["code"]}, message: {res["message"]}')
		# log update content
		for res in res_update:
			if res['code'] == -1:
				echo.cerr(f'POST RESULT ERROR: {res["message"]}')
				raise Exception(f'POST REQUEST (UPDATE CONTENT) FAILED FOR cid: {res["cid"]}, dir: {modified_contents_dict[res["cid"]]["dir"]}')
			elif res['code'] == 1:
				echo.csuccess(f'POST SUCCESS: UPDATE CONTENT cid: {res["cid"]}, dir: {modified_contents_dict[res["cid"]]["dir"]}')
			else: raise Exception(f'UNKNOWN STATUS CODE {res["code"]}, message: {res["message"]}')
		# log delete content
		for res in res_delete:
			if res['code'] == -1:
				echo.cerr(f'POST RESULT ERROR: {res["message"]}')
				raise Exception(f'POST REQUEST (DELETE CONTENT) FAILED FOR cid: {res["cid"]}, title: {deleted_titles[str(res["cid"])]}')
			elif res['code'] == 1:
				echo.csuccess(f'POST SUCCESS: DELETE CONTENT cid: {res["cid"]}, title: {deleted_titles[str(res["cid"])]}')
			else: raise Exception(f'UNKNOWN STATUS CODE {res["code"]}, message: {res["message"]}')

		# fields
		# read fields in posts
		cid_dir = read.read_local_dirs(local_cids)
		local_fields = read.read_fields_in_posts(local_cids)
		# get remote fields
		remote_fields = messenger.fetch_database(source, 'fields')
		# diff fields between local and remote
		new_fields, deleted_fields = tdiff.diff_fields(local_fields, remote_fields)
		res_add, _, res_delete = messenger.post_data('fields', source, new_fields, [], deleted_fields)
		# log field response
		# log add fields
		for res in res_add:
			cid = res['cid']
			name = res['name']
			res_dir = 'NOT_IN_DB'
			if str(cid) in cid_dir.keys():
				res_dir = cid_dir[str(cid)]
			if res['code'] == -1:
				echo.cerr(f'POST RESULT ERROR: {res["message"]}')
				raise Exception(f'POST REQUEST (ADD FIELD) FAILED FOR [cid]:[{cid}] {res_dir} => {name}')
			elif res['code'] == 1:
				echo.csuccess(f'POST SUCCESS: ADD FIELD, [cid]:[{cid}] {res_dir} => {name}')
			else: raise Exception(f'UNKNOWN STATUS CODE {res["code"]}, message: {res["message"]}')
		# log delete fields
		for res in res_delete:
			cid = res['cid']
			name = res['name']
			res_dir = 'NOT_IN_DB'
			if str(cid) in cid_dir.keys():
				res_dir = cid_dir[str(cid)]
			if res['code'] == -1:
				echo.cerr(f'POST RESULT ERROR: {res["message"]}')
				raise Exception(f'POST REQUEST (DELETE FIELD) FAILED FOR [cid]:[{cid}] {res_dir} => {name}')
			elif res['code'] == 1:
				echo.csuccess(f'POST SUCCESS: DELETE FIELD, [cid]:[{cid}] {res_dir} => {name}')
			else: raise Exception(f'UNKNOWN STATUS CODE {res["code"]}, message: {res["message"]}')
		# meta
		# get mid => type / name
		mid_data = read.read_local_meta_name()
		# read local metas in `metas.json`
		local_metas = read.read_local_metas()
		# read local metas in posts
		post_metas = read.read_metas_in_posts()
		# get remote metas
		remote_metas = tformatter.format_metas(messenger.fetch_database(source, 'metas'))
		# diff metas between local and remote
		new_metas, modified_metas, deleted_metas, deleted_names = tdiff.diff_metas(local_metas, post_metas, remote_metas)
		# format the new & modified metas
		new_metas_dict = { new_meta['hash']: new_meta['data'] for new_meta in new_metas }
		modified_metas_dict = { modified_meta['mid']: modified_meta['data'] for modified_meta in modified_metas }
		# post meta to server
		res_add, res_update, res_delete = messenger.post_data('metas', source, new_metas, modified_metas, deleted_metas)
		local_metas = read.read_local_metas()
		# log meta response
		# log add meta
		for res in res_add:
			if res['code'] == -1:
				echo.cerr(f'POST RESULT ERROR: {res["message"]}')
				raise Exception(f'POST REQUEST (ADD META) FAILED FOR hash: {res["hash"]}, name: {new_metas_dict[res["hash"]]["name"]}')
			elif res['code'] == 1:
				type = new_metas_dict[res["hash"]]["type"][1:-1]
				name = new_metas_dict[res["hash"]]["name"][1:-1]
				mid = res["mid"]
				echo.csuccess(f'POST SUCCESS: ADD META hash: {res["hash"]}, mid: {mid}, name: {name}')
				mid_data[str(mid)] = {
					"name": name,
					"type": type
				}
				local_metas[type][name] = {
					'mid': int(mid),
					'type': type
				}
			else: raise Exception(f'UNKNOWN STATUS CODE {res["code"]}, message: {res["message"]}')
		# log update meta
		for res in res_update:
			if res['code'] == -1:
				echo.cerr(f'POST RESULT ERROR: {res["message"]}')
				raise Exception(f'POST REQUEST (UPDATE META) FAILED FOR mid: {res["mid"]}, name: {modified_metas_dict[str(res["mid"])]["name"]}')
			elif res['code'] == 1:
				echo.csuccess(f'POST SUCCESS: UPDATE META mid: {res["mid"]}, name: {modified_metas_dict[str(res["mid"])]["name"]}')
			else: raise Exception(f'UNKNOWN STATUS CODE {res["code"]}, message: {res["message"]}')
		# log delete meta
		for res in res_delete:
			if res['code'] == -1:
				echo.cerr(f'POST RESULT ERROR: {res["message"]}')
				raise Exception(f'POST REQUEST (DELETE META) FAILED FOR mid: {res["mid"]}, title: {deleted_names[str(res["mid"])]}')
			elif res['code'] == 1:
				echo.csuccess(f'POST SUCCESS: DELETE META mid: {res["mid"]}, title: {deleted_names[str(res["mid"])]}')
			else: raise Exception(f'UNKNOWN STATUS CODE {res["code"]}, message: {res["message"]}')
		
		# relationships
		# read pairs in posts
		local_pairs = read.read_pairs_in_posts(local_cids, local_metas)
		# get remote pairs
		remote_pairs = messenger.fetch_database(source, 'relationships')
		# get cid => dir
		cid_dir = read.read_local_dirs()
		# diff pairs between local and remote
		new_pairs, deleted_pairs = tdiff.diff_relationships(local_pairs, remote_pairs)
		res_add, _, res_delete = messenger.post_data('relationships', source, new_pairs, [], deleted_pairs)
		# log pair response
		# log add pairs
		for res in res_add:
			cid = res["cid"]
			mid = res["mid"]
			res_dir = 'NOT_IN_DB'
			res_meta = 'NOT_IN_DB'
			if str(cid) in cid_dir.keys():
				res_dir = cid_dir[str(cid)]
			if str(mid) in mid_data.keys():
				res_meta = f'[{mid_data[str(mid)]["type"]}] {mid_data[str(mid)]["name"]}'
			if res['code'] == -1:
				echo.cerr(f'POST RESULT ERROR: {res["message"]}')
				raise Exception(f'POST REQUEST (ADD PAIR) FAILED FOR [cid, mid]:[{cid}, {mid}] {res_dir} => {res_meta}')
			elif res['code'] == 1:
				echo.csuccess(f'POST SUCCESS: ADD PAIR, [cid,mid]:[{cid}, {mid}] {res_dir} => {res_meta}')
			else: raise Exception(f'UNKNOWN STATUS CODE {res["code"]}, message: {res["message"]}')
		# log delete pairs
		for res in res_delete:
			cid = res["cid"]
			mid = res["mid"]
			res_dir = 'NOT_IN_DB'
			res_meta = 'NOT_IN_DB'
			if str(cid) in cid_dir.keys():
				res_dir = cid_dir[str(cid)]
			if str(mid) in mid_data.keys():
				res_meta = f'[{mid_data[str(mid)]["type"]}] {mid_data[str(mid)]["name"]}'
			if res['code'] == -1:
				echo.cerr(f'POST RESULT ERROR: {res["message"]}')
				raise Exception(f'POST REQUEST (DELETE PAIR) FAILED FOR [cid, mid]:[{cid}, {mid}] {res_dir} => {res_meta}')
			elif res['code'] == 1:
				echo.csuccess(f'POST SUCCESS: DELETE PAIR, [cid,mid]:[{cid}, {mid}] {res_dir} => {res_meta}')
			else: raise Exception(f'UNKNOWN STATUS CODE {res["code"]}, message: {res["message"]}')
		####
		ctx.invoke(pull, source=source)
		####
		# recount count
		meta_count = tdiff.calculate_count(read.read_pairs_in_posts())
		meta_data = read.read_local_meta_name()
		# post meta to server
		_, res_update, _ = messenger.post_data('metas', source, [], meta_count, [])
		# log update meta
		for res in res_update:
			if res['code'] == -1:
				echo.cerr(f'POST RESULT ERROR: {res["message"]}')
				raise Exception(f'POST REQUEST (UPDATE META) FAILED FOR mid: {res["mid"]}, name: {meta_data[str(res["mid"])]["name"]}')
			elif res['code'] == 1:
				echo.csuccess(f'POST SUCCESS: UPDATE META mid: {res["mid"]}, name: {meta_data[str(res["mid"])]["name"]}')
			else: raise Exception(f'UNKNOWN STATUS CODE {res["code"]}, message: {res["message"]}')
		####
		ctx.invoke(pull, source=source)
		####
	except Exception as e:
		echo.cerr(f'deploying failed. error: {repr(e)}')
		traceback.print_exc()
		echo.cexit('DEPLOYING FAILED')
	finally:
		echo.pop_subroutine()


@cli.command()
def server():
	'''
	🚧 Start a test PHP server locally
	'''
	# subprocess.call(['php', '-S', '127.0.0.1:7777', '-t', globalvar.get_global('site_dir')])


@cli.command()
@click.argument('type', type=click.Choice(['post', 'page']))
@click.option('--draft', is_flag=True, default=False)
@click.argument('title')
def new(type: str, draft: bool, title: str):
	'''
	✅ Create a new content item
	'''
	echo.push_subroutine(sys._getframe().f_code.co_name)

	echo.clog(f'creating new content item: [{type}], draft: [{draft}], title: {title}')
	try:
		# file type
		file_type = type
		if draft: file_type = f'{file_type}_draft'
		# file name
		file_name = utils.slugify(title)
		# time
		time_stamp = int(time.time())
		year = str(time.localtime(time_stamp).tm_year)
		mon = str(time.localtime(time_stamp).tm_mon)
		# dir
		base_dir = os.path.join(globalvar.get_global('wp_dir'), f'{file_type}s')
		year_dir = os.path.join(base_dir, year)
		mon_dir = os.path.join(year_dir, mon)
		save_dir = os.path.join(mon_dir, f'./{file_name}.md')
		# check whether exists
		if not os.path.exists(year_dir): os.mkdir(year_dir)
		if not os.path.exists(mon_dir): os.mkdir(mon_dir)
		# read default meta profile
		meta_data = globalvar.get_global('conf')['defaultProperties']
		meta_data['created'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time_stamp))
		meta_data['modified'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time_stamp))
		meta_data['title'] = title
		meta_data['type'] = file_type
		meta_data['fields'] = globalvar.get_global('conf')['defaultFields']
		if globalvar.get_global('conf')['defaultSlugType']:
			meta_data['slug'] = file_name
		# dump yaml
		meta = yaml.dump(meta_data, allow_unicode=True, default_flow_style=None)
		# dump
		with open(save_dir, 'w+', encoding='utf8') as f:
			f.write('---\n')
			f.write(meta)
			f.write('---\n')
		echo.csuccess(f'new item success: /{file_type}s/{year}/{mon}/{file_name}.md')
	except Exception as e:
		echo.cerr(f'error: {repr(e)}')
		traceback.print_exc()
		echo.cexit('NEW ITEM CREATION FAILED')
	finally:
		echo.pop_subroutine()


@cli.command()
def format():
	'''
	✅ Format files
	'''
	echo.push_subroutine(sys._getframe().f_code.co_name)

	echo.clog('formtting files')
	try:
		tdump.dump_contents_raw(read.read_local_contents_raw(), git_modified())
	except Exception as e:
		echo.cerr(f'error: {repr(e)}')
		traceback.print_exc()
		echo.cexit('FORMATTING FILES FAILED')
	finally:
		echo.pop_subroutine()


@cli.command(name='import')
@click.argument('type', type=click.Choice(['post', 'page']))
@click.option('--draft', is_flag=True, default=False)
@click.argument('file', type=click.Path(exists=True))
def import_command(type: str, draft: bool, file: str):
	'''
	✅ Import a markdown file to workplace
	'''
	echo.push_subroutine(sys._getframe().f_code.co_name)

	echo.clog(f'importing markdown file: {file}')
	try:
		# file type
		file_type = type
		if draft: file_type = f'{file_type}_draft'
		# file name
		true_file_name = os.path.basename(file)[:-3]
		file_name = utils.slugify(os.path.basename(file)[:-3])
		# create time
		time_stamp = int(os.path.getctime(file))
		year = str(time.localtime(time_stamp).tm_year)
		mon = str(time.localtime(time_stamp).tm_mon)
		# dir
		base_dir = os.path.join(globalvar.get_global('wp_dir'), f'{file_type}s')
		year_dir = os.path.join(base_dir, year)
		mon_dir = os.path.join(year_dir, mon)
		save_dir = os.path.join(mon_dir, f'./{file_name}.md')
		# check whether exists
		if not os.path.exists(year_dir): os.mkdir(year_dir)
		if not os.path.exists(mon_dir): os.mkdir(mon_dir)
		# read default meta profile
		meta_data = globalvar.get_global('conf')['defaultProperties']
		meta_data['created'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time_stamp))
		meta_data['modified'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(os.path.getmtime(file))))
		meta_data['title'] = true_file_name
		meta_data['type'] = file_type
		meta_data['fields'] = globalvar.get_global('conf')['defaultFields']
		if globalvar.get_global('conf')['defaultSlugType']:
			meta_data['slug'] = file_name
		# dump yaml
		meta = yaml.dump(meta_data, allow_unicode=True, default_flow_style=None)
		# dump
		with open(save_dir, 'w+', encoding='utf8') as f:
			f.write('---\n')
			f.write(meta)
			f.write('---\n')
			with open(file, 'r', encoding='utf8') as f1:
				f.write(f1.read())
		echo.csuccess(f'new item success: /{file_type}s/{year}/{mon}/{file_name}.md')
	except Exception as e:
		echo.cerr(f'error: {repr(e)}')
		traceback.print_exc()
		echo.cexit('FILE IMPORT FAILED')
	finally:
		echo.pop_subroutine()


@cli.command()
def status():
	'''
	✅ Check the current status of current branch of workplace
	'''
	echo.push_subroutine(sys._getframe().f_code.co_name)

	echo.clog('checking status of workplace...')
	try:
		git_status_subprocess()
	except Exception as e:
		echo.cerr(f'status check failed. error: {repr(e)}')
		traceback.print_exc()
		echo.cexit('STATUS CHECK FAILED')
	finally:
		echo.pop_subroutine()


@cli.command()
@click.pass_context
def commit(ctx):
	'''
	✅ Clean working tree: `git commit -am` for current branch
	'''
	echo.push_subroutine(sys._getframe().f_code.co_name)

	echo.clog('cleaning working tree.')
	try:
		ctx.invoke(format)
		echo.clog('status: ')
		git_status_subprocess()
		echo.clog('git add .')
		git_add_all_subprocess()
		echo.clog('git commit')
		git_commit_subprocess(f'[Update] {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}')
		echo.csuccess('working tree cleaned.')
	except Exception as e:
		echo.cerr(f'working tree cleaning failed. error: {repr(e)}')
		traceback.print_exc()
		echo.cexit('WORKING TREE CLEANING FAILED')
	finally:
		echo.pop_subroutine()


@cli.command()
@click.argument('branch', type=click.Choice(['prod', 'test']))
def merge(branch: str):
	'''
	✅ Merge the branch with local repo
	'''
	echo.push_subroutine(sys._getframe().f_code.co_name)

	echo.clog(f'merging {branch} environment with local repo...')
	git_safe_merge_to_master(branch)

	echo.pop_subroutine()


@cli.command()
def push():
	'''
	✅ Update remote refs along with associated objects
	'''
	echo.push_subroutine(sys._getframe().f_code.co_name)

	echo.clog('pushing to remote')
	git_safe_push()
	echo.pop_subroutine()


@cli.command()
def discard_change():
	'''
	✅ Discard change on current branch: git reset --hard HEAD
	'''
	echo.push_subroutine(sys._getframe().f_code.co_name)
	
	echo.clog('start discarding changes...')
	git_safe_discard_change()

	echo.pop_subroutine()


@cli.command()
def prod_test():
	'''
	✅ Test connectvity of production environment
	'''
	echo.push_subroutine(sys._getframe().f_code.co_name)

	echo.clog('testing connectivity...')
	try:
		response = requests.get(f"{globalvar.get_global('conf')['prod']['url']}/welcome?token={globalvar.get_global('conf')['prod']['token']}", verify=globalvar.get_global('conf')['verify'])
		# If the response was successful, no Exception will be raised
		response.raise_for_status()
	except requests.HTTPError as http_err:
		echo.cerr(f'HTTP error occurred: {repr(http_err)}')
		traceback.print_exc()
		echo.cexit('PROD TEST FAILED')
	except Exception as err:
		echo.cerr(f'other error occurred: {repr(err)}')
		traceback.print_exc()
		echo.cexit('PROD TEST FAILED')
	else:
		res = response.json()
		echo.clog(f'RESPONSE: {res}')
		if res['code'] == 1: echo.clog('connectivity test passed')
		else: echo.cerr(f'Connectivity test failed, Message: {res["message"]}')
	finally:
		echo.pop_subroutine()


@cli.command()
def fix_git_utf8():
	'''
	✅ Fix utf-8 encoding error of git
	'''
	echo.push_subroutine(sys._getframe().f_code.co_name)

	echo.clog('WARNING:')
	click.echo('IMPORTANT: this command will configure the git on your system. Continue? [y/n] ', nl=False)
	user_in = input()

	try:
		if (user_in != 'y' and user_in != 'Y'): 
			echo.cexit('REJECTED')
		git_fix_utf8()
	except Exception as e:
		echo.cerr(f'error: {repr(e)}')
		traceback.print_exc()
		echo.cexit('UTF8 FIX FAILED')
	finally:
		echo.pop_subroutine()

# -------------- TESTING -------------- #

@cli.command()
def test():
	pass

#### Command Line Interface (CLI) End ####

if __name__ == '__main__':
	# main log
	click.echo(click.style('[typexo-cli-main]', bg='blue', fg='white'), nl=False)
	click.echo(' read configuration...')
	# read configuration
	read_conf()
	click.echo(click.style('-' * 40, fg = 'bright_blue'))
	# Enable click
	cli()
