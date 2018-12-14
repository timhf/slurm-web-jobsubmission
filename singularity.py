## Helper functions for singularity container solution
from subprocess import check_output
import json

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

    return json_dict
