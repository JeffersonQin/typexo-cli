
def global_init():
	global global_dict
	global_dict = {}

def set_global(key: str, value):
	global_dict[key] = value

def get_global(key: str):
	return global_dict[key]
