---
title: Theming
description: Pick a Basecoat style and shadcn/ui colors, shared by the dashboard and the charts.
sidebar:
  order: 3
---

The dashboard and the charts share one palette, so a color you set shows up in both. `INSIGHTS_STYLE` picks one of the [Basecoat styles](https://basecoatui.com/customization/), `INSIGHTS_THEME` sets the colors with the names of the [shadcn/ui themes](https://ui.shadcn.com/themes):

```python
INSIGHTS_STYLE = "sera"
INSIGHTS_THEME = "blue"
```

## Styles

`vega` (the default), `nova`, `maia`, `lyra`, `mira`, `luma`, `sera` and `rhea`.

## Colors

- **Accent colors** change the primary color and the five chart colors: `amber`, `blue`, `cyan`, `emerald`, `fuchsia`, `green`, `indigo`, `lime`, `orange`, `pink`, `purple`, `red`, `rose`, `sky`, `teal`, `violet` and `yellow`.
- **Base colors** change the greys of the background, cards and borders, and give grey charts: `neutral`, `stone`, `zinc`, `mauve`, `olive`, `mist` and `taupe`.

## Your own colors

Combine them, or set single colors, with a dict. `accent` takes a theme name or any hex color, `light` and `dark` set colors on top of it:

```python
INSIGHTS_THEME = {
    "base": "zinc",
    "accent": "blue",
    "dark": {"card": "#111827", "border": "#1f2937"},
}
```

A color is one of the shadcn variables with underscores, all as `"#rrggbb"`:

- `background`, `foreground`, `card`, `muted_foreground`, `border`
- `primary`, `primary_foreground`, `sidebar_primary`
- `chart_1` to `chart_5`

A chart uses `card` as its background, `foreground` for its text, and `chart_3` (light) or `chart_1` (dark) for its bars and lines. Anything else is ignored, and `manage.py check` tells you what (`insights.W007` to `W009`, see [System checks](../reference/checks.md)).

## Light and dark

`INSIGHTS_DEFAULT_THEME` is `"dark"` or `"light"`, the mode used until a visitor picks one in the dashboard.

## Updating the colors

The theme colors come from the shadcn registry. To update them, in a checkout of Django Insights:

```bash
python scripts/generate_palettes.py
ruff format django_insights/palettes.py
```
