import git
import os
import subprocess
import sys
import traceback
from globalvar import * 
from echo import *

# GitPython

def git_untracked():
	return git_repo().untracked_files


def git_diff():
	return [ item.a_path for item in git_repo().index.diff(None) ]


def git_deleted():
	ret = []
	for item in git_diff():
		if not os.path.exist(os.path.join(get_global('wp_dir'), item)):
			ret.append(item)


def git_modified():
	return git_diff() - git_deleted()


def git_uncommitted():
	return git_untracked() + git_diff()

# GitPython -- git native

def git_repo():
	return git.Repo(get_global('wp_dir'))


def git_branch_native():
	wp_git = git_repo().git
	return wp_git.branch()


def git_create_branch_native(branch: str):
	wp_git = git_repo().git
	return wp_git.branch(branch)


def git_checkout_native(branch: str):
	wp_git = git_repo().git
	return wp_git.checkout(branch)


def git_status_native():
	wp_git = git_repo().git
	return wp_git.status()


def git_merge_native(branch: str):
	wp_git = git_repo().git
	return wp_git.merge(branch)

# subprocess

def git_fix_utf8():
	subprocess.call(['git', 'config', '--global', 'core.quotepath', 'false'])
	subprocess.call(['git', 'config', '--global', 'gui.encoding', 'utf-8'])
	subprocess.call(['git', 'config', '--global', 'i18n.commit.encoding', 'utf-8'])
	subprocess.call(['git', 'config', '--global', 'i18n.logoutputencoding', 'utf-8'])


def git_init_subprocess():
	subprocess.call(['git', '-C', get_global('wp_dir'), 'init'])


def git_status_subprocess():
	subprocess.call(['git', '-C', get_global('wp_dir'), 'status'])


def git_merge_subprocess(branch: str):
	subprocess.call(['git', '-C', get_global('wp_dir'), 'merge', branch])


def git_add_all_subprocess():
	subprocess.call(['git', '-C', get_global('wp_dir'), 'add', get_global('wp_dir')])


def git_commit_subprocess(message: str):
	subprocess.call(['git', '-C', get_global('wp_dir'), 'commit', '-m', f'"{message}"'])


def git_checkout_subprocess(branch: str):
	subprocess.call(['git', '-C', get_global('wp_dir'), 'checkout', branch])


def git_branch_subprocess():
	subprocess.call(['git', '-C', get_global('wp_dir'), 'branch'])


def git_create_branch_subprocess(branch: str):
	subprocess.call(['git', '-C', get_global('wp_dir'), 'branch', branch])


def git_delete_branch_subprocess(branch: str):
	subprocess.call(['git', '-C', get_global('wp_dir'), 'branch', '-d', branch])


def git_reset_head_hard_subprocess():
	subprocess.call(['git', '-C', get_global('wp_dir'), 'reset', '--hard', 'HEAD'])

# warp

def is_working_tree_clean():
	if git_uncommitted(): return False
	else: return True


def git_safe_switch(branch: str):
	set_global('cmd_name', sys._getframe().f_code.co_name)

	try:
		# PREREQUISITE: changes are staged, current branch clean
		git_status_subprocess()
		if not is_working_tree_clean():
			cerr('working tree not clean, make sure that all the changes are staged and committed.')
			clog('To add to index and commit: you can either stage and commit manually, or just try `clean-tree` command.')
			clog('To discard changes: you can either discard manually, or just try `discard-change` command.')
			raise Exception('working tree not clean')
		# PREREQUISITE: make sure that branch exists
		# get initial branches
		git_branch_subprocess()
		branch_res = git_branch_native()
		clog(f'checking branches: \n{branch_res}')
		# check whether branch exist
		if f'* {branch}' in branch_res:
			csuccess('switch complete.')
			return
		if f'  {branch}' not in branch_res.split('\n'):
			clog(f'"{branch}" branch does not exist, creating...')
			# create branch
			cb_res = git_create_branch_subprocess(branch)
			csuccess(f'create "{branch}" branch success.')
		else: csuccess(f'"{branch}" branch exists.')
		# check branch status
		clog('branches: ')
		git_branch_subprocess()
		# checkout to branch
		git_checkout_subprocess(branch)
		csuccess(f'checkout to "{branch}" success.')
		# check branch status after checkout
		clog('branches: ')
		git_branch_subprocess()
		csuccess(f'switch complete')
	except Exception as e:
		cerr(f'error: {repr(e)}')
		traceback.print_exc()
		cexit(f'SAFE SWITCHING to {branch} FAILED')


def git_safe_merge_to_master(branch: str):
	set_global('cmd_name', sys._getframe().f_code.co_name)

	try:
		clog('safe switching to master...')
		git_safe_switch('master')
		clog(f'git merge {branch}')
		git_merge_subprocess(branch)
		clog('git status')
		git_status_subprocess()
		if not is_working_tree_clean():
			cerr('CONFLICT OCCURRED DURING MERGE. please merge by `merge` command after the conflict is resolved.')
			raise Exception('auto merge failed, working tree not clean.')
		csuccess('merge success.')
		if branch == 'prod':
			clog('NOTE: PLEASE DO NOT DELETE PROD BRANCH, this is used to merge conflcits in the future.')
			return
		if branch == 'test':
			clog(f'automatically deleting "{branch}" branch...')
			git_delete_branch_subprocess(branch)
			csuccess(f'"{branch}" delete success.')
	except Exception as e:
		cerr(f'error: {repr(e)}')
		traceback.print_exc()
		cexit(f'SAFE MERGE TO MASTER FROM {branch} FAILED')


def git_safe_discard_change():
	set_global('cmd_name', sys._getframe().f_code.co_name)
	
	try:
		clog('status: ')
		git_status_subprocess()
		clog('branch: ')
		git_branch_subprocess()
		branches = git_branch_native()
		b = 'master'
		for branch in branches.split('\n'):
			if branch.startswith('* '):
				b = branch[2:]
		click.echo(f'IMPORTANT: THIS COMMAND WILL DISCARD ALL THE UNSTAGED CHANGE ON BRANCH {b}, continue? [y/n] ', nl=False)
		user_in = input()
		if (user_in != 'y' and user_in != 'Y'):
			cexit('REJECTED')
		git_reset_head_hard_subprocess()
	except Exception as e:
		cerr(f'error: {repr(e)}')
		traceback.print_exc()
		cexit(f'DISCARDING FAILED')
