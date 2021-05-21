import yaml
import os
import click
import requests
import git
import sys
import shutil
import time
import re
import unicodedata
import json
import traceback
import copy


# initialize paths & caches
root_dir = os.path.split(os.path.abspath(__file__))[0]
lib_dir = os.path.join(root_dir, './lib/')
config_dir = os.path.join(root_dir, 'config.yml')
wp_dir = os.path.join(root_dir, './workplace/')
readme_dir = os.path.join(wp_dir, 'README.md')

# import lib
sys.path.insert(0, lib_dir)
from utils import *
from globalvar import *
from pull import *
from warp_git import *
from read import *
from echo import *
from deploy import *

# initialize subroutine
init_subroutine()

# initialize global var
global_init()

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
content_meta_string = ['title', 'slug', 'text', 'template', 'type', 'status', 'password', 'allowComment', 'allowPing', 'allowFeed']
content_meta_int = ['created', 'modified', 'authorId']

# globalize other variable
set_global('conf', {})
set_global('cmd_name', 'main')
set_global('wp_dir', wp_dir)
set_global('root_dir', root_dir)
set_global('lib_dir', lib_dir)
set_global('config_dir', config_dir)
set_global('wp_essential_structure', wp_essential_structure)
set_global('content_meta_exclude', content_meta_exclude)
set_global('meta_meta_exclude', meta_meta_exclude)
set_global('content_check_essential', content_check_essential)
set_global('content_meta_string', content_meta_string)
set_global('content_meta_int', content_meta_int)

def read_conf():
	# Read configuration
	with open(config_dir, 'r', encoding='utf8') as f:
		contents = f.read()
		set_global('conf', yaml.load(contents, Loader=yaml.FullLoader))

#### Command Line Interface (CLI) Start ####

@click.group()
def cli():
	pass


@cli.command()
def init():
	'''
	🚧 Initialize a git version control workplace from nothing
	'''
	push_subroutine(sys._getframe().f_code.co_name)

	clog('initializing workplace...')
	if not os.path.exists(wp_dir): os.mkdir(wp_dir)
	if os.listdir(wp_dir) != []:
		cerr('workplace folder is not empty. Try "rm" command first.')
		return
	try:
		git_init_subprocess()
		csuccess('git initialization success.')
		# TODO: write file structure
		with open(readme_dir, 'w+', encoding='utf8') as f:
			f.write('This file is created automatically by [typexo-cli](https://github.com/JeffersonQin/typexo-cli)')
		csuccess('write file test success.')
		add_res = git_repo().index.add(items=['README.md'])
		clog(f'add README.md: \n{add_res}')
		commit_res = git_repo().index.commit('Initial auto commit by typexo.')
		clog(f'commit (initial auto): \n{commit_res}')
		clog(f'branch info: \n{git_branch_native()}')
	except Exception as e:
		cerr(f'error: {repr(e)}')
		traceback.print_exc()
		cexit('INIT FAILED')
	finally:
		pop_subroutine()


@cli.command()
def rm():
	'''
	✅ Delete the whole workplace
	'''
	push_subroutine(sys._getframe().f_code.co_name)

	if not os.path.exists(wp_dir):
		cerr('workplace folder does not exist.')
		return

	clog('triggered to delete')
	click.echo('IMPORTANT: this command will delete everything in the workplace folder. Are you sure to continue? [y/n] ', nl=False)
	user_in = input()
	if (user_in != 'y' and user_in != 'Y'):
		cexit('REJECTED')
	try:
		shutil.rmtree(wp_dir)
		csuccess('delete success.')
	except Exception as e:
		cerr(f'error: {repr(e)}')
		traceback.print_exc()
		cexit('REMOVE WP FAILED')
	finally:
		pop_subroutine()


@cli.command()
@click.argument('repo')
def clone(repo: str):
	'''
	❌ Clone the workplace from remote repo
	'''
	push_subroutine(sys._getframe().f_code.co_name)

	clog('cloning from remote repo...')

	pop_subroutine()


@cli.command()
@click.argument('source', type=click.Choice(['prod', 'test']))
def pull(source: str):
	'''
	✅ Pull the workplace from prod / test environment
	'''
	push_subroutine(sys._getframe().f_code.co_name)

	clog(f'pulling from {source} environment...')
	try:
		# safe switch to `source` branch
		git_safe_switch(source)
		# delete all files except `.git`
		for sub_dir in os.listdir(wp_dir):
			if os.path.isdir(os.path.join(wp_dir, sub_dir)) and (sub_dir in wp_essential_structure['folders']): 
				shutil.rmtree(os.path.join(wp_dir, sub_dir))
			if os.path.isfile(os.path.join(wp_dir, sub_dir)) and (sub_dir in wp_essential_structure['files']):
				os.remove(os.path.join(wp_dir, sub_dir))
		# ---------------------------- #
		# dumping section start
		# check structure
		res = check_dirs()
		# meta
		meta_data = fetch_database(source, 'metas')
		dump_metas(copy.deepcopy(meta_data))
		meta_data = format_metas(meta_data)
		# relationship
		pair_data = fetch_database(source, 'relationships')
		pair_data = format_relationships(pair_data)
		# fields
		field_data = fetch_database(source, 'fields')
		field_data = format_fields(field_data)
		# content
		content_data = fetch_database(source, 'contents')
		res = dump_contents(content_data, meta_data=meta_data, pair_data=pair_data, field_data=field_data)
		# ---------------------------- #
		clog('git status')
		git_status_subprocess()
		clog('git add .')
		git_add_all_subprocess()
		clog('git commit')
		git_commit_subprocess(f'Pull from "{source}": {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}')
		git_safe_merge_to_master(source)
	except Exception as e:
		cerr(f'pulling failed. error: {repr(e)}')
		traceback.print_exc()
		cexit(f'PULL FROM {source} FAILED')
	finally:
		pop_subroutine()


@cli.command()
@click.argument('source', type=click.Choice(['prod', 'test']))
def diff(source: str):
	'''
	🚧 Show difference between local workplace and prod / test
	'''
	push_subroutine(sys._getframe().f_code.co_name)

	clog(f'differing with {source}...')
	try:
		# safe checkout to master
		git_safe_switch('master')
		# content
		# get remote contents
		remote_contents = fetch_database(source, 'contents')
		# read local contents
		local_contents = read_local_contents()
		# diff contents between local and remote 
		diff_contents(local_contents, remote_contents)
	except Exception as e:
		cerr(f'deploying failed. error: {repr(e)}')
		traceback.print_exc()
		cexit('DEPLOYING FAILED')
	finally:
		pop_subroutine()


@cli.command()
@click.pass_context
def deploy(ctx):
	'''
	🚧 Deploy the local workspace to PROD server
	'''
	push_subroutine(sys._getframe().f_code.co_name)

	clog(f'deploying to server...')
	try:
		# safe checkout to master
		git_safe_switch('master')
		# pull from server (in which will safe checkout to prod)
		ctx.invoke(pull, source='prod')
		# content
		# get remote contents
		remote_contents = fetch_database('prod', 'contents')
		# read local contents
		local_contents = read_local_contents()
		# diff contents between local and remote 
		new_contents, modified_contents, deleted_contents, deleted_titles = diff_contents(local_contents, remote_contents)
		# format the new & modified contents
		new_contents_dict = { new_content['hash']: new_content for new_content in new_contents }
		modified_contents_dict = { modified_content['cid']: modified_content for modified_content in modified_contents }
		# post content to server
		res_add, res_update, res_delete = post_data('contents', 'prod', new_contents, modified_contents, deleted_contents)
		# log post response
		# log add content
		for res in res_add:
			if res['code'] == -1:
				cerr(f'POST RESULT ERROR: {res["message"]}')
				raise Exception(f'POST REQUEST (ADD CONTENT) FAILED FOR hash: {res["hash"]}, dir: {new_contents_dict[res["hash"]]["dir"]}')
			elif res['code'] == 1:
				csuccess(f'POST SUCCESS: ADD CONTENT hash: {res["hash"]}, cid: {res["cid"]}, dir: {new_contents_dict[res["hash"]]["dir"]}')
			else: raise Exception(f'UNKNOWN STATUS CODE {res["code"]}, message: {res["message"]}')
		# log update content
		for res in res_update:
			if res['code'] == -1:
				cerr(f'POST RESULT ERROR: {res["message"]}')
				raise Exception(f'POST REQUEST (UPDATE CONTENT) FAILED FOR cid: {res["cid"]}, dir: {modified_contents_dict[res["cid"]]["dir"]}')
			elif res['code'] == 1:
				csuccess(f'POST SUCCESS: UPDATE CONTENT cid: {res["cid"]}, dir: {modified_contents_dict[res["cid"]]["dir"]}')
			else: raise Exception(f'UNKNOWN STATUS CODE {res["code"]}, message: {res["message"]}')
		# log delete content
		for res in res_delete:
			if res['code'] == -1:
				cerr(f'POST RESULT ERROR: {res["message"]}')
				raise Exception(f'POST REQUEST (DELETE CONTENT) FAILED FOR cid: {res["cid"]}, title: {deleted_titles[str(res["cid"])]}')
			elif res['code'] == 1:
				csuccess(f'POST SUCCESS: UPDATE CONTENT cid: {res["cid"]}, title: {deleted_titles[str(res["cid"])]}')
			else: raise Exception(f'UNKNOWN STATUS CODE {res["code"]}, message: {res["message"]}')

	except Exception as e:
		cerr(f'deploying failed. error: {repr(e)}')
		traceback.print_exc()
		cexit('DEPLOYING FAILED')
	finally:
		pop_subroutine()


@cli.command()
def status():
	'''
	✅ Check the current status of current branch of workplace
	'''
	push_subroutine(sys._getframe().f_code.co_name)

	clog('checking status of workplace...')
	try:
		git_status_subprocess()
	except Exception as e:
		cerr(f'status check failed. error: {repr(e)}')
		traceback.print_exc()
		cexit('STATUS CHECK FAILED')
	finally:
		pop_subroutine()


@cli.command()
def commit():
	'''
	✅ Clean working tree: `git commit -am` for current branch
	'''
	push_subroutine(sys._getframe().f_code.co_name)

	clog('cleaning working tree.')
	try:
		clog('status: ')
		git_status_subprocess()
		clog('git add .')
		git_add_all_subprocess()
		clog('git commit')
		git_commit_subprocess(f'[Update] {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}')
		csuccess('working tree cleaned.')
	except Exception as e:
		cerr(f'working tree cleaning failed. error: {repr(e)}')
		traceback.print_exc()
		cexit('WORKING TREE CLEANING FAILED')
	finally:
		pop_subroutine()


@cli.command()
@click.argument('branch', type=click.Choice(['prod', 'test']))
def merge(branch: str):
	'''
	✅ Merge the branch with local repo
	'''
	push_subroutine(sys._getframe().f_code.co_name)

	clog(f'merging {branch} environment with local repo...')
	git_safe_merge_to_master(branch)

	pop_subroutine()


@cli.command()
def push():
	'''
	❌ Update remote refs along with associated objects
	'''
	push_subroutine(sys._getframe().f_code.co_name)

	clog('pushing to remote')

	pop_subroutine()


@cli.command()
def discard_change():
	'''
	✅ Discard change on current branch: git reset --hard HEAD
	'''
	push_subroutine(sys._getframe().f_code.co_name)
	
	clog('start discarding changes...')
	git_safe_discard_change()

	pop_subroutine()


@cli.command()
def prod_test():
	'''
	✅ Test connectvity of production environment
	'''
	push_subroutine(sys._getframe().f_code.co_name)

	clog('testing connectivity...')
	try:
		response = requests.get(f"{get_global('conf')['remote']['url']}/welcome?token={get_global('conf')['remote']['token']}")
		# If the response was successful, no Exception will be raised
		response.raise_for_status()
	except HTTPError as http_err:
		cerr(f'HTTP error occurred: {repr(http_err)}')
		traceback.print_exc()
		cexit('PROD TEST FAILED')
	except Exception as err:
		cerr(f'other error occurred: {repr(err)}')
		traceback.print_exc()
		cexit('PROD TEST FAILED')
	else:
		res = response.json()
		clog(f'RESPONSE: {res}')
		if res['code'] == 1: clog('test', 'connectivity test passed')
		else: cerr(f'Connectivity test failed, Message: {res["message"]}')
	finally:
		pop_subroutine()


@cli.command()
def fix_git_utf8():
	'''
	✅ Fix utf-8 encoding error of git
	'''
	push_subroutine(sys._getframe().f_code.co_name)

	clog('WARNING:')
	click.echo('IMPORTANT: this command will configure the git on your system. Continue? [y/n] ', nl=False)
	user_in = input()

	try:
		if (user_in != 'y' and user_in != 'Y'): 
			cexit('REJECTED')
		git_fix_utf8()
	except Exception as e:
		cerr(f'error: {repr(e)}')
		traceback.print_exc()
		cexit('UTF8 FIX FAILED')
	finally:
		pop_subroutine()

# -------------- TESTING -------------- #

@cli.command()
def test():
	print(read_local_contents())
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
