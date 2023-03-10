from django import template
from django.utils.safestring import mark_safe

from django_insights.charts import barchart, scatterplot, timeseries
from django_insights.models import Bucket

register = template.Library()


@register.simple_tag
def bar_chart(bucket: Bucket, theme: str = "light"):  # Rename
    img = barchart(bucket=bucket, theme=theme)

    return mark_safe(
        f"""
        <img
            class="w-full h-auto border-gray-200 border-t-1"
            src="data:image/png;base64,{img}"
            alt="{bucket.question}"
        />
    """
    )


@register.simple_tag
def timeseries_chart(bucket: Bucket, theme: str = "light"):
    img = timeseries(bucket=bucket, theme=theme)

    return mark_safe(
        f"""
        <img
            class="w-full h-auto border-gray-200 border-t-1"
            src="data:image/png;base64,{img}"
            alt="{bucket.question}"
        />
    """
    )


@register.simple_tag
def scatterplot_chart(bucket: Bucket, theme: str = "light"):
    img = scatterplot(bucket=bucket, theme=theme)

    return mark_safe(
        f"""
        <img
            class="w-full h-auto border-gray-200 border-t-1"
            src="data:image/png;base64,{img}"
            alt="{bucket.question}"
        />
    """
    )
