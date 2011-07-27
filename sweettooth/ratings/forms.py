
from django import forms
from django.forms import widgets
from django.contrib.comments.forms import CommentForm
from django.utils.safestring import mark_safe
from ratings.models import RatingComment

class RatingCommentForm(CommentForm):
    title = forms.IntegerField(min_value=0, max_value=10, widget=RatingWidget)

    def get_comment_model(self):
        return RatingComment

    def get_comment_create_data(self):
        data = super(RatingCommentForm, self).get_comment_create_data()
        data['rating'] = self.cleaned_data['rating']
        return data
