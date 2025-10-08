from django import forms
from .models import EmployeeVaultFile

class VaultFileForm(forms.ModelForm):
    class Meta:
        model = EmployeeVaultFile
        fields = ["title", "description", "file", "shared_with", "is_public"]
        widgets = {
            "shared_with": forms.CheckboxSelectMultiple,
        }
