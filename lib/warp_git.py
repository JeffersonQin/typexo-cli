import git
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
