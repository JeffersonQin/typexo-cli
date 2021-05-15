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
content_meta_exclude = ['cid', 'order', 'commentsNum', 'text', 'views']
meta_meta_exclude = ['count', 'order']

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
	Initialize a git version control workplace from nothing
	'''
	set_global('cmd_name', sys._getframe().f_code.co_name)

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
		clog(f'branch info: \n{git_branch()}')
	except Exception as e:
		cerr(f'error: {repr(e)}')
		traceback.print_exc()


@cli.command()
def rm():
	'''
	Delete the whole workplace
	'''
	set_global('cmd_name', sys._getframe().f_code.co_name)

	if not os.path.exists(wp_dir):
		cerr('workplace folder does not exist.')
		return

	clog('triggered to delete')
	click.echo('IMPORTANT: this command will delete everything in the workplace folder. Are you sure to continue? [y/n] ', nl=False)
	user_in = input()
	if (user_in != 'y' and user_in != 'Y'): return
	
	try:
		shutil.rmtree(wp_dir)
		csuccess('delete success.')
	except Exception as e:
		cerr(f'error: {repr(e)}')
		traceback.print_exc()


@cli.command()
def clone():
	'''
	Clone the workplace from remote repo
	'''
	set_global('cmd_name', sys._getframe().f_code.co_name)

	clog('cloning from remote repo...')


@cli.command()
@click.argument('source', type=click.Choice(['prod', 'test']))
def pull(source: str):
	'''
	Pull the workplace from prod / test environment
	'''
	set_global('cmd_name', sys._getframe().f_code.co_name)

	clog(f'pulling from {source} environment...')
	try:
		# PREREQUISITE: changes are staged, current branch clean
		status_res = git_status_native()
		git_status_subprocess()
		if not status_res.split('\n')[1] == 'nothing to commit, working tree clean':
			cerr('working tree not clean, make sure that all the changes are staged and committed.')
			return
		# PREREQUISITE: make sure that `source` branch exists
		# get initial branches
		branch_res = git_branch()
		clog(f'checking branches: \n{branch_res}')
		# check whether `source` branch exist
		if f'* {source}' not in branch_res.split('\n') and f'  {source}' not in branch_res.split('\n'):
			clog(f'"{source}" branch does not exist, creating...')
			# create `source` branch
			cb_res = git_create_branch_subprocess(source)
			csuccess(f'create "{source}" branch success.')
		else: csuccess(f'"{source}" branch exists.')
		# check branch status
		clog('branches: ')
		git_branch_subprocess()
		# checkout to source branch
		git_checkout_subprocess(source)
		csuccess(f'checkout to "{source}" success.')
		# check branch status after checkout
		clog('branches: ')
		git_branch_subprocess()
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
		if res == -1:
			cerr('INVALID FILE STRUCTURE, exiting program.')
			return
		# meta
		meta_data = fetch_resource('metas')
		if meta_data is None:
			cerr('META FETCHING FAILED, exiting program.')
			return
		meta_data = dump_metas(meta_data)
		if meta_data == -1:
			cerr('META DUMPING FAILED, exiting program')
			return
		# relationship
		pair_data = fetch_resource('relationships')
		if pair_data is None:
			cerr('RELATIONSHIP FETCHING FAILED, exiting program.')
			return
		pair_data = format_relationships(pair_data)
		if pair_data == -1:
			cerr('RELATIONSHIP FORMATTING FAILED, exiting program.')
			return
		# content
		content_data = fetch_resource('contents')
		if content_data is None:
			cerr('CONTENT FETCHING FAILED, exiting program.')
			return
		res = dump_contents(content_data, meta_data=meta_data, pair_data=pair_data)
		if res == -1:
			cerr('CONTENT DUMPING FAILED, exiting program.')
			return
		# ---------------------------- #
		# Check status
		clog('git status')
		git_status_subprocess()
		clog('git add .')
		git_add_subprocess()
		clog('git commit')
		git_commit_subprocess(f'Pull from "{source}": {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}')
		clog('git checkout master')
		git_checkout_subprocess('master')
		clog(f'git merge {source}')
		git_merge_subprocess(source)
		clog('git status')
		git_status_subprocess()
		diff = git_diff()
		clog(f'diff after merge: {diff}')
		if diff:
			cerr('CONFLICT OCCURRED DURING MERGE. please merge by `merge` command after the conflict is resolved.')
			return
		csuccess('pull success.')
		if source == 'prod':
			clog('NOTE: PLEASE DO NOT DELETE THE `prod` BRANCH, THIS BRANCH IS USED TO MERGE THE PULL FROM PROD IN THE FUTURE.')
		if source == 'test':
			clog('auto deleting the `test` branch...')
			# TODO: delete test branch
	except Exception as e:
		cerr(f'pulling failed. error: {repr(e)}')
		traceback.print_exc()
		

@cli.command()
def status():
	'''
	Check the current status of workplace
	'''
	set_global('cmd_name', sys._getframe().f_code.co_name)

	clog('checking status of workplace...')
	git_status_subprocess()


@cli.command()
def add():
	'''
	Add file contents to the index
	'''
	set_global('cmd_name', sys._getframe().f_code.co_name)

	clog('adding file contents to index...')


@cli.command()
def commit():
	'''
	Record changes to the repository
	'''
	set_global('cmd_name', sys._getframe().f_code.co_name)

	clog('recoding changes...')


@cli.command()
def merge():
	'''
	Merge the PROD environment and local repo
	'''
	set_global('cmd_name', sys._getframe().f_code.co_name)

	clog('merging prod environment with local repo...')


@cli.command()
def push():
	'''
	Update remote refs along with associated objects
	'''
	set_global('cmd_name', sys._getframe().f_code.co_name)

	clog('pushing to remote')


@cli.command()
def prod_test():
	'''
	test connectvity of production environment
	'''
	set_global('cmd_name', sys._getframe().f_code.co_name)

	clog('testing connectivity...')
	try:
		response = requests.get(f"{get_global('conf')['remote']['url']}/welcome?token={get_global('conf')['remote']['token']}")
		# If the response was successful, no Exception will be raised
		response.raise_for_status()
	except HTTPError as http_err:
		cerr(f'HTTP error occurred: {repr(http_err)}')
		traceback.print_exc()
	except Exception as err:
		cerr(f'other error occurred: {repr(err)}')
		traceback.print_exc()
	else:
		res = response.json()
		clog(f'RESPONSE: {res}')
		if res['code'] == 1: clog('test', 'connectivity test passed')
		else: cerr(f'Connectivity test failed, Message: {res["message"]}')

@cli.command()
def fix_git_utf8():
	'''
	Fix utf-8 encoding error of git
	'''
	set_global('cmd_name', sys._getframe().f_code.co_name)

	clog('WARNING:')
	click.echo('IMPORTANT: this command will configure the git on your system. Continue? [y/n] ', nl=False)
	user_in = input()

	if (user_in != 'y' and user_in != 'Y'): return
	git_fix_utf8()

# -------------- TESTING -------------- #

@cli.command()
def test():
	git_add_subprocess()
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