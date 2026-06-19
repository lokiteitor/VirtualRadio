"""Generation job routes."""
from __future__ import annotations

from flask import Blueprint

from app.auth.permissions import check_permission
from app.common.responses import success
from app.controllers import job as ctrl

bp = Blueprint("jobs", __name__)


@bp.get("/jobs/<job_id>")
@check_permission("job", "read")
def get_job(job_id):
    return success(ctrl.get_job(job_id))


@bp.get("/jobs/<job_id>/traces")
@check_permission("job", "read")
def get_job_traces(job_id):
    return success(ctrl.get_job_traces(job_id))
