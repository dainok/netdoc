"""Run discovery.

Usage:
/opt/netbox/venv/bin/python3 /opt/netbox/netbox/manage.py shell < run_discovery.py
"""
import uuid

from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User

from extras.scripts import get_scripts, run_script
from extras.models import JobResult, Script
from utilities.utils import NetBoxFakeRequest

from netdoc.models import Discoverable

FILTERS = ["172.25.82.50"]


def main():
    """Main function."""
    data = {
        "discoverables": Discoverable.objects.filter(address__in=FILTERS)
        if FILTERS
        else [],
    }
    user = User.objects.filter(is_superuser=True).order_by("pk")[0]
    script = get_scripts().get("NetDoc").get("Discover")
    request = NetBoxFakeRequest(
        {
            "META": {},
            "POST": data,
            "GET": {},
            "FILES": {},
            "user": user,
            "id": uuid.uuid4(),
        }
    )

    JobResult.enqueue_job(
        run_script,
        name=script.full_name,
        obj_type=ContentType.objects.get_for_model(Script),
        user=request.user,  # pylint: disable=no-member
        schedule_at=None,
        interval=None,
        job_timeout=script.job_timeout,
        data=request.POST,  # pylint: disable=no-member
        request=request,
    )


if __name__ == "django.core.management.commands.shell":
    main()
