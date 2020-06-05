from django.db.models import signals
from functools import partial
from user.models import AuditedModel


def add_audit_fields(request, sender, instance=None, **kwargs):
    """
    Update the fields created_by and updated_by

    expected to be called in pre_save so instance save fields itself
    """
    if issubclass(sender, AuditedModel):
        if not instance.id:
            instance.created_by = request.user
        instance.modified_by = request.user


class AuditingMiddleWare:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        signals.pre_save.connect(partial(add_audit_fields, request), dispatch_uid=(self.__class__, request), weak=False)
        try:
            response = self.get_response(request)
        finally:
            signals.pre_save.disconnect(dispatch_uid=(self.__class__, request))

        return response
