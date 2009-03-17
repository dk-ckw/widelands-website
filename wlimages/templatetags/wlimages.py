#!/usr/bin/env python -tt
# encoding: utf-8
#
# File: wlimages/wlimages.py
#


# import re
from django import template
# from django.contrib.contenttypes.models import ContentType
# from wlimages.models import , FreeThreadedComment
from widelands.wlimages.forms import UploadImageForm

register = template.Library()

def do_get_upload_image_form(parser, token):
    """
    TODO
    """
    error_message = "%r tag must be of format {%% %r as CONTEXT_VARIABLE %%}" % (token.contents.split()[0], token.contents.split()[0])
    try:
        split = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, error_message
    if split[1] != 'as':
        raise template.TemplateSyntaxError, error_message
    if len(split) != 3:
        raise template.TemplateSyntaxError, error_message
    return UploadFormNode(split[2])

class UploadFormNode(template.Node):
    def __init__(self, context_name):
        self.context_name = context_name
    def render(self, context):
        form = UploadImageForm()
        context[self.context_name] = form
        return ''

register.tag('get_upload_form', do_get_upload_image_form)
