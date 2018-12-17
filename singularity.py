## Helper functions for singularity container solution
from subprocess import check_output
import json
import os

#Source: https://singularityhub.github.io/singularity-cli/api/modules/spython/main/inspect.html#inspect
def get_container_details(image):
    '''
    Input: Container image file
    Output: dict of labels
    '''

    cmd = ['singularity', 'inspect', image]
    out_bytes = check_output(cmd)
    out_decoded = out_bytes.decode('utf-8').replace("'", '"')
    json_dict = json.loads(out_decoded)
    json_dict['image.filename'] = os.path.split(image)[1]

    return json_dict


def get_all_container(path):
    ''' This function is looking for img-files in a given path and returns their
    absolute path as a list
    '''
    return_value = []

    for root, _, files in os.walk(path):
        for filename in files:
            full_path = os.path.join(root, filename)
            # FIXME better check for magic rather than extensionm
            if os.path.splitext(full_path)[1] == '.img':
                return_value.append(full_path)

    return return_value
