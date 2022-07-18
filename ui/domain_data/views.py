from django.shortcuts import render

from django.template import loader

from .models import DomainActions, DomainActionsFilter


def index(request):
    f = DomainActionsFilter(request.GET, queryset=DomainActions.objects.order_by('-last_time_seen'))

    return render(request, 'index.html', {'filter': f})