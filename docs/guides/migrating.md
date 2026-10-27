---
title: Upgrading from 0.2
description: What changed in django-insights 0.3, and the four steps to upgrade from 0.2.x.
sidebar:
  order: 7
---

Version 0.3 is a big update, but your insights keep working. Most projects need the four steps below and take about ten minutes. Your collected data is kept.

## What changed

| Area         | What changed                                                                | Do you need to act?            |
| ------------ | --------------------------------------------------------------------------- | ------------------------------ |
| Requirements | Python 3.11 to 3.14, Django 5.2, 6.0 or 6.1                                 | Yes, if you are older          |
| Settings     | Three renamed, the chart colors replaced by `INSIGHTS_THEME`                | Yes                            |
| Database     | Two migrations for the `insights` database                                  | Yes, one command               |
| Collecting   | One transaction, a failing insight now makes the command exit with an error | Check your cron or CI          |
| Permissions  | A permission class without `has_permission` now denies access               | Check your classes             |
| PDF export   | Removed, with all its dependencies                                          | Yes, if you used it            |
| Dashboard    | New design with Basecoat UI, light and dark                                 | Only if you override templates |
| New          | Trends, themes with 24 shadcn colors, 8 styles, system checks               | No, optional                   |

## Upgrade in four steps

:::steps
1. **Upgrade the package.** You need Python 3.11 to 3.14 and Django 5.2, 6.0 or 6.1 (Django 6 needs Python 3.12+).

   ```bash
   pip install -U django-insights
   ```

2. **Rename your settings.** The old names are ignored, `manage.py check` warns while they are still set.

   | Old                                                                       | New                                         |
   | ------------------------------------------------------------------------- | ------------------------------------------- |
   | `INSIGHT_CHARTS_USE_MEDIA_CACHE`                                          | `INSIGHTS_CHARTS_USE_MEDIA_CACHE`           |
   | `INSIGHT_MEDIA_CACHE_ROOT`                                                | `INSIGHTS_MEDIA_CACHE_ROOT`                 |
   | `INSIGHT_DASHBOARD_PERMISSIONS`                                           | `INSIGHTS_DASHBOARD_PERMISSIONS`            |
   | `INSIGHTS_CHART_LIGHT_PRIMARY_COLOR`, `INSIGHTS_CHART_DARK_PRIMARY_COLOR` | `INSIGHTS_THEME`, see [Theming](theming.md) |

   ```python
   INSIGHTS_THEME = "blue"  # a shadcn theme name, or {"accent": "#ec4899"}
   ```

   `INSIGHTS_APP_NAME`, `INSIGHTS_CHART_DPI` and `INSIGHTS_DEFAULT_THEME` are unchanged.

3. **Migrate the insights database.** Two migrations, your data is kept.

   ```bash
   python manage.py migrate insights --database=insights
   ```

4. **Collect once and check.**

   ```bash
   python manage.py collect_insights   # exit code 0
   python manage.py check              # no insights warnings
   ```
:::

That is it for most projects. Read on for the changes that can affect you.

## Things to check

:::caution[Permissions now fail closed]
A class in `INSIGHTS_DASHBOARD_PERMISSIONS` without a `has_permission(request)` method used to be skipped, which granted access. It now raises `ImproperlyConfigured` and the dashboard denies access. Check that every class you list has the method and returns `True` for the people who should get in.
:::

:::caution[Cron jobs and CI see failures]
`collect_insights` now runs in one transaction. When an insight raises, it is logged and reported, the others still run, and the command exits with an error such as `3 of 14 insights failed`. A monitor that watches the exit code will start to report them.
:::

:::caution[PDF export is removed]
Nothing replaces it. Remove links to `insights:insight_pdf` and `insights:insight_pdf_test`, and the `[pdf]` extra from your requirements. `weasyprint`, `django-weasyprint` and PyMuPDF are no longer used, and no system libraries (Pango and friends) are needed.
:::

:::note[Old dashboard bookmarks]
Dashboard URLs use a stable id per app, derived from the module path. Bookmarks of `/app/<uuid>/` from 0.2 stop working once, collect again and use the new links.
:::

## What is new

- **Trends** on counters and gauges: a small line and the change against the previous period, see [Trend](metrics/trend.md).
- **Themes**: pick a Basecoat style and shadcn colors, shared by the dashboard and the charts, see [Theming](theming.md).
- **System checks**: `manage.py check` warns about a missing insights database, a wrong setting and more, see [System checks](../reference/checks.md).
- **Stable collecting**: one transaction, per-insight errors, no output when it is not a terminal.
- **A pytest plugin** that loads by itself, see [Testing insights](testing.md).

## More details

:::details[Settings behavior]
- Settings are read when they are used, so `override_settings` works. Unknown names raise `AttributeError`.
- `INSIGHTS_CHARTS_USE_MEDIA_CACHE = True` requires `INSIGHTS_MEDIA_CACHE_ROOT` (`insights.W003`).
- System checks are warnings only (`insights.W001` to `W012`), they never stop the project from starting. `django_insights.database.check_settings()` is removed, run `manage.py check`.
:::

:::details[The database migrations]
- `0002`: labels are unique per app (two apps can both have `count_users`), `Counter.value` is a big integer, explicit ordering. The unused histogram type, the `ExecutionDelta` model and `Gauge.gauge()` are removed.
- `0003`: a `trend` column for counters and gauges.

The insights database is a cache of your data, so you can also delete it, migrate it again and run `collect_insights`.
:::

:::details[Collecting from code]
- `metrics.collect()` returns the list of failures. It raises `InsightsError` (from `django_insights.exceptions`) when an insight saves duplicates, it no longer prints and calls `exit()`.
- The progress bar is hidden when the output is not a terminal.
- The chart cache only deletes cached `*-*-*.png` files, it no longer wipes the whole media cache root.
:::

:::details[Templates and static files]
Only needed if you override templates or use the template tags yourself.

- The dashboard is rebuilt with Basecoat UI. The templates under `insights/` have a new structure (`base.html`, `dashboard.html`, `app.html`, `_bucket.html`, `_stat.html`, `_empty.html`). If you override any, start from the new ones, see [Customizing](customizing.md).
- `{% chart bucket %}` no longer takes an `overlay` argument. `{% pdf_chart %}` and `pdf_available` are removed, and so are the `insights/pdf.html` and `pdf.css` overrides.
- Stylesheets are compiled per Basecoat style, icons are CSS classes and the Geist font is served from the package. Nothing is loaded from a CDN. Run `collectstatic` as usual.
- The chart font is Geist (was Ubuntu). The library no longer changes matplotlib's global configuration.
:::

:::details[Using the library in code]
- The `insights` console script is removed (it never worked).
- `bar` and `hbar` charts no longer crash when a category is `None`.
- Only the names in `__all__` of `django_insights.metrics` and `django_insights.metrics_types` are public.
:::

:::details[Testing with the pytest plugin]
- The plugin loads through the `pytest11` entry point, you do not need to register it.
- The module-level `registry`, `register_insights_modules` and the injected fixture are removed. If you imported them from `django_insights.pytest`, use the `insights_query` fixture instead.
- Errors inside an `insights.py` are no longer swallowed. The `insights` marker is registered, so `--strict-markers` works.
:::

:::details[Building from source]
Only for contributors.

- `uv build` replaces flit. The version comes from the latest git tag (setuptools-scm).
- `pnpm install && pnpm build` in `django_insights/packages` rebuilds the dashboard CSS.
- ruff replaces black, isort and flake8, and tox runs through uv. Releases are made by pushing a tag.
:::
