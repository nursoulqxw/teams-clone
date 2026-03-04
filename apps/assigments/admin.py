from django.contrib.admin import register,ModelAdmin

from .models import (
    Assigments,
    Assignment_Submissions
)


@register(Assigments)
class AssigmnetsAdmin(ModelAdmin):
    list_display = (
        'team_id',
        'title',
        'due_data',
        'max_points'
    )
    list_editable = ('max_points',)
    list_filter = ('team_id',)


@register(Assignment_Submissions)
class Assignment_SubmissionsAdmin(ModelAdmin):
    list_display = (
        'assigment_id',
        'status',
    )
    list_editable = ('status',)
    list_filter = ('status',)
