from django import template
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import SafeString

from django_insights.models import Bucket

register = template.Library()


@register.simple_tag
def chart(bucket: Bucket) -> SafeString:
    return format_html(
        '<img loading="lazy" class="h-auto w-full" src="{}" alt="{}" />',
        reverse("insights:insight_chart", args=[bucket.pk]),
        bucket.question,
    )
