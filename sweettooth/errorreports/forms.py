
from django import forms

from errorreports.models import ErrorReport

class ErrorReportForm(forms.ModelForm):

    comment = forms.CharField(widget=forms.Textarea())
    can_contact = forms.BooleanField(label="I wish to provide the extension author with my email address", required=False)

    class Meta:
        model = ErrorReport
        fields = ('comment', 'can_contact')

    def clean_comment(self):
        return self.cleaned_data['comment'].strip()

    def clean_can_contact(self):
        return self.cleaned_data.get('can_contact', False)

    def save(self, request, extension, commit=True):
        report = super(ErrorReportForm, self).save(commit=False)
        report.user = request.user
        report.extension = extension
        if commit:
            report.save()
        return report

