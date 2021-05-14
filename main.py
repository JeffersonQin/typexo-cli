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
config_dir = os.path.join(root_dir, 'config.yml')
wp_dir = os.path.join(root_dir, './workplace/')
readme_dir = os.path.join(wp_dir, 'README.md')
# configure structure
wp_essential_structure = {
	'folders': [
		'posts', 'pages', 'post_drafts', 'page_drafts'
	],
	'files': [
		'metas.json', 'relationship.json'
	]
}
# configure items exclude in content metadata
content_meta_exclude = ['cid', 'order', 'commentsNum', 'text', 'views']
# initialize other variable
conf = {}
cmd_name = 'main'

def read_conf():
	# Read configuration
	with open(config_dir, 'r') as f:
		contents = f.read()
		global conf
		conf = yaml.load(contents, Loader=yaml.FullLoader)

#### Logging Start ####

def clog(message: str):
	click.echo(click.style(f"[{cmd_name}]", bg='magenta', fg='white'), nl=False)
	click.echo(f" {message}")

def cerr(message: str):
	click.echo(click.style(f"[{cmd_name}]", bg='magenta', fg='white'), nl=False)
	click.echo(click.style(f" {message}", fg = 'bright_red'))

def csuccess(message: str):
	click.echo(click.style(f"[{cmd_name}]", bg='magenta', fg='white'), nl=False)
	click.echo(click.style(f" {message}", fg = 'green'))

#### Logging End ####

#### Fetching Start ####

def fetch_resource(resource: str):
	global cmd_name
	cmd_name = sys._getframe().f_code.co_name

	clog(f'fetching {resource}')

	cache_dir = os.path.join(root_dir, 'cache/')
	file_dir = os.path.join(cache_dir, f'{resource}.json')

	if not os.path.exists(cache_dir): os.mkdir(cache_dir)

	download_file(f"{conf['remote']['url']}/fetch_{resource}?token={conf['remote']['token']}", file_dir)
	
	try:
		with open(file_dir, 'r') as f:
			res = json.load(f)
			if res['code'] == 1: 
				csuccess(f'connectivity test passed, message: {res["message"]}')
				return res['data']
			else: 
				cerr(f'fetch contents failed, message: {res["message"]}')
				return None		
	except Exception as e:
		cerr(f'error occurred: {repr(e)}')
		traceback.print_exc()
	
#### Fetching End ####

#### utilities start ####

def download_file(url, dir):
	global cmd_name
	cmd_name = sys._getframe().f_code.co_name

	clog(f'start downloading: {url} => {dir}')
	try:
		# define request headers
		headers = {'Proxy-Connection':'keep-alive'}
		# start and block request
		r = requests.get(url, stream=True, headers=headers)
		# obtain content length
		length = int(r.headers['content-length'])
		clog(f'file size: {size_description(length)}')
		# start writing
		f = open(dir, 'wb+')
		# show in progressbar
		with click.progressbar(label="Downloading from remote: ", length=length) as bar:
			for chunk in r.iter_content(chunk_size = 512):
				if chunk:
					f.write(chunk)
					bar.update(len(chunk))
		csuccess('Download Complete.')
		f.close()
	except Exception as err:
		cerr(f'error: {repr(err)}')
		traceback.print_exc()


def size_description(size):
	'''
	Taken and modified from https://blog.csdn.net/wskzgz/article/details/99293181
	'''
	def strofsize(integer, remainder, level):
		if integer >= 1024:
			remainder = integer % 1024
			integer //= 1024
			level += 1
			return strofsize(integer, remainder, level)
		else:
			return integer, remainder, level

	units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
	integer, remainder, level = strofsize(size, 0, 0)
	if level + 1 > len(units):
		level = -1
	return ( '{}.{:>03d} {}'.format(integer, remainder, units[level]) )


def slugify(value, allow_unicode=True):
	'''
	Taken and modified from django/utils/text.py
	Copyright (c) Django Software Foundation and individual contributors.
	All rights reserved.
	Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
	dashes to single dashes. Remove characters that aren't alphanumerics,
	underscores, or hyphens. Convert to lowercase. Also strip leading and
	trailing whitespace, dashes, and underscores.
	'''
	value = str(value)
	if allow_unicode:
		value = unicodedata.normalize('NFKC', value)
	else:
		value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
	value = re.sub(r'[^\w\s-]', '', value.lower())
	return re.sub(r'[-\s]+', '-', value).strip('-_')

#### utilities end ####

#### localize start ####

def check_dirs():
	global cmd_name
	cmd_name = sys._getframe().f_code.co_name

	clog('checking essential structure...')
	try:
		for dir in wp_essential_structure['folders']:
			if not os.path.exists(os.path.join(wp_dir, dir)):
				os.mkdir(os.path.join(wp_dir, dir))
		csuccess('checking finished.')
	except Exception as e:
		cerr(f'error: {repr(e)}')
		traceback.print_exc()
		return -1


def write_contents(data: list):
	global cmd_name
	cmd_name = sys._getframe().f_code.co_name
	
	clog('writing contents...')
	try:
		for item in data:
			# obtain essential meta data
			type = f"{item['type']}s"
			create_local_time = time.localtime(item['created'])
			create_year = str(create_local_time.tm_year)
			create_month = str(create_local_time.tm_mon)
			file_name = slugify(item['title'])
			# dealing with directories
			base_dir = os.path.join(wp_dir, type)
			year_dir = os.path.join(base_dir, create_year)
			mon_dir = os.path.join(year_dir, create_month)
			# create if not exist
			if not os.path.exists(year_dir): os.mkdir(year_dir)
			if not os.path.exists(mon_dir): os.mkdir(mon_dir)
			# exclude some unneeded meta data
			for exclude in content_meta_exclude:
				if exclude in item.keys():
					item.pop(exclude)
			# format the metas for yml
			item['created'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(item['created']))
			item['modified'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(item['modified']))
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
			for key in item.keys():
				if item[key] == None: item[key] = ''
			clog(yaml.dump(item, allow_unicode=True))
			# start writing
			clog(f'success: /{type}/{create_year}/{create_month}/{file_name}.md')
	except Exception as e_in:
		cerr(f'error: /{type}/{create_year}/{create_month}/{file_name}.md')
		traceback.print_exc()
		return -1

#### localize end ####

#### local git start ####

def git_repo():
	return git.Repo(wp_dir)

def git_branch():
	wp_git = git_repo().git
	return wp_git.branch()

def git_branch_create(branch: str):
	wp_git = git_repo().git
	return wp_git.branch(branch)

def git_checkout(branch: str):
	wp_git = git_repo().git
	return wp_git.checkout(branch)

def git_status_native():
	wp_git = git_repo().git
	return wp_git.status()

#### Local git end ####

#### Command Line Interface (CLI) Start ####

@click.group()
def cli():
	pass


@cli.command()
def init():
	'''
	Initialize a git version control workplace from nothing
	'''
	global cmd_name
	cmd_name = sys._getframe().f_code.co_name

	clog('initializing workplace...')
	if not os.path.exists(wp_dir): os.mkdir(wp_dir)
	if os.listdir(wp_dir) != []:
		cerr('workplace folder is not empty. Try "rm" command first.')
		return
	try:
		git.Repo.init(path=wp_dir)
		csuccess('git initialization success.')
		# TODO: write file structure
		with open(readme_dir, 'w+') as f:
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
	global cmd_name
	cmd_name = sys._getframe().f_code.co_name

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
	global cmd_name
	cmd_name = sys._getframe().f_code.co_name

	clog('cloning from remote repo...')


@cli.command()
def pull():
	'''
	Pull the workplace from PROD environment
	'''
	global cmd_name
	cmd_name = sys._getframe().f_code.co_name
	
	clog('pulling from PROD environment...')
	try:
		# PREREQUISITE: changes are staged, current branch clean
		status_res = git_status_native()
		clog(f'git status: \n{status_res}')
		if not status_res.split('\n')[1] == 'nothing to commit, working tree clean':
			cerr('working tree not clean, make sure that all the changes are staged and committed.')
			return
		# PREREQUISITE: make sure that `prod` branch does not exist
		# get initial branches
		branch_res = git_branch()
		clog(f'checking branches: \n{branch_res}')
		# check whether `prod` branch exist
		for branch in branch_res.split('\n'):
			if branch == '* prod' or branch == '  prod':
				cerr(f'"prod" branch already exist. either use "rm-prod" to delete the branch, or resolve the previous merge.')
				return
		# create `prod` branch
		cb_res = git_branch_create('prod')
		csuccess('create "prod" branch success.')
		# check branch status
		branch_res = git_branch()
		clog(f'branches: \n{branch_res}')
		# checkout to prod branch
		git_checkout('prod')
		csuccess('checkout to "prod" success.')
		# check branch status after checkout
		branch_res = git_branch()
		clog(f'branches: \n{branch_res}')
		# delete all files except `.git`
		for sub_dir in os.listdir(wp_dir):
			if os.path.isdir(os.path.join(wp_dir, sub_dir)) and (sub_dir in wp_essential_structure['folders']): 
				shutil.rmtree(os.path.join(wp_dir, sub_dir))
			if os.path.isfile(os.path.join(wp_dir, sub_dir)) and (sub_dir in wp_essential_structure['files']):
				os.remove(os.path.join(wp_dir, sub_dir))
		# ---------------------------- #
		# writing section start
		# check structure
		res = check_dirs()
		if res == -1:
			cerr('INVALID FILE STRUCTURE, exiting program.')
			return
		# content
		data = fetch_resource('contents')
		if data is None:
			cerr('DATA FETCHING FAILED, exiting program.')
			return
		res = write_contents(data)
		if res == -1:
			cerr('DATA WRITING FAILED, exiting program.')
			return

	except Exception as e:
		cerr(f'pulling failed. error: {repr(e)}')
		traceback.print_exc()
		

@cli.command()
def status():
	'''
	Check the current status of workplace
	'''
	global cmd_name
	cmd_name = sys._getframe().f_code.co_name

	clog('checking status of workplace...')


@cli.command()
def add():
	'''
	Add file contents to the index
	'''
	global cmd_name
	cmd_name = sys._getframe().f_code.co_name

	clog('adding file contents to index...')


@cli.command()
def commit():
	'''
	Record changes to the repository
	'''
	global cmd_name
	cmd_name = sys._getframe().f_code.co_name

	clog('recoding changes...')


@cli.command()
def merge():
	'''
	Merge the PROD environment and local repo
	'''
	global cmd_name
	cmd_name = sys._getframe().f_code.co_name

	clog('merging prod environment with local repo...')


@cli.command()
def rm_prod():
	'''
	Delete PROD branch in your local repo
	'''


@cli.command()
def push():
	'''
	Update remote refs along with associated objects
	'''
	global cmd_name
	cmd_name = sys._getframe().f_code.co_name

	clog('pushing to remote')


@cli.command()
def prod_test():
	'''
	test connectvity of production environment
	'''
	global cmd_name
	cmd_name = sys._getframe().f_code.co_name

	clog('testing connectivity...')
	try:
		response = requests.get(f"{conf['remote']['url']}/welcome?token={conf['remote']['token']}")
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