# Migrating to django-insights 0.3 (v2)

A checklist for upgrading from 0.2.x. Work through it top to bottom, most projects need steps 1 to 5 only.

## 1. Requirements

- [ ] Python 3.11 to 3.14 (3.8 to 3.10 are dropped).
- [ ] Django 5.2, 6.0 or 6.1 (3.2 to 4.2 are dropped). Django 6 needs Python 3.12+.
- [ ] Browser with `<dialog>` and Tailwind 4 support for the dashboard: Chrome 111+, Safari 16.4+, Firefox 128+.

```bash
pip install -U django-insights
```

## 2. Rename your settings

The three settings without the `S` are renamed. The old names are ignored, `manage.py check` warns when they are still set (`insights.W006`).

| Old | New |
| --- | --- |
| `INSIGHT_CHARTS_USE_MEDIA_CACHE` | `INSIGHTS_CHARTS_USE_MEDIA_CACHE` |
| `INSIGHT_MEDIA_CACHE_ROOT` | `INSIGHTS_MEDIA_CACHE_ROOT` |
| `INSIGHT_DASHBOARD_PERMISSIONS` | `INSIGHTS_DASHBOARD_PERMISSIONS` |

The chart color settings are replaced by one theme setting (`manage.py check` warns with `insights.W010` while they are still set):

| Old | New |
| --- | --- |
| `INSIGHTS_CHART_LIGHT_PRIMARY_COLOR` | `INSIGHTS_THEME`, see below |
| `INSIGHTS_CHART_DARK_PRIMARY_COLOR` | `INSIGHTS_THEME`, see below |

```python
INSIGHTS_THEME = "blue"  # a shadcn theme name
INSIGHTS_THEME = {"accent": "#ec4899"}  # or any hex color
INSIGHTS_STYLE = "vega"  # Basecoat style, optional
```

The dashboard and the charts share one palette now. All names and the dict form are in the README (Theming).

Unchanged: `INSIGHTS_APP_NAME`, `INSIGHTS_CHART_DPI`, `INSIGHTS_DEFAULT_THEME`.

Other things about settings:

- [ ] Settings are read when they are used, so `override_settings` works. Unknown names raise `AttributeError`.
- [ ] `INSIGHTS_CHARTS_USE_MEDIA_CACHE = True` requires `INSIGHTS_MEDIA_CACHE_ROOT` (`insights.W003`).
- [ ] `INSIGHTS_DASHBOARD_PERMISSIONS` fails closed: a class without `has_permission(request)` used to be skipped, which granted access. It now raises `ImproperlyConfigured`. Check that every class you list has the method and returns `True` for the people who should get in.
- [ ] System checks are warnings only (`insights.W001` to `W012`), they never stop the project from starting. `django_insights.database.check_settings()` is removed, run `manage.py check`.

## 3. Migrate the insights database

Two migrations, both for the `insights` database. Your data is kept.

```bash
python manage.py migrate insights --database=insights
```

- `0002`: labels are unique per app (two apps can both have `count_users`), `Counter.value` is a big integer, explicit ordering, the unused histogram type, `ExecutionDelta` model and `Gauge.gauge()` are removed.
- `0003`: a `trend` column for counters and gauges.

The insights database is a cache of your data, so you can also delete it and run `collect_insights`.

- [ ] Run `python manage.py collect_insights` once after upgrading. Dashboard URLs now use a stable id per app (derived from the module path), so old bookmarks of `/app/<uuid>/` stop working once.

## 4. Collecting

- [ ] `collect_insights` runs in one transaction. A failing insight is logged (logger `django_insights.registry`), reported on stderr and makes the command exit with an error (`3 of 14 insights failed`), the other insights still run. Cron jobs and CI will now see a non-zero exit code, check your monitoring.
- [ ] `metrics.collect()` returns the list of failures. It raises `InsightsError` (from `django_insights.exceptions`) when an insight saves duplicates, it no longer prints and calls `exit()`.
- [ ] The progress bar is hidden when output is not a terminal.
- [ ] The chart cache only deletes cached `*-*-*.png` files, it no longer wipes the whole media cache root.

## 5. PDF export is removed

The PDF report is gone, together with its dependencies. Nothing replaces it.

- [ ] Remove links to `insights:insight_pdf` and `insights:insight_pdf_test` (`insights/pdf/` and `insights/pdf/test/`), they no longer exist.
- [ ] Remove the `[pdf]` extra from your requirements: `pip install 'django-insights[pdf]'` is no longer needed. `weasyprint` and `django-weasyprint` are not dependencies anymore, and PyMuPDF is not used.
- [ ] If you override `insights/pdf.html` or `pdf.css`, delete them. `{% pdf_chart %}` and `pdf_available` are removed too.
- [ ] No system libraries (Pango and friends) are needed anymore.

## 6. Templates and static files

Only needed if you override templates or use the template tags yourself.

- [ ] The dashboard is rebuilt with Basecoat UI. Templates under `insights/` have new structure (`base.html`, `dashboard.html`, `app.html`, `_bucket.html`, `_stat.html`, `_empty.html`). If you override any, start from the new ones.
- [ ] `{% chart bucket %}` no longer takes an `overlay` argument.
- [ ] Stylesheets are compiled per Basecoat style (`insights/css/<style>.css`), icons are CSS classes, the Geist font is served from the package. Nothing is loaded from a CDN. Run `collectstatic` as usual.
- [ ] The chart font is Geist (was Ubuntu). The library no longer changes matplotlib's global configuration, the chart style is only applied while a chart is built.

## 7. Using the library in code

- [ ] The `insights` console script is removed (it never worked).
- [ ] `bar` and `hbar` charts no longer crash when a category is `None`.
- [ ] Only the names in `__all__` of `django_insights.metrics` and `django_insights.metrics_types` are public.
- [ ] New and optional: counters and gauges accept `trend=` for a sparkline and change percentage that survive a rebuild of the database:

```python
@metrics.counter(label="Users", trend=users_per_month)
def count_users() -> int: ...
```

`trend` is a function that returns `(datetime, value)` rows, the last 60 points are stored.

## 8. Tests

If you test your insights with the pytest plugin:

- [ ] The plugin loads through the `pytest11` entry point, you do not need to register it. It does nothing at import and does not need Django to be configured.
- [ ] The module-level `registry`, `register_insights_modules` and the injected fixture are removed. If you imported them from `django_insights.pytest`, use the `insights_query` fixture instead.
- [ ] `insights_query` returns the plain function behind an insight. It is found by the test name (without `test_`), by a name given to the `insights` marker, or by `module.name`. A missing or ambiguous name fails the test.
- [ ] Errors inside an `insights.py` are no longer swallowed. The `insights` marker is registered, so `--strict-markers` works.

## 9. Building from source

Only for contributors.

- [ ] `uv build` replaces flit. The version comes from the latest git tag (setuptools-scm). The wheel no longer contains `node_modules`.
- [ ] `pnpm install && pnpm build` in `django_insights/packages` rebuilds the dashboard CSS. pnpm is pinned in `package.json`.
- [ ] ruff replaces black, isort and flake8, tox runs through uv. Releases are made by pushing a tag, the release workflow publishes to PyPI.

## Quick check

```bash
python manage.py check                              # no insights warnings
python manage.py migrate insights --database=insights
python manage.py collect_insights                   # exit code 0
```
