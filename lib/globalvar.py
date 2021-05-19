
def global_init():
	global global_dict
	global_dict = {}

def set_global(key: str, value):
	global_dict[key] = value

def get_global(key: str):
	return global_dict[key]

def push_old_name():
	global_dict['old_cmd_name'] = global_dict['cmd_name']

def pop_new_name():
	global_dict['cmd_name'] = global_dict['old_cmd_name']
