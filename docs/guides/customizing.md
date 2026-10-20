---
title: Customizing
description: Change where the dashboard lives, override its templates and reuse its template tags.
sidebar:
  order: 6
---

## The URLs

Include the URLs under any path. The namespace must be `insights`:

```python
(path("stats/", include("django_insights.urls", namespace="insights")),)
```

These names are available for `reverse()` and `{% url %}`:

| Name                         | Path           | Shows                           |
| ---------------------------- | -------------- | ------------------------------- |
| `insights:insight_dashboard` | `/`            | counters and gauges of all apps |
| `insights:insight_app`       | `app/<uuid>/`  | the charts of one app           |
| `insights:insight_chart`     | `charts/<id>/` | the PNG of one chart            |

The chart responses carry an `ETag` and are private, so a browser only loads a chart again when it changed. The mode comes from a `theme` cookie that the dashboard sets, `INSIGHTS_DEFAULT_THEME` otherwise.

## Templates

Override a template by adding one with the same name to a templates folder of your project that comes before the app, for example `templates/insights/dashboard.html` with `DIRS: [BASE_DIR / "templates"]`.

| Template                  | Used for                                      |
| ------------------------- | --------------------------------------------- |
| `insights/base.html`      | the page: sidebar, header, theme switch       |
| `insights/dashboard.html` | the dashboard, fills the `content` block      |
| `insights/app.html`       | the page of an app, fills the `content` block |
| `insights/_stat.html`     | one counter or gauge                          |
| `insights/_bucket.html`   | one chart with its data                       |
| `insights/_empty.html`    | the page when nothing is collected yet        |

A small dashboard of your own:

```django
{% extends "insights/base.html" %}
{% load insight_stat %}
{% block content %}
  {% for counter in counter_list %}
    <p>{{ counter.label }}: {{ counter.value }} {{ counter.trend|sparkline }}</p>
  {% endfor %}
{% endblock content %}
```

## Template tags

Use them in your own pages too:

| Tag                                       | Does                                                              |
| ----------------------------------------- | ----------------------------------------------------------------- |
| `{% chart bucket %}` from `insight_chart` | an `<img>` of the chart of a bucket, loaded lazily                |
| `values\|sparkline` from `insight_stat`   | an inline SVG line of a trend, nothing with fewer than two values |
| `values\|trend` from `insight_stat`       | the percentage change of the last value against the one before it |

```django
{% load insight_chart %}
{% chart bucket %}
```

The `chart` tag needs the URLs above, and a user who may see the dashboard.

## Static files

The stylesheet of the chosen style, the scripts and the Geist font live in the package under `insights/`. Run `collectstatic` for production, and serve the files like the rest of your static files.
