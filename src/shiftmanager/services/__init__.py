"""Services: rules spanning repositories. Never imports tkinter."""

from shiftmanager.services import report_service, scheduling_service
from shiftmanager.services.scheduling_service import ConflictError

__all__ = ["ConflictError", "report_service", "scheduling_service"]
