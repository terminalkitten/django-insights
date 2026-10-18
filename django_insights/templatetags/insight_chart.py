from django import template
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import SafeString

from django_insights.charts import render_bucket, to_base64img
from django_insights.models import Bucket
from django_insights.settings import settings

register = template.Library()


@register.simple_tag
def chart(bucket: Bucket) -> SafeString:
    return format_html(
        '<img loading="lazy" class="h-auto w-full" src="{}" alt="{}" />',
        reverse("insights:insight_chart", args=[bucket.pk]),
        bucket.question,
    )


def base64img(bucket: Bucket, override_theme: str | None = None) -> str:
    theme = override_theme or settings.INSIGHTS_DEFAULT_THEME
    return to_base64img(render_bucket(bucket, theme))


@register.simple_tag
def pdf_chart(bucket: Bucket) -> SafeString:
    img_data = base64img(bucket, override_theme="light")

    return format_html('<img class="chart" src="data:image/png;base64,{}" />', img_data)
