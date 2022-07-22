import os
import sys
import json
import traceback
import requests

import globalvar
import echo
import utils


def fetch_database(source: str, database: str):
	echo.push_subroutine(sys._getframe().f_code.co_name)

	echo.clog(f'fetching {database}')

	cache_dir = os.path.join(globalvar.get_global('root_dir'), 'cache/')
	file_dir = os.path.join(cache_dir, f'{database}.json')

	if not os.path.exists(cache_dir): os.mkdir(cache_dir)

	utils.download_file(f"{globalvar.get_global('conf')[source]['url']}/fetch?db={database}&token={globalvar.get_global('conf')[source]['token']}", file_dir)
	
	try:
		with open(file_dir, 'r', encoding='utf8') as f:
			res = json.load(f)
			if res['code'] == 1: 
				echo.csuccess(f'connectivity test passed, message: {res["message"]}')
				return res['data']
			else: 
				echo.cerr(f'fetch contents failed, message: {res["message"]}')
				raise Exception(f'fetch contents failed, message: {res["message"]}')
	except Exception as e:
		echo.cerr(f'error: {repr(e)}')
		traceback.print_exc()
		echo.cexit(f'{source}/{database} FETCHING FAILED')
	finally:
		echo.pop_subroutine()


def post_data(item: str, target: str, add: list, update: list, delete: list):
	echo.push_subroutine(sys._getframe().f_code.co_name)

	echo.clog(f'posting data to {target} server...')
	try:
		url = f"{globalvar.get_global('conf')[target]['url']}/push_{item}"
		data = {
			'token': globalvar.get_global('conf')[target]['token'],
			'add': add,
			'update': update,
			'delete': delete
		}
		res = requests.post(url=url, data=json.dumps(data), verify=globalvar.get_global('conf')['verify']).json()
		if res['code'] == -1:
			echo.cerr(f'POST ERROR: {res["message"]}')
			raise Exception('POST REQUEST FAILED')
		if res['code'] == 1:
			echo.csuccess(f'POST {item} TO {target} SUCCESS, message: {res["message"]}')
			return res['add'], res['update'], res['delete']
		raise Exception(f'UNKNOWN STATUS CODE {res["code"]}, message: {res["message"]}')
	except Exception as e:
		echo.cerr(f'error: {repr(e)}')
		traceback.print_exc()
		echo.cexit('POSTING DATA FAILED')
	finally:
		echo.pop_subroutine()

