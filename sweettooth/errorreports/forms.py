
from django import forms

from errorreports.models import ErrorReport

class ErrorReportForm(forms.ModelForm):

    comments = forms.CharField(widget=forms.Textarea())
    can_contact = forms.BooleanField(label="I wish to provide the extension author with my email address")

    class Meta:
        model = ErrorReport
        fields = ('comments', 'can_contact')

    def clean_comments(self):
        return self.cleaned_data['comments'].strip()

    def save(self, request, version, commit=True):
        report = super(ErrorReportForm, self).save(commit=False)
        report.user = request.user
        report.version = version
        if commit:
            report.save()
        return report

