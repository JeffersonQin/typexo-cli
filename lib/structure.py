import os
import sys

import echo
import globalvar


def check_dirs():
	echo.push_subroutine(sys._getframe().f_code.co_name)

	echo.clog('checking essential structure...')
	try:
		for dir in globalvar.get_global('wp_essential_structure')['folders']:
			if not os.path.exists(os.path.join(globalvar.get_global('wp_dir'), dir)):
				os.mkdir(os.path.join(globalvar.get_global('wp_dir'), dir))
		echo.csuccess('checking finished.')
	except Exception as e:
		echo.cerr(f'error: {repr(e)}')
		traceback.print_exc()
		echo.cexit('INVALID FILE STRUCTURE')
	finally:
		echo.pop_subroutine()
