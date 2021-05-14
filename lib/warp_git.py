import git
import os
import subprocess
from globalvar import * 


def git_repo():
	return git.Repo(get_global('wp_dir'))


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


def git_merge(branch: str):
	wp_git = git_repo().git
	return wp_git.merge(branch)


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


def git_unstaged():
	return git_untracked() + git_diff()

###########################################################################

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


def git_add_subprocess():
	subprocess.call(['git', '-C', get_global('wp_dir'), 'add', get_global('wp_dir')])


def git_commit_subprocess(message: str):
	subprocess.call(['git', '-C', get_global('wp_dir'), 'commit', '-m', f'"{message}"'])


def git_checkout_subprocess(branch: str):
	subprocess.call(['git', '-C', get_global('wp_dir'), 'checkout', branch])


def git_branch_subprocess():
	subprocess.call(['git', '-C', get_global('wp_dir'), 'branch'])


def git_create_branch_subprocess(branch: str):
	subprocess.call(['git', '-C', get_global('wp_dir'), 'branch', branch])
