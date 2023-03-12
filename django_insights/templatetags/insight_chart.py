from django import template
from django.urls import reverse
from django.utils.safestring import mark_safe

from django_insights.models import Bucket

register = template.Library()


@register.simple_tag
def chart(bucket: Bucket):
    img_url = reverse("insights:insight_chart", args=[bucket.pk])
    return mark_safe(
        f"""
        <img
            class="w-full h-auto border-gray-200 border-t-1"
            src="{img_url}"
            alt="{bucket.question}"
        />
    """
    )
