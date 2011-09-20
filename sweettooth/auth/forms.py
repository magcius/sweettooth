
from django.contrib.auth import forms, models

class PlainOutputForm(object):
    def as_plain(self):
        return self._html_output(
            normal_row = u'%(errors)s%(field)s%(help_text)s',
            error_row = u'%s',
            row_ender = u'',
            help_text_html = u'<br /><span class="helptext">%s</span>',
            errors_on_separate_row = False)

class AutoFocusForm(object):
    def __init__(self, *a, **kw):
        super(AutoFocusForm, self).__init__(*a, **kw)
        self.fields.value_for_index(0).widget.attrs['autofocus'] = True

class InlineForm(object):
    def __init__(self, *a, **kw):
        super(InlineForm, self).__init__(*a, **kw)
        for field in self.fields.itervalues():
            field.widget.attrs['placeholder'] = field.label

class InlineAuthenticationForm(PlainOutputForm, AutoFocusForm,
                               InlineForm, forms.AuthenticationForm):
    pass

class AuthenticationForm(AutoFocusForm, forms.AuthenticationForm):
    pass

class UserCreationEmailForm(forms.UserCreationForm):
    class Meta:
        model = models.User
        fields = 'username', 'email'

class UserCreationForm(AutoFocusForm, UserCreationEmailForm):
    pass
