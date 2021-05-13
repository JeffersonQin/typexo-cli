import yaml
import os
import click
import requests
import git
import sys
import shutil

# Initialization for paths & caches
root_dir = os.path.split(os.path.abspath(__file__))[0]
config_dir = os.path.join(root_dir, 'config.yml')
wp_dir = os.path.join(root_dir, './workplace/')
readme_dir = os.path.join(wp_dir, 'README.md')
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

def fetch_contents():
	global cmd_name
	cmd_name = sys._getframe().f_code.co_name
	
	clog('fetching contents...')
	try:
		response = requests.get(f"{conf['remote']['url']}/fetch_contents?token={conf['remote']['token']}")
		# If the response was successful, no Exception will be raised
		response.raise_for_status()
	except HTTPError as http_err:
		cerr(f'HTTP error occurred: {repr(http_err)}')
	except Exception as err:
		cerr(f'other error occurred: {repr(err)}')
	else:
		res = response.json()
		clog(f'RESPONSE: {res}')
		if res['code'] == 1: csuccess('connectivity test passed')
		else: 
			cerr(f'fetch contents failed, message: {res["message"]}')
			return
		git_branch()

#### Fetching End ####

#### local git start ####

def git_repo():
	return git.Repo(wp_dir)

def git_branch():
	wp_git = git_repo().git
	return wp_git.branch()

def git_branch_create(branch:str):
	wp_git = git_repo().git
	return wp_git.branch(branch)

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
		cerr('workplace folder is not empty.')
		return
	try:
		git.Repo.init(path=wp_dir)
		csuccess('git initialization success.')
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
	if (user_in != 'y' and user_in != 'Y'): return;
	
	try:
		shutil.rmtree(wp_dir)
		csuccess('delete success.')
	except Exception as e:
		cerr(f'error: {repr(e)}')


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
	except Exception as err:
		cerr(f'other error occurred: {repr(err)}')
	else:
		res = response.json()
		clog(f'RESPONSE: {res}')
		if res['code'] == 1: clog('test', 'connectivity test passed')
		else: cerr(f'Connectivity test failed, Message: {res["message"]}')

# -------------- TESTING -------------- #

@cli.command()
def test():
	git_branch_create('prod')

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