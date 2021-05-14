import click
import os
from globalvar import *

def clog(message: str):
	click.echo(click.style(f"[{get_global('cmd_name')}]", bg='magenta', fg='white'), nl=False)
	click.echo(f" {message}")

def cerr(message: str):
	click.echo(click.style(f"[{get_global('cmd_name')}]", bg='magenta', fg='white'), nl=False)
	click.echo(click.style(f" {message}", fg = 'bright_red'))

def csuccess(message: str):
	click.echo(click.style(f"[{get_global('cmd_name')}]", bg='magenta', fg='white'), nl=False)
	click.echo(click.style(f" {message}", fg = 'green'))
