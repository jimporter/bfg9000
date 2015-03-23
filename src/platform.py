from node import Node

# TODO: This still needs some improvement to be more flexible
def target_name(target):
    if type(target).__name__ == 'Library':
        return 'lib{}.so'.format(target.name)
    elif type(target).__name__ == 'ObjectFile':
        return '{}.o'.format(target.name)
    else:
        return target.name
