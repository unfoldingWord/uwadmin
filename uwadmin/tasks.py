from __future__ import absolute_import

import subprocess
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from celery import task
from .models import PublishRequest, OpenBibleStory
from django.utils.datetime_safe import datetime


@task()
def publish(langcode):
    subprocess.call(["/var/www/vhosts/door43.org/tools/uw/publish.sh", "-l", langcode])


@task()
def send_request_email(request_id):
    pr = PublishRequest.objects.get(pk=request_id)
    html_contents = render_to_string("./uwadmin/email_html_publishrequest.html", {"publish_request": pr})
    plain_contents = render_to_string("./uwadmin/email_plain_publishrequest.html", {"publish_request": pr})
    send_mail("Publish Request #{0}".format(str(pr.pk)),
              plain_contents,
              settings.EMAIL_FROM,
              settings.EMAIL_NOTIFY_LIST,
              html_message=html_contents)


def _compute_version(source_version):
    parts = source_version.split(".")
    if len(parts) == 3:
        return ".".join([parts[0], str(int(parts[1]) + 1), parts[2]])
    else:
        return "invalid"


def approve_publish_request(request_id, user_id):
    pr = PublishRequest.objects.get(pk=request_id)
    obs = OpenBibleStory()
    obs.created_by_id = user_id
    obs.language = pr.language
    obs.checking_level = pr.checking_level
    obs.source_text = pr.source_text
    obs.source_version = pr.source_version
    obs.version = _compute_version(pr.source_version)
    obs.notes = "requestor: " + pr.requestor
    obs.date_started = pr.created_at.date()
    obs.save()
    pr.approved_at = datetime.now()
    pr.save()
    return obs.pk
