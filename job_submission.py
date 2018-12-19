from django.conf import settings
import os
import tempfile
import zipfile
import subprocess
import io

VAR_FOLDER = "/var/job_sched"

def handle_upload_file(file):
    temp_filename = os.path.join(VAR_FOLDER, next(tempfile._get_candidate_names()))
    temp_extraction_folder = os.path.join(VAR_FOLDER, next(tempfile._get_candidate_names()))

    os.mkdir(temp_extraction_folder)

    with open(temp_filename, 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)

    with zipfile.ZipFile(temp_filename, 'r') as zip_ref:
        zip_ref.extractall(temp_extraction_folder)

    return temp_extraction_folder

def submit_job(cpus, ram, gpus, job_name, comment, uid, user_email, singularity_image, temp_path, entry_point):
    #give all files to the user
    os.chown(temp_path, uid=uid, gid=-1)

    #entry file to absolute path for image
    entry_point_mount = os.path.join("/auto_mount_point", entry_point)

    #select application to execute script...
    if not os.access(entry_point, os.X_OK):
        _, extension = os.path.splitext(entry_point)
        if extension == ".py":
            run_command = "python"
        elif extension == ".sh":
            run_command = "sh"
    else:
        # executable file, run without interpreter
        run_command = ""

    singularity_image_path = os.path.join(settings.SINGULARITY_IMAGES_FOLDER, singularity_image)

    script_command = "singularity exec --nv -B {0}:/auto_mount_point {1} {2} {3}".format(temp_path, singularity_image_path, run_command, entry_point_mount)

    #build slurm script
    slurm_script_path = os.path.join(temp_path, "runner.job")
    with open(slurm_script_path, "w") as script:
        script.write("#! /bin/bash" + os.linesep)
        script.write("#SBATCH --job-name={}".format(job_name) + os.linesep)
        script.write("#SBATCH --ntasks={}".format(cpus) + os.linesep)
        script.write("#SBATCH --mem={}".format(ram) + os.linesep)
        script.write("#SBATCH --mail-type=END,FAIL" + os.linesep)
        script.write("#SBATCH --mail-user={}".format(user_email) + os.linesep)
        script.write("#SBATCH --output={}".format(os.path.join(temp_path, "stdout-%j.out")) + os.linesep)
        if gpus >= 1:
            script.write("#SBATCH --gres=gpu:1" + os.linesep)

        script.write(script_command + os.linesep)

    #start job
    args = ["sbatch", "--uid={}".format(uid), slurm_script_path]
    stdout = subprocess.check_output(args).strip()
    if not stdout.startswith(b"Submitted batch job"):
        return -1
    #return job ID
    return int(stdout.split()[-1])

#compress a folder and return a byte stream of the zip archive
def compress_folder_into_zip(data_path):
    stream = io.BytesIO()
    zip_handle = zipfile.ZipFile(stream, 'w')
    for root, dirs, files in os.walk(data_path):
        for file in files:
            file_path = os.path.join(root, file)
            zip_handle.write(file_path, os.path.relpath(file_path, data_path))
    zip_handle.close()
    return stream
