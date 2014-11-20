from __future__ import absolute_import, division, generators, nested_scopes, print_function, unicode_literals, with_statement

from django import forms


class NewImageForm(forms.Form):
    git_url             = forms.URLField()
    git_commit          = forms.CharField(required=False)
    git_dockerfile_path = forms.CharField(required=False)
    tag                 = forms.CharField()
    parent_registry     = forms.CharField(required=False)
    target_registries   = forms.MultipleChoiceField(required=False)
    repos               = forms.MultipleChoiceField(required=False)


class MoveImageForm(forms.Form):
    source_registry     = forms.CharField()
    target_registry     = forms.CharField()
    tags                = forms.MultipleChoiceField()

