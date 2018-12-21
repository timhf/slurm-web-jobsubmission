from django_tables2 import tables, RequestConfig, columns
from django_tables2.utils import A
from django.utils.safestring import mark_safe
from django.utils.html import format_html
from django.urls import reverse
import django_tables2 as dt
from file_table.file_table import FileTable
from datetime import datetime
import os
import pwd
import itertools


class DockerImagesTable(dt.Table):
    id = columns.Column()
    tags = dt.Column()
    comment = dt.Column()

    def render_id(self, value):
        return format_html('<input type="radio" name="environment_image" value="{0}" required id="id_environment_image_0">', value)

class SingularityImagesTable(dt.Table):
    id = dt.Column(verbose_name=" ")
    name = dt.Column()
    features = dt.Column()
    based_on = dt.Column()

    def render_id(self, value):
        return format_html('<input type="radio" name="environment_image" value="{0}" required id="id_environment_image_0">', value)

class SelectFileTable(FileTable):
    selection = columns.Column(verbose_name="Selection", empty_values=())

    def render_selection(self, value, record):
        return format_html('<input type="radio" name="entry_path" value="{0}" required id="id_entry_path">', record['file_table_file'])

class JobFilesTable(FileTable):
    actions = dt.Column(empty_values=())

    def render_actions(self, value, record):
        if record['file_table_type'] == "file":
            file_id = record['file_table_id']
            return format_html('<a href="download_file/{0}">Download</a>', file_id)
        else:
            return ""

class QueueTable(dt.Table):
    class Meta:
        template_name = 'django_tables2/bootstrap-responsive.html'

    def __init__(self, *args, **kwargs):
        self.login_user = kwargs.pop('user_logged_in')
        super(QueueTable, self).__init__(*args, **kwargs)

    def render_user_id(self, value):
        return pwd.getpwuid(int(value)).pw_name

    def render_submit_time(self, value):
        return datetime.utcfromtimestamp(value).strftime('%Y-%m-%d %H:%M:%S')

    def render_job_state(self, value):
        color = "black"
        if value == "RUNNING":
            color = "green"
        if value == "PENDING":
            color = "gray"
        if value == "COMPLETED":
            color = "blue"
        if value == "FAILED":
            color = "red"

        return mark_safe('<span style="color: %s"> %s </span>' % (color, value))

    def render_actions(self, value, record):
        if record['user_id'] == self.login_user:
            href_details = reverse('details_job', args=[record['job_id']])
            href_remove = reverse('remove_job', args=[record['job_id']])
            return mark_safe('<a href="{}">Details</a> <a href={}>Remove</a>'.format(href_details, href_remove))
        else:
            return "--"

    login_user = 0

    job_id = dt.Column()
    job_state = dt.Column()
    account = dt.Column(verbose_name='Group')
    user_id = dt.Column(verbose_name='User')
    submit_time = dt.Column()
    actions = dt.Column(empty_values=())
