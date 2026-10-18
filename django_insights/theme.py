from __future__ import annotations

import colorsys
import hashlib
import json
import re
from typing import Any

from django_insights.settings import settings

__all__ = [
    'DEFAULT_STYLE',
    'PRESETS',
    'STYLES',
    'chart_colors',
    'css_overrides',
    'fingerprint',
    'palette',
    'problems',
    'style',
    'stylesheet',
]

PRESETS = {
    'blue': '#2563eb',
    'green': '#16a34a',
    'orange': '#ea580c',
    'red': '#dc2626',
    'pink': '#ec4899',
    'violet': '#7c3aed',
    'teal': '#0d9488',
}
STYLES = ('vega', 'nova', 'maia', 'lyra', 'mira', 'luma', 'sera', 'rhea')
DEFAULT_STYLE = 'vega'
MODES = ('light', 'dark')
HEX = re.compile(r'^#[0-9a-fA-F]{6}$')
CHART_STEPS = (0.22, 0.08, 0.0, -0.06, -0.14)
CHART_KEYS = tuple(f'chart_{number}' for number in range(1, 6))
KEYS = (
    'background',
    'foreground',
    'card',
    'muted_foreground',
    'border',
    'primary',
    'primary_foreground',
    *CHART_KEYS,
)

# the Basecoat defaults as hex, charts cannot read the oklch colors of the stylesheet
CHART_DEFAULTS = dict(
    zip(
        CHART_KEYS, ('#93c5fd', '#3b82f6', '#2563eb', '#1d4ed8', '#1e40af'), strict=True
    )
)
DEFAULTS = {
    'light': {
        'background': '#ffffff',
        'foreground': '#0a0a0a',
        'card': '#ffffff',
        'muted_foreground': '#737373',
        'border': '#e5e5e5',
        'primary': '#171717',
        'primary_foreground': '#fafafa',
        **CHART_DEFAULTS,
    },
    'dark': {
        'background': '#0a0a0a',
        'foreground': '#fafafa',
        'card': '#171717',
        'muted_foreground': '#a3a3a3',
        'border': '#2e2e2e',
        'primary': '#e5e5e5',
        'primary_foreground': '#171717',
        **CHART_DEFAULTS,
    },
}
VARIABLES = {
    'background': ('--background',),
    'foreground': ('--foreground',),
    'card': ('--card', '--popover'),
    'muted_foreground': ('--muted-foreground',),
    'border': ('--border',),
    'primary': ('--primary', '--sidebar-primary', '--ring'),
    'primary_foreground': ('--primary-foreground', '--sidebar-primary-foreground'),
    **{key: (f'--chart-{key[-1]}',) for key in CHART_KEYS},
}


def style() -> str:
    """The Basecoat style pack, the default when the setting is not a known one"""
    name = settings.INSIGHTS_STYLE
    return name if name in STYLES else DEFAULT_STYLE


def stylesheet() -> str:
    return f'insights/css/{style()}.css'


def lightness(color: str, shift: float) -> str:
    red, green, blue = (int(color[index : index + 2], 16) / 255 for index in (1, 3, 5))
    hue, light, saturation = colorsys.rgb_to_hls(red, green, blue)
    red, green, blue = colorsys.hls_to_rgb(
        hue, min(max(light + shift, 0.1), 0.92), saturation
    )
    return '#{:02x}{:02x}{:02x}'.format(
        *(round(part * 255) for part in (red, green, blue))
    )


def readable_on(color: str) -> str:
    """Dark text on light colors and the other way around"""
    red, green, blue = (int(color[index : index + 2], 16) / 255 for index in (1, 3, 5))
    return '#0a0a0a' if 0.299 * red + 0.587 * green + 0.114 * blue > 0.6 else '#fafafa'


def from_accent(accent: str) -> dict[str, dict[str, str]]:
    """Primary color and the chart colors of both modes, derived from one color"""
    accent = accent.lower()
    charts = {
        key: accent if step == 0 else lightness(accent, step)
        for key, step in zip(CHART_KEYS, CHART_STEPS, strict=True)
    }
    dark_primary = lightness(accent, 0.12)
    return {
        'light': {
            'primary': accent,
            'primary_foreground': readable_on(accent),
            **charts,
        },
        'dark': {
            'primary': dark_primary,
            'primary_foreground': readable_on(dark_primary),
            **charts,
        },
    }


def configured_theme() -> dict[str, Any]:
    """INSIGHTS_THEME as a dict, a preset name is the same as {'accent': name}"""
    configured: Any = settings.INSIGHTS_THEME
    if isinstance(configured, str):
        return {'accent': configured}
    return configured if isinstance(configured, dict) else {}


def accent_color(value: object) -> str | None:
    """A preset name or a hex color as hex, None for anything else"""
    if isinstance(value, str):
        if value in PRESETS:
            return PRESETS[value]
        if HEX.match(value):
            return value.lower()
    return None


def user_colors() -> dict[str, dict[str, str]]:
    """The valid colors per mode of INSIGHTS_THEME, anything else is ignored"""
    return {
        mode: {
            key: value.lower()
            for key, value in colors.items()
            if key in KEYS and isinstance(value, str) and HEX.match(value)
        }
        for mode, colors in configured_theme().items()
        if mode in MODES and isinstance(colors, dict)
    }


def overrides(mode: str) -> dict[str, str]:
    """What differs from the Basecoat defaults, the accent first and your colors on top"""
    accent = accent_color(configured_theme().get('accent'))
    derived = from_accent(accent)[mode] if accent else {}
    return {**derived, **user_colors().get(mode, {})}


def palette(mode: str) -> dict[str, str]:
    """Every color of a mode as hex, the dashboard and the charts both use these"""
    if mode not in MODES:
        raise ValueError(f"Unknown theme: {mode}")
    return {**DEFAULTS[mode], **overrides(mode)}


def chart_colors(mode: str) -> dict[str, str]:
    """The colors of a chart, taken from the same palette as the dashboard"""
    colors = palette(mode)
    return {
        'primary': colors['chart_3'] if mode == 'light' else colors['chart_1'],
        'face': colors['card'],
        'edge': colors['card'],
        'tick': colors['foreground'],
        'grid': colors['foreground'],
    }


def css_overrides() -> str:
    """CSS variables for the colors that are set, empty when everything is default"""
    blocks = []
    for mode, selector in (('light', ':root'), ('dark', '.dark')):
        declarations = ''.join(
            f'{variable}:{color};'
            for key, color in overrides(mode).items()
            for variable in VARIABLES[key]
        )
        if declarations:
            blocks.append(f'{selector}{{{declarations}}}')
    return ''.join(blocks)


def fingerprint() -> str:
    """Changes with the colors, so cached chart images are not served in old colors"""
    colors = json.dumps({mode: palette(mode) for mode in MODES}, sort_keys=True)
    return hashlib.sha256(colors.encode()).hexdigest()[:12]


def problems() -> list[tuple[str, str]]:
    """Settings that are ignored, as (check id, message)"""
    found: list[tuple[str, str]] = []
    if settings.INSIGHTS_STYLE not in STYLES:
        found.append(
            (
                'insights.W007',
                f"INSIGHTS_STYLE {settings.INSIGHTS_STYLE!r} is not one of "
                f"{', '.join(STYLES)}, '{DEFAULT_STYLE}' is used.",
            )
        )

    found.extend(theme_problems())
    return found


def theme_problems() -> list[tuple[str, str]]:
    configured: Any = settings.INSIGHTS_THEME
    if configured is None:
        return []
    if isinstance(configured, str):
        configured = {'accent': configured}
    if not isinstance(configured, dict):
        return [
            (
                'insights.W009',
                'INSIGHTS_THEME must be a preset name like "pink" or a dict like '
                '{"accent": "#ec4899", "dark": {"card": "#101010"}}.',
            )
        ]

    messages = []
    for mode, colors in configured.items():
        if mode == 'accent':
            if accent_color(colors) is None:
                messages.append(
                    (
                        'insights.W008',
                        f'INSIGHTS_THEME accent {colors!r} is not one of '
                        f'{", ".join(PRESETS)} or a color like "#ec4899".',
                    )
                )
        elif mode not in MODES or not isinstance(colors, dict):
            messages.append(
                (
                    'insights.W009',
                    f"INSIGHTS_THEME has {mode!r}, use 'accent', 'light' and 'dark'.",
                )
            )
        else:
            messages.extend(
                (
                    'insights.W009',
                    f'INSIGHTS_THEME[{mode!r}] has {key!r}, known colors are '
                    f'{", ".join(KEYS)}.'
                    if key not in KEYS
                    else f'INSIGHTS_THEME[{mode!r}][{key!r}] must be a color like "#101010".',
                )
                for key, value in colors.items()
                if key not in KEYS or not (isinstance(value, str) and HEX.match(value))
            )
    return messages
