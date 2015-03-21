from node import Node

# TODO: This still needs some improvement to be more flexible
def target_name(node):
    if node.kind == 'library' or node.kind == 'external_library':
        return 'lib{}.so'.format(node.name)
    elif node.kind == 'object_file':
        return '{}.o'.format(node.name)
    else:
        return node.name
