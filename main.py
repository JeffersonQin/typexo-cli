import yaml
import os
import click
import requests

# Initialization for paths & caches
root_dir = os.path.split(os.path.abspath(__file__))[0]
config_dir = os.path.join(root_dir, 'config.yml')
conf = {}

def read_conf():
	# Read configuration
	with open(config_dir, 'r') as f:
		contents = f.read()
		global conf
		conf = yaml.load(contents, Loader=yaml.FullLoader)

#### Logging Start ####

def main_log(message: str):
	click.echo(click.style('[typexo-cli-main]', bg='blue', fg='white'), nl=False)
	click.echo(f" {message}")

def sub_log(command: str, message: str):
	click.echo(click.style(f"[{command}]", bg='magenta', fg='white'), nl=False)
	click.echo(f" {message}")

def sub_err(command: str, message: str):
	click.echo(click.style(f"[{command}]", bg='magenta', fg='white'), nl=False)
	click.echo(click.style(f" {message}", fg = 'bright_red'))


#### Logging End ####

#### Fetching Start ####

def fetch_contents():
	sub_log('fetch_contents', 'fetching contents...')
	try:
		response = requests.get(f"{conf['remote']['url']}/fetch_contents?token={conf['remote']['token']}")
		# If the response was successful, no Exception will be raised
		response.raise_for_status()
	except HTTPError as http_err:
		sub_err('fetch_contents', f'HTTP error occurred: {repr(http_err)}')
	except Exception as err:
		sub_err('fetch_contents', f'other error occurred: {repr(err)}')
	else:
		res = response.json()
		sub_log('fetch_contents', f'RESPONSE: {res}')
		if res['code'] == 1: sub_log('fetch_contents', 'connectivity test passed')
		else: 
			sub_err('fetch_contents', f'fetch contents failed, message: {res["message"]}')
			return

#### Fetching End ####

#### Command Line Interface (CLI) Start ####

@click.group()
def cli():
	pass


@cli.command()
def init():
	'''
	Initialize a git version control workplace from nothing
	'''
	sub_log('init', 'initializing workplace...')


@cli.command()
def rm():
	'''
	Delete the whole workplace
	'''
	sub_log('rm', 'deleting workplace...')


@cli.command()
def clone():
	'''
	Clone the workplace from remote repo
	'''
	sub_log('clone', 'cloning from remote repo...')


@cli.command()
def pull():
	'''
	Pull the workplace from PROD environment
	'''
	sub_log('pull', 'pulling from PROD environment...')


@cli.command()
def status():
	'''
	Check the current status of workplace
	'''
	sub_log('status', 'checking status of workplace...')


@cli.command()
def add():
	'''
	Add file contents to the index
	'''
	sub_log('add', 'adding file contents to index...')


@cli.command()
def commit():
	'''
	Record changes to the repository
	'''
	sub_log('commit', 'recoding changes...')


@cli.command()
def merge():
	'''
	Merge the PROD environment and local repo
	'''
	sub_log('merge', 'merging prod environment with local repo...')


@cli.command()
def push():
	'''
	Update remote refs along with associated objects
	'''
	sub_log('push', 'pushing to remote')


@cli.command()
def prod_test():
	'''
	test connectvity of production environment
	'''
	sub_log('prod-test', 'testing connectivity...')
	try:
		response = requests.get(f"{conf['remote']['url']}/welcome?token={conf['remote']['token']}")
		# If the response was successful, no Exception will be raised
		response.raise_for_status()
	except HTTPError as http_err:
		sub_err('prod-test', f'HTTP error occurred: {repr(http_err)}')
	except Exception as err:
		sub_err('prod-test', f'other error occurred: {repr(err)}')
	else:
		res = response.json()
		sub_log('prod-test', f'RESPONSE: {res}')
		if res['code'] == 1: sub_log('test', 'connectivity test passed')
		else: sub_err('prod-test', f'Connectivity test failed, Message: {res["message"]}')



#### Command Line Interface (CLI) End ####

if __name__ == '__main__':
	main_log('read configuration...')
	read_conf()
	click.echo(click.style('-' * 40, fg = 'bright_blue'))
	# Enable click
	cli()