"""Default settings for the ``core`` app of the Marsha project."""
from django.utils.translation import gettext_lazy as _


PENDING, PROCESSING, ERROR, READY, LIVE, IDLE, STARTING, STOPPED = (
    "pending",
    "processing",
    "error",
    "ready",
    "live",
    "idle",
    "starting",
    "stopped",
)
STATE_CHOICES = (
    (PENDING, _("pending")),
    (PROCESSING, _("processing")),
    (ERROR, _("error")),
    (READY, _("ready")),
    (LIVE, _("live")),
)

LIVE_CHOICES = (
    (IDLE, _("idle")),
    (STARTING, _("starting")),
    (LIVE, _("live")),
    (STOPPED, _("stopped")),
)
