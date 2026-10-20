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

An **accent** changes the primary color and the five chart colors. The chart bars and lines use the middle color of the ramp, in light and dark mode.

| Accent    | Primary (light)  | Primary (dark)   | Chart colors                                                                         |
| --------- | ---------------- | ---------------- | ------------------------------------------------------------------------------------ |
| `amber`   | :swatch[#b55200] | :swatch[#953d00] | :swatch[#ffd237] :swatch[#f69e00] :swatch[#da7700] :swatch[#b55200] :swatch[#953d00] |
| `blue`    | :swatch[#1447e6] | :swatch[#193cb8] | :swatch[#91c5ff] :swatch[#3280ff] :swatch[#155dfc] :swatch[#1447e6] :swatch[#193cb8] |
| `cyan`    | :swatch[#007492] | :swatch[#005f78] | :swatch[#53eafd] :swatch[#00b6d4] :swatch[#0091b3] :swatch[#007492] :swatch[#005f78] |
| `emerald` | :swatch[#007857] | :swatch[#005f46] | :swatch[#5ee9b5] :swatch[#00b980] :swatch[#009669] :swatch[#007857] :swatch[#005f46] |
| `fuchsia` | :swatch[#a600b4] | :swatch[#8a0194] | :swatch[#f2a9ff] :swatch[#e12afb] :swatch[#c500da] :swatch[#a600b4] :swatch[#8a0194] |
| `green`   | :swatch[#008139] | :swatch[#016630] | :swatch[#7bf1a8] :swatch[#00c65a] :swatch[#00a447] :swatch[#008139] :swatch[#016630] |
| `indigo`  | :swatch[#432dd7] | :swatch[#372aac] | :swatch[#a4b4ff] :swatch[#6260ff] :swatch[#4f39f6] :swatch[#432dd7] :swatch[#372aac] |
| `lime`    | :swatch[#9de500] | :swatch[#83cc00] | :swatch[#bbf451] :swatch[#83cc00] :swatch[#64a300] :swatch[#4b7d00] :swatch[#3c6300] |
| `orange`  | :swatch[#c43e00] | :swatch[#9f2d00] | :swatch[#ffb970] :swatch[#fc7100] :swatch[#ec5600] :swatch[#c43e00] :swatch[#9f2d00] |
| `pink`    | :swatch[#c3005c] | :swatch[#a2004c] | :swatch[#fda5d5] :swatch[#f6339a] :swatch[#e30076] :swatch[#c3005c] :swatch[#a2004c] |
| `purple`  | :swatch[#8200da] | :swatch[#6e11b0] | :swatch[#d8b4ff] :swatch[#ab4eff] :swatch[#9810fa] :swatch[#8200da] :swatch[#6e11b0] |
| `red`     | :swatch[#bf000f] | :swatch[#9f0712] | :swatch[#ffa3a4] :swatch[#fb2c36] :swatch[#e40016] :swatch[#bf000f] :swatch[#9f0712] |
| `rose`    | :swatch[#c1003a] | :swatch[#a30037] | :swatch[#ffa3ae] :swatch[#ff2357] :swatch[#e60044] :swatch[#c1003a] :swatch[#a30037] |
| `sky`     | :swatch[#0069a2] | :swatch[#005987] | :swatch[#78d4ff] :swatch[#00a5eb] :swatch[#0084c8] :swatch[#0069a2] :swatch[#005987] |
| `teal`    | :swatch[#00776e] | :swatch[#005f5a] | :swatch[#46ecd5] :swatch[#00b9a6] :swatch[#009488] :swatch[#00776e] :swatch[#005f5a] |
| `violet`  | :swatch[#7008e7] | :swatch[#5d0ec0] | :swatch[#c4b4ff] :swatch[#8d56ff] :swatch[#7f22fe] :swatch[#7008e7] :swatch[#5d0ec0] |
| `yellow`  | :swatch[#f7c900] | :swatch[#eab300] | :swatch[#ffe02f] :swatch[#eab300] :swatch[#cb8a00] :swatch[#a26200] :swatch[#874b00] |

A **base** changes the greys of the background, cards and borders, and gives grey charts. The swatches are the background, card, muted and border color.

| Base      | Light                                                               | Dark                                                                |
| --------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `neutral` | :swatch[#ffffff] :swatch[#ffffff] :swatch[#f5f5f5] :swatch[#e5e5e5] | :swatch[#0a0a0a] :swatch[#171717] :swatch[#262626] :swatch[#2e2e2e] |
| `stone`   | :swatch[#ffffff] :swatch[#ffffff] :swatch[#f5f5f4] :swatch[#e7e5e4] | :swatch[#0c0a09] :swatch[#1c1917] :swatch[#292524] :swatch[#33302e] |
| `zinc`    | :swatch[#ffffff] :swatch[#ffffff] :swatch[#f4f4f5] :swatch[#e4e4e7] | :swatch[#09090b] :swatch[#18181b] :swatch[#27272a] :swatch[#2f2f32] |
| `mauve`   | :swatch[#ffffff] :swatch[#ffffff] :swatch[#f3f1f3] :swatch[#e7e4e7] | :swatch[#0c090c] :swatch[#1d161e] :swatch[#2a212c] :swatch[#342d34] |
| `olive`   | :swatch[#ffffff] :swatch[#ffffff] :swatch[#f4f4f0] :swatch[#e8e8e3] | :swatch[#0c0c09] :swatch[#1d1d16] :swatch[#2b2b22] :swatch[#34342d] |
| `mist`    | :swatch[#ffffff] :swatch[#ffffff] :swatch[#f1f3f3] :swatch[#e3e7e8] | :swatch[#090b0c] :swatch[#161b1d] :swatch[#22292b] :swatch[#2d3234] |
| `taupe`   | :swatch[#ffffff] :swatch[#ffffff] :swatch[#f3f1f1] :swatch[#e8e4e3] | :swatch[#0c0a09] :swatch[#1d1816] :swatch[#2b2422] :swatch[#342f2d] |

The default is the shadcn `neutral` base with the blue Basecoat charts. Any hex color is an accent too, see below.

## Your own colors

Combine them, or set single colors, with a dict. `accent` takes a theme name or any hex color, `light` and `dark` set colors on top of it:

```python
INSIGHTS_THEME = {
    "base": "zinc",
    "accent": "blue",
    "dark": {"card": "#111827", "border": "#1f2937"},
}
```

A color is one of the shadcn variables with underscores, written as `"#rrggbb"`: `background`, `foreground`, `card`, `muted_foreground`, `border`, `primary`, `primary_foreground`, `sidebar_primary`, `chart_1` to `chart_5` and the rest of the shadcn set.

:::details[All color names]
`background`, `foreground`, `card`, `card_foreground`, `popover`, `popover_foreground`, `primary`, `primary_foreground`, `secondary`, `secondary_foreground`, `muted`, `muted_foreground`, `accent`, `accent_foreground`, `destructive`, `border`, `input`, `ring`, `chart_1` to `chart_5`, `sidebar`, `sidebar_foreground`, `sidebar_primary`, `sidebar_primary_foreground`, `sidebar_accent`, `sidebar_accent_foreground`, `sidebar_border` and `sidebar_ring`.
:::

A chart uses `card` as its background, `foreground` for its text and `chart_3` for its bars and lines. Anything that is not a known name with a `"#rrggbb"` value is ignored, and `manage.py check` tells you what (`insights.W007` to `W009`, see [System checks](../reference/checks.md)).

A single accent color, for example :swatch[#ec4899] `"#ec4899"`, gives a primary color and a ramp of five chart colors that is lighter at the start and darker at the end:

```python
INSIGHTS_THEME = {"accent": "#ec4899"}
```

## Light and dark

`INSIGHTS_DEFAULT_THEME` is `"dark"` or `"light"`, the mode used until a visitor picks one in the dashboard.

## Updating the colors

The theme colors come from the shadcn registry. To update them, in a checkout of Django Insights:

```bash
python scripts/generate_palettes.py
ruff format django_insights/palettes.py
```
