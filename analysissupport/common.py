import os
from collections import deque


def get_folders(path):
    folders = next(os.walk(path))[1]
    return sorted(folders)


def process_all(config, process_session, **args):
    pipeline_prefix = config['path']
    nesting = config['nesting']

    output = dict()

    if nesting == 0:
        output[()] = process_session(config, pipeline_prefix, **args)
        return output

    folders = get_folders(pipeline_prefix)
    level = 1

    q = deque()

    next_folders = [(os.path.join(pipeline_prefix, folder),
                     (folder,),
                     level)
                    for folder in folders]
    q.extend(next_folders)

    while len(q) != 0:
        path, past_folders, level = q.pop()

        if nesting < 0:
            output[past_folders] = process_session(config, path, **args)

            folders = get_folders(path)
            next_folders = [(os.path.join(path, folder),
                             past_folders + (folder,),
                             level + 1)
                            for folder in folders]
            q.extend(next_folders)
        else:
            if level == nesting:
                output[past_folders] = process_session(config, path, **args)
            elif level > nesting:
                continue
            elif level < nesting:
                folders = get_folders(path)
                next_folders = [(os.path.join(path, folder),
                                 past_folders + (folder,),
                                 level + 1)
                                for folder in folders]
                q.extend(next_folders)

    return output


def make_process_fun(process_session, **args):
    def fun(config):
        return process_all(config, process_session, **args)

    return fun
