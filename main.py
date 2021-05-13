import yaml
import os
import click
import requests

# Initialization for paths & caches
root_dir = os.path.split(os.path.abspath(__file__))[0]
config_dir = os.path.join(root_dir, 'config.yml')
conf = {}


def main_log(message: str):
	click.echo(click.style('[typexo-cli-main]', bg='blue', fg='white'), nl=False)
	click.echo(f" {message}")

def sub_log(command: str, message: str):
	click.echo(click.style(f"[{command}]", bg='magenta', fg='white'), nl=False)
	click.echo(f" {message}")

def sub_err(command: str, message: str):
	click.echo(click.style(f"[{command}]", bg='magenta', fg='white'), nl=False)
	click.echo(click.style(f" {message}", fg = 'bright_red'))



def read_conf():
	# Read configuration
	with open(config_dir, 'r') as f:
		contents = f.read()
		global conf
		conf = yaml.load(contents, Loader=yaml.FullLoader)

@click.group()
def cli():
	pass


@cli.command()
def test():
	sub_log('test', 'Start Testing Connectivity...')
	try:
		response = requests.get(f"{conf['remote']['url']}/welcome?token={conf['remote']['token']}")
		# If the response was successful, no Exception will be raised
		response.raise_for_status()
	except HTTPError as http_err:
		sub_err('test', f'HTTP error occurred: {repr(http_err)}')
	except Exception as err:
		sub_err('test', f'Other error occurred: {repr(err)}')
	else:
		res = response.json()
		sub_log('test', f'RESPONSE: {res}')
		if res['code'] == 1: sub_log('test', 'Connectivity test passed')
		else: sub_err('test', f'Connectivity test failed, Message: {res["message"]}')


@cli.command()
def fetch_contents():
	sub_log('fetch_contents', 'Start Fetching Contents...')
	try:
		response = requests.get(f"{conf['remote']['url']}/fetch_contents?token={conf['remote']['token']}")
		# If the response was successful, no Exception will be raised
		response.raise_for_status()
	except HTTPError as http_err:
		sub_err('fetch_contents', f'HTTP error occurred: {repr(http_err)}')
	except Exception as err:
		sub_err('fetch_contents', f'Other error occurred: {repr(err)}')
	else:
		res = response.json()
		sub_log('fetch_contents', f'RESPONSE: {res}')
		if res['code'] == 1: sub_log('fetch_contents', 'Connectivity test passed')
		else: 
			sub_err('fetch_contents', f'Fetch contents failed, Message: {res["message"]}')
			return
		


if __name__ == '__main__':
	main_log('PROGRAM STARTS')
	main_log('Read Configuration')
	read_conf()
	# Enable click
	cli()