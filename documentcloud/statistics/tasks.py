# Django
from celery.exceptions import SoftTimeLimitExceeded
from celery.schedules import crontab
from celery.task import periodic_task
from django.core.management import call_command
from django.db.models import Sum
from django.db.models.functions import Coalesce

# Standard Library
import logging
from datetime import date, timedelta

# DocumentCloud
from documentcloud.documents.choices import Access, Status
from documentcloud.documents.models import Document, Note
from documentcloud.projects.models import Project
from documentcloud.statistics.models import Statistics

logger = logging.getLogger(__name__)

# This is using UTC time instead of the local timezone
@periodic_task(run_every=crontab(hour=5, minute=30))
def store_statistics():
    """Store the daily statistics"""
    # pylint: disable=too-many-statements

    yesterday = date.today() - timedelta(1)

    kwargs = {}
    kwargs["date"] = yesterday

    kwargs["total_documents"] = Document.objects.count()
    kwargs["total_documents_public"] = Document.objects.filter(
        access=Access.public
    ).count()
    kwargs["total_documents_organization"] = Document.objects.filter(
        access=Access.organization
    ).count()
    kwargs["total_documents_private"] = Document.objects.filter(
        access=Access.private
    ).count()
    kwargs["total_documents_invisible"] = Document.objects.filter(
        access=Access.invisible
    ).count()
    kwargs["total_documents_success"] = Document.objects.filter(
        status=Status.success
    ).count()
    kwargs["total_documents_readable"] = Document.objects.filter(
        status=Status.readable
    ).count()
    kwargs["total_documents_pending"] = Document.objects.filter(
        status=Status.pending
    ).count()
    kwargs["total_documents_error"] = Document.objects.filter(
        status=Status.error
    ).count()
    kwargs["total_documents_nofile"] = Document.objects.filter(
        status=Status.nofile
    ).count()
    kwargs["total_documents_deleted"] = Document.objects.filter(
        status=Status.deleted
    ).count()

    kwargs["total_pages"] = Document.objects.aggregate(
        pages=Coalesce(Sum("page_count"), 0)
    )["pages"]
    kwargs["total_pages_public"] = Document.objects.filter(
        access=Access.public
    ).aggregate(pages=Coalesce(Sum("page_count"), 0))["pages"]
    kwargs["total_pages_organization"] = Document.objects.filter(
        access=Access.organization
    ).aggregate(pages=Coalesce(Sum("page_count"), 0))["pages"]
    kwargs["total_pages_private"] = Document.objects.filter(
        access=Access.private
    ).aggregate(pages=Coalesce(Sum("page_count"), 0))["pages"]
    kwargs["total_pages_invisible"] = Document.objects.filter(
        access=Access.invisible
    ).aggregate(pages=Coalesce(Sum("page_count"), 0))["pages"]

    kwargs["total_notes"] = Note.objects.count()
    kwargs["total_notes_public"] = Note.objects.filter(access=Access.public).count()
    kwargs["total_notes_organization"] = Note.objects.filter(
        access=Access.organization
    ).count()
    kwargs["total_notes_private"] = Note.objects.filter(access=Access.private).count()
    kwargs["total_notes_invisible"] = Note.objects.filter(
        access=Access.invisible
    ).count()
    kwargs["total_users_uploaded"] = (
        Document.objects.order_by().values("user_id").distinct().count()
    )
    kwargs["total_users_public_uploaded"] = (
        Document.objects.order_by()
        .filter(access=Access.public)
        .values("user_id")
        .distinct()
        .count()
    )
    kwargs["total_users_private_uploaded"] = (
        Document.objects.order_by()
        .filter(access=Access.private)
        .values("user_id")
        .distinct()
        .count()
    )
    kwargs["total_users_organization_uploaded"] = (
        Document.objects.order_by()
        .filter(access=Access.organization)
        .values("user_id")
        .distinct()
        .count()
    )
    kwargs["total_organizations_uploaded"] = (
        Document.objects.order_by().values("organization_id").distinct().count()
    )
    kwargs["total_organizations_public_uploaded"] = (
        Document.objects.order_by()
        .filter(access=Access.public)
        .values("organization_id")
        .distinct()
        .count()
    )
    kwargs["total_organizations_private_uploaded"] = (
        Document.objects.order_by()
        .filter(access=Access.private)
        .values("organization_id")
        .distinct()
        .count()
    )
    kwargs["total_organizations_organization_uploaded"] = (
        Document.objects.order_by()
        .filter(access=Access.organization)
        .values("organization_id")
        .distinct()
        .count()
    )

    kwargs["total_projects"] = Project.objects.count()

    Statistics.objects.create(**kwargs)


@periodic_task(
    run_every=crontab(hour=6, minute=0), time_limit=1800, soft_time_limit=1740
)
def db_cleanup():
    """Call some management commands to clean up the database"""
    logger.info("Starting DB Clean up")
    try:
        call_command("clearsessions", verbosity=2)
        call_command("deleterevisions", days=180, verbosity=2)
    except SoftTimeLimitExceeded:
        logger.error("DB Clean up took too long")
    logger.info("Ending DB Clean up")
