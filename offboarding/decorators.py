"""
offboarding/decorators.py

This module is used to write custom authentication decorators for offboarding module
"""
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from horilla.decorators import decorator_with_arguments
from offboarding.models import Offboarding, OffboardingStage, OffboardingTask


@decorator_with_arguments
def any_manager_can_enter(function, perm, offboarding_employee_can_enter=False):
    def _function(request, *args, **kwargs):
        employee = request.user.employee_get
        if (
            request.user.has_perm(perm)
            or offboarding_employee_can_enter
            or (
                Offboarding.objects.filter(managers=employee).exists()
                | OffboardingStage.objects.filter(managers=employee).exists()
                | OffboardingTask.objects.filter(managers=employee).exists()
            )
        ):
            return function(request, *args, **kwargs)
        else:
            messages.info(request, "You dont have permission.")
            return HttpResponse("<script>window.location.reload()</script>")

    return _function


@decorator_with_arguments
def offboarding_manager_can_enter(function, perm):
    def _function(request, *args, **kwargs):
        employee = request.user.has_perm(perm)
        if (
            request.user.has_perm(perm)
            or Offboarding.objects.filter(managers=employee).exists()
        ):
            return function(request, *args, **kwargs)
        else:
            messages.info(request, "You dont have permission.")
            return HttpResponse("<script>window.location.reload()</script>")

    return _function


@decorator_with_arguments
def offboarding_or_stage_manager_can_enter(function, perm):
    def _function(request, *args, **kwargs):
        employee = request.user.has_perm(perm)
        if (
            request.user.has_perm(perm)
            or Offboarding.objects.filter(managers=employee).exists()
            or OffboardingStage.objects.filter(managers=employee).exists()
        ):
            return function(request, *args, **kwargs)
        else:
            messages.info(request, "You dont have permission.")
            return HttpResponse("<script>window.location.reload()</script>")

    return _function