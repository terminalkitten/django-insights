from asgiref.sync import async_to_sync
from django import template
from django.urls import reverse
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
def chart(bucket: Bucket, overlay: str = None):
    img_url = reverse("insights:insight_chart", args=[bucket.pk])

    overlay_attr = ""
    if overlay:
        overlay_attr = f'data-hs-overlay="#hs-full-screen-modal-{overlay}"'

    return mark_safe(
        f"""
        <img
            {overlay_attr}
            class="w-full h-auto border-gray-200 cursor-pointer border-t-1"
            src="{img_url}"
            alt="{bucket.question}"
        />
    """
    )


@async_to_sync
async def base64img(bucket: Bucket, override_theme=None):
    theme = override_theme or settings.INSIGHTS_DEFAULT_THEME
    if bucket.is_timeseries:
        fig = await timeseries(bucket, theme=theme)
    if bucket.is_scatterplot:
        fig = await scatterplot(bucket, theme=theme)
    if bucket.is_barchart:
        fig = await barchart(bucket, theme=theme)
    if bucket.is_hbarchart:
        fig = await hbarchart(bucket, theme=theme)

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
