import yaml
import os
import click
import requests
import git
import sys
import shutil
import time
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
	🚧 Initialize a git version control workplace from nothing
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
		# TODO: write file structure
		with open(readme_dir, 'w+', encoding='utf8') as f:
			f.write('This file is created automatically by [typexo-cli](https://github.com/JeffersonQin/typexo-cli)')
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
@click.argument('repo')
def clone(repo: str):
	'''
	❌ Clone the workplace from remote repo
	'''
	echo.push_subroutine(sys._getframe().f_code.co_name)

	echo.clog('cloning from remote repo...')

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
		# delete all files except `.git`
		for sub_dir in os.listdir(wp_dir):
			if os.path.isdir(os.path.join(wp_dir, sub_dir)) and (sub_dir in wp_essential_structure['folders']): 
				shutil.rmtree(os.path.join(wp_dir, sub_dir))
			if os.path.isfile(os.path.join(wp_dir, sub_dir)) and (sub_dir in wp_essential_structure['files']):
				os.remove(os.path.join(wp_dir, sub_dir))
		# ---------------------------- #
		# dumping section start
		# check structure
		res = structure.check_dirs()
		# meta
		meta_data = messenger.fetch_database(source, 'metas')
		tdump.dump_metas(tformatter.format_metas(copy.deepcopy(meta_data)))
		meta_data = tformatter.format_metas_for_contents(meta_data)
		# relationship
		pair_data = messenger.fetch_database(source, 'relationships')
		pair_data = tformatter.format_relationships(pair_data)
		# fields
		field_data = messenger.fetch_database(source, 'fields')
		field_data = tformatter.format_fields(field_data)
		# content
		content_data = messenger.fetch_database(source, 'contents')
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
def deploy(ctx):
	'''
	🚧 Deploy the local workspace to PROD server
	'''
	echo.push_subroutine(sys._getframe().f_code.co_name)

	echo.clog(f'deploying to server...')
	try:
		# safe checkout to master
		git_safe_switch('master')
		# pull from server (in which will safe checkout to prod)
		ctx.invoke(pull, source='prod')
		# content
		# get remote contents
		remote_contents = messenger.fetch_database('prod', 'contents')
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
		res_add, res_update, res_delete = messenger.post_data('contents', 'prod', new_contents, modified_contents, deleted_contents)
		# log post response
		# log add content
		for res in res_add:
			if res['code'] == -1:
				echo.cerr(f'POST RESULT ERROR: {res["message"]}')
				raise Exception(f'POST REQUEST (ADD CONTENT) FAILED FOR hash: {res["hash"]}, dir: {new_contents_dict[res["hash"]]["dir"]}')
			elif res['code'] == 1:
				echo.csuccess(f'POST SUCCESS: ADD CONTENT hash: {res["hash"]}, cid: {res["cid"]}, dir: {new_contents_dict[res["hash"]]["dir"]}')
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
				echo.csuccess(f'POST SUCCESS: UPDATE CONTENT cid: {res["cid"]}, title: {deleted_titles[str(res["cid"])]}')
			else: raise Exception(f'UNKNOWN STATUS CODE {res["code"]}, message: {res["message"]}')
		# meta
		local_metas = read.read_local_metas()
		post_metas = read.read_metas_in_posts()
		remote_metas = tformatter.format_metas(messenger.fetch_database('prod', 'metas'))

		new_metas, modified_metas, deleted_metas, deleted_names = tdiff.diff_metas(local_metas, post_metas, remote_metas)

		print(new_metas)
		print(modified_metas)
		print(deleted_metas)
		print(deleted_names)


	except Exception as e:
		echo.cerr(f'deploying failed. error: {repr(e)}')
		traceback.print_exc()
		echo.cexit('DEPLOYING FAILED')
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
def commit():
	'''
	✅ Clean working tree: `git commit -am` for current branch
	'''
	echo.push_subroutine(sys._getframe().f_code.co_name)

	echo.clog('cleaning working tree.')
	try:
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
	❌ Update remote refs along with associated objects
	'''
	echo.push_subroutine(sys._getframe().f_code.co_name)

	echo.clog('pushing to remote')

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
		response = requests.get(f"{globalvar.get_global('conf')['prod']['url']}/welcome?token={globalvar.get_global('conf')['prod']['token']}")
		# If the response was successful, no Exception will be raised
		response.raise_for_status()
	except HTTPError as http_err:
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
