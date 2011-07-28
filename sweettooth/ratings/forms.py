
import datetime

from django.forms import fields, widgets
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.comments.forms import CommentForm
from django.utils.encoding import StrAndUnicode, force_unicode
from django.utils.safestring import mark_safe

from ratings.models import RatingComment

CHOICES = zip(range(5), (str(r) for r in range(1, 6)))

class NoLabelRadioInput(widgets.RadioInput):
    """
    Like RadioInput, but with no label.
    """

    def __unicode__(self):
        return self.tag()

class NoSoapRadio(StrAndUnicode):
    """
    Like RadioSelectRenderer, but without lists.
    """

    def __init__(self, name, value, attrs, choices):
        self.name, self.value, self.attrs = name, value, attrs
        self.choices = choices

    def __iter__(self):
        for i, choice in enumerate(self.choices):
            yield NoLabelRadioInput(self.name, self.value, self.attrs.copy(), choice, i)

    def __getitem__(self, idx):
        choice = self.choices[idx] # Let the IndexError propogate
        return NoLabelRadioInput(self.name, self.value, self.attrs.copy(), choice, idx)

    def __unicode__(self):
        return self.render()

    def render(self):
        """Outputs a <ul> for this set of radio fields."""
        return mark_safe(u'\n'.join(force_unicode(w) for w in self))

class RatingCommentForm(CommentForm):
    rating = fields.IntegerField(min_value=0, max_value=4,
                                 widget=widgets.RadioSelect(choices=CHOICES,
                                                            renderer=NoSoapRadio,
                                                            attrs={"class": "rating"}))

    def get_comment_model(self):
        return RatingComment

    def get_comment_create_data(self):
        return dict(
            content_type = ContentType.objects.get_for_model(self.target_object),
            object_pk    = force_unicode(self.target_object._get_pk_val()),
            user_name    = self.cleaned_data["name"],
            user_email   = self.cleaned_data["email"],
            comment      = self.cleaned_data["comment"],
            rating       = self.cleaned_data["rating"],
            submit_date  = datetime.datetime.now(),
            site_id      = settings.SITE_ID,
            is_public    = True,
            is_removed   = False,
        )

# Remove the URL field, we don't want it.
RatingCommentForm.base_fields.pop('url')
