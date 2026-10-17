from django import template
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from django_insights.charts import (
    barchart,
    hbarchart,
    scatterplot,
    timeseries,
    to_base64img,
)
from django_insights.models import Bucket
from django_insights.settings import settings

register = template.Library()


@register.simple_tag
def chart(bucket: Bucket, overlay: str | None = None):
    img_url = reverse("insights:insight_chart", args=[bucket.pk])

    overlay_attr = (
        format_html('data-dialog-open="#insights-modal-{}"', overlay) if overlay else ""
    )

    return format_html(
        """
        <img
            {}
            class="w-full h-auto border-gray-200 cursor-pointer border-t-1"
            src="{}"
            alt="{}"
        />
    """,
        overlay_attr,
        img_url,
        bucket.question,
    )


def base64img(bucket: Bucket, override_theme=None):
    theme = override_theme or settings.INSIGHTS_DEFAULT_THEME
    fig = None
    if bucket.is_timeseries:
        fig = timeseries(bucket, theme=theme)
    if bucket.is_scatterplot:
        fig = scatterplot(bucket, theme=theme)
    if bucket.is_barchart:
        fig = barchart(bucket, theme=theme)
    if bucket.is_hbarchart:
        fig = hbarchart(bucket, theme=theme)

    if fig is None:
        raise ValueError(f"Unsupported bucket type: {bucket.type}")

    return to_base64img(fig)


@register.simple_tag
def pdf_chart(bucket_id: int):
    bucket = Bucket.objects.get(pk=bucket_id)
    img_data = base64img(bucket, override_theme="light")

    return mark_safe(
        f"""
        <img
            class="chart"
            src="data:image/png;base64,{img_data}"
        />
    """
    )
