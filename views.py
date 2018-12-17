from django.shortcuts import render
from django.template import loader
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect, Http404
from django.views import generic
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django import forms
from django_tables2 import tables, RequestConfig, columns
from django_tables2.utils import A
from django_filters.views import FilterView
import pyslurm
import os
import docker
import pwd

from .views_tables import QueueTable, DockerImagesTable, SelectFileTable, JobFilesTable, SingularityImagesTable
from .views_forms import JobCreationForm, JobCreationEntrySelectionForm
from .job_submission import *
from .singularity import *
from .pam_authentification_backend import PAMAuthentificationBackend

#get information about a job with a given id
def get_job(id):
    jobs = pyslurm.job().get()
    if id in jobs:
        return jobs[id]
    else:
        return False

#use pwd backend to get uid from linux username
def get_current_user_id(user):
    return pwd.getpwnam(user.username).pw_uid if user else 0

## Generic 404 view
def response_404(message=""):
    return HttpResponseNotFound("<h2>Page not available</h2>{}".format(message))

## Index page
@login_required()
def index_view(request):
    data = pyslurm.job().get()
    jobs = list(data.values())
    table = QueueTable(jobs, user_logged_in=get_current_user_id(request.user))

    table.order_by = '-submit_time'

    stats = {}
    nodes = pyslurm.node().get()
    stats["cpus_util"] = nodes["gpu-server"]["alloc_cpus"]  #FIXME
    stats["cpus_total"] = nodes["gpu-server"]["cpus"]  #FIXME
    stats["ram_util"] = nodes["gpu-server"]["alloc_mem"]  #FIXME
    stats["ram_total"] = nodes["gpu-server"]["real_memory"]  #FIXME
    stats["gpus_util"] = nodes["gpu-server"]["gres_used"]  #FIXME
    stats["gpus_total"] = nodes["gpu-server"]["gres"]  #FIXME

    return render(request, 'job_submission/job_queue.html', {'table': table, 'stats': stats})

##  Job details view
@login_required()
def job_details_view(request, id):
    job_data = get_job(id)

    if job_data:
        # check if the correct user is looking at this..
        if not job_data['user_id'] == get_current_user_id(request.user):
            return response_404('You have no permission to view this job')

        job_out = {'std_out' : '', 'std_out_available' : False}
        # get std out content
        if os.path.isfile(job_data['std_out']):
            with open(job_data['std_out'], 'r') as content_file:
                job_out['std_out'] = content_file.read()
                job_out['std_out_available'] = True
        else:
            job_out['std_out'] = "Log file currently not available"

        file_list = create_sub_file_list(os.path.split(job_data['command'])[0]) #take the same path as the command script
        table = JobFilesTable(file_list)

        return render(request, 'job_submission/job_details.html', {'job_data' : job_data,
                                                                   'job_data_items' : job_data.items(),
                                                                   'job_out' : job_out,
                                                                   'job_id': id,
                                                                   'files_table': table} )
    else:
        return response_404()

##  Job download std out page
@login_required()
def job_download_std_out_view(request, id):
    job_data = get_job(id)
    if job_data:
        if not job_data['user_id'] == get_current_user_id(request.user):
            return response_404('You have no permission to view this job')

        if not os.path.isfile(job_data['std_out']):
            return response_404()
        with open(job_data['std_out'], 'r') as content_file:
            response = HttpResponse(content_file, content_type='text/plain')
            response['Content-Disposition'] = 'attachment; filename=std_out.txt'
            return response
        return response_404()
    return response_404()


##  Job creation page
@login_required()
def job_create_view(request):
    # process form ...
    if request.method == "POST":
        form = JobCreationForm(request.POST, request.FILES)
        if form.is_valid():
            #get data
            post_data = request.POST.copy()
            temp_path = handle_upload_file(request.FILES['project_files'])

            #save data as session
            request.session['create_temp_path'] = temp_path
            request.session['create_post_data'] = request.POST

            redirect =  HttpResponseRedirect("create_job_entry")
            return redirect
    else:
        form = JobCreationForm()

    #get all available docker contrainers
    client = docker.from_env()
    images = client.images.list()
    tags = [{'id'      : x.id[7:],
             'tags'    : x.tags,
             'comment' : x.attrs['Comment'] } \
            for x in images]

    table = DockerImagesTable(tags)
    table.paginate(page=request.GET.get('page', 1), per_page=25)

    return render(request, 'job_submission/job_creation_form.html', {'form': form, 'available_images': table})

## Job entry file selection
@login_required()
def job_create_select_entrypoint_view(request):
    if request.method == "POST":
        form = JobCreationEntrySelectionForm(request.POST)
        if form.is_valid():
            original_post = request.session["create_post_data"]
            gpu_count = 1 if "gpu_requirements" in original_post else 0
            if request.user.is_authenticated:
                user_id = get_current_user_id(request.user)
                user_email = request.user.email

                submit_job(cpus=original_post['cpu_requirements'],
                           ram=original_post['ram_requirements'],
                           gpus=gpu_count,
                           job_name=original_post['title'],
                           comment=request.POST['comments'],
                           uid=user_id,
                           user_email=user_email,
                           docker_image=original_post['environment_image'],
                           temp_path=request.session["create_temp_path"],
                           entry_point=request.POST['entry_path'])
            else:
                return response_404()
            return HttpResponseRedirect("create_job_done")
    else:
        form = JobCreationEntrySelectionForm()

    file_list = create_sub_file_list(request.session["create_temp_path"])
    table = SelectFileTable(file_list)
    return render(request, 'job_submission/job_creation_entry_selection.html', {'form':form, 'entry_files':table})

## Jobs successfully queued
@login_required()
def job_create_done_view(request):
    return render(request, 'job_submission/job_submitted.html')

## Job deletion form and view
@login_required()
def job_remove_view(request):
    if request.method == "POST":
        form = JobRemoveForm(request.POST)
        if form.is_valid():
            #Remove job#TODO! #FIXME
            return HttpResponseRedirect("/queue")
    else:
        form = JobRemoveForm()

    return render(request, 'job_submission/job_remove.html', {'form': form})

@login_required()
def job_details_download_file(request, id, file_id):
    job_data = get_job(id)

    if job_data:
        if not job_data['user_id'] == get_current_user_id(request.user):
            return response_404('You have no permission to view this job')

        file_list = create_sub_file_list(os.path.split(job_data['command'])[0])
        fullpath = ""

        #get matching file id item using a generator
        found_file = next(item for item in file_list if item['file_table_id'] == file_id)
        if found_file:
            fullpath = os.path.join(os.path.split(job_data['command'])[0], found_file['file_table_file'])
        else:
            return response_404("File not found")

        if not os.path.isfile(fullpath):
            return response_404("File not found")

        with open(fullpath, 'rb') as content_file:
            response = HttpResponse(content_file, content_type='application/octet-stream')
            response['Content-Disposition'] = 'attachment; filename={}'.format(os.path.split(fullpath)[1])
            return response

    else:
        return response_404("No job found for this id")

def job_details_download_all_files(request, id):
    job_data = get_job(id)

    if job_data:
        if not job_data['user_id'] == get_current_user_id(request.user):
            return response_404('You have no permission to view this job')

        path = os.path.split(job_data['command'])[0]
        stream = compress_folder_into_zip(path) #package all files into a zip image

        response = HttpResponse(stream.getvalue(), content_type='application/octet-stream')
        response['Content-Disposition'] = 'attachment; filename=job.zip'
        return response

    else:
        return response_404("No job found for this id")


## Login views
def login_view(request):
    username = request.POST['username']
    password = request.POST['password']

    if authenticate(username=username, password=password):
        #success
        login(request, user)
        return HttpResponseRedirect('/queue')
    else:
        #failed
        return render(request, 'job_submission/login.html')

## Logout view
def logout_view(request):
    logout(request)
    return render(request, 'job_submission/logout.html')



################### Helper
# create a list of dicts with all files
def create_sub_file_list(path):
    file_list = []
    file_id = 0
    for root, dirs, files in os.walk(path):
        file_list.append({'file_table_file':os.path.relpath(root, path), 'file_table_type':'root_path', 'file_table_id': -1})
        for file in files:
            file_list.append({'file_table_file':os.path.relpath(os.path.join(root, file), path), 'file_table_type':'file', 'file_table_id': file_id})
            file_id += 1

    return file_list


#### TESTS ...

##  Job creation page Test...
@login_required()
def job_create_view_test(request):
    # process form ...
    if request.method == "POST":
        form = JobCreationForm(request.POST, request.FILES)
        if form.is_valid():
            #get data
            post_data = request.POST.copy()
            temp_path = handle_upload_file(request.FILES['project_files'])

            #save data as session
            request.session['create_temp_path'] = temp_path
            request.session['create_post_data'] = request.POST

            redirect =  HttpResponseRedirect("create_job_entry")
            return redirect
    else:
        form = JobCreationForm()

    #get all available docker contrainers
    containers = get_all_container('/home/test/singularity-images/output')
    container_features = [get_container_details(x) for x in containers]

    tags = [{'id'       : container['image.filename'],
             'name'     : container['image.filename'],
             'features' : container['Features'],  #Fixme?
             'based_on' : container['org.label-schema.usage.singularity.deffile.from'] } \
            for container in container_features]

    table = SingularityImagesTable(tags)
    table.paginate(page=request.GET.get('page', 1), per_page=25)

    return render(request, 'job_submission/job_creation_form.html', {'form': form, 'available_images': table})
