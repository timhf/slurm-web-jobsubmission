from django import forms

class JobCreationForm(forms.Form):
    title = forms.CharField(max_length = 255, label="Job title")
    cpu_requirements = forms.DecimalField(max_value=16, min_value=0, label="No of CPUs required", initial=1)
    ram_requirements = forms.DecimalField(max_value=8192, min_value=0, label="Amount of RAM required (MB)", initial=2048)
    gpu_requirements = forms.BooleanField(label="Is a GPU required", required=False)
    project_files = forms.FileField(label="Project files (zip)")

    def clean_project_files(self):
        data = self.cleaned_data['project_files']
        #FIXME: Check actual file type not just the extension
        if not data.name.split('.')[1] == "zip":
            raise forms.ValidationError("Please submit only zip files. For now we only check the extension, not the actual filetype. Consider renaming. ")


class JobCreationEntrySelectionForm(forms.Form):
    comments = forms.CharField(widget=forms.Textarea(attrs={'rows': 4, 'cols':70}))

class JobRemoveForm(forms.Form):
    pass
