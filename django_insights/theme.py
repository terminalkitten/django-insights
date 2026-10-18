from __future__ import annotations

import colorsys
import hashlib
import json
import re
from typing import Any

from django_insights.palettes import ACCENTS, BASES
from django_insights.settings import settings

__all__ = [
    'ACCENT_NAMES',
    'BASE_NAMES',
    'DEFAULT_STYLE',
    'STYLES',
    'chart_colors',
    'css_overrides',
    'fingerprint',
    'palette',
    'problems',
    'style',
    'stylesheet',
]

STYLES = ('vega', 'nova', 'maia', 'lyra', 'mira', 'luma', 'sera', 'rhea')
DEFAULT_STYLE = 'vega'
MODES = ('light', 'dark')
HEX = re.compile(r'\A#[0-9a-fA-F]{6}\Z')
BASE_NAMES = tuple(BASES)
ACCENT_NAMES = tuple(ACCENTS)
CHART_STEPS = (0.22, 0.08, 0.0, -0.06, -0.14)
CHART_KEYS = tuple(f'chart_{number}' for number in range(1, 6))
KEYS = tuple(BASES['neutral']['light'])

# Basecoat colors its charts blue, the shadcn neutral theme grey
BASECOAT_CHARTS = dict(
    zip(
        CHART_KEYS, ('#93c5fd', '#3b82f6', '#2563eb', '#1d4ed8', '#1e40af'), strict=True
    )
)
DEFAULTS = {
    mode: {**BASES['neutral'][mode], **BASECOAT_CHARTS} for mode in ('light', 'dark')
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
    return {
        'light': {
            'primary': accent,
            'primary_foreground': readable_on(accent),
            'sidebar_primary': accent,
            'sidebar_primary_foreground': readable_on(accent),
            **charts,
        },
        'dark': {
            'primary': accent,
            'primary_foreground': readable_on(accent),
            'sidebar_primary': accent,
            'sidebar_primary_foreground': readable_on(accent),
            **charts,
        },
    }


def configured_theme() -> dict[str, Any]:
    """INSIGHTS_THEME as a dict, a name is the same as {'base': name} or {'accent': name}"""
    configured: Any = settings.INSIGHTS_THEME
    if isinstance(configured, str):
        return {'base': configured} if configured in BASES else {'accent': configured}
    return configured if isinstance(configured, dict) else {}


def accent_colors(value: object) -> dict[str, dict[str, str]]:
    """The colors of an accent, a shadcn theme name or any hex color, empty when unknown"""
    if isinstance(value, str):
        if value in ACCENTS:
            return ACCENTS[value]
        if HEX.match(value):
            return from_accent(value)
    return {}


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
    """What differs from the Basecoat defaults: base, accent and then your colors"""
    configured = configured_theme()
    name = configured.get('base')
    base = BASES[name][mode] if isinstance(name, str) and name in BASES else {}
    accent = accent_colors(configured.get('accent')).get(mode, {})
    merged = {**base, **accent, **user_colors().get(mode, {})}
    return {key: color for key, color in merged.items() if color != DEFAULTS[mode][key]}


def palette(mode: str) -> dict[str, str]:
    """Every color of a mode as hex, the dashboard and the charts both use these"""
    if mode not in MODES:
        raise ValueError(f"Unknown theme: {mode}")
    return {**DEFAULTS[mode], **overrides(mode)}


def chart_colors(mode: str) -> dict[str, str]:
    """The colors of a chart, taken from the same palette as the dashboard"""
    colors = palette(mode)
    return {
        'primary': colors['chart_3'],
        'face': colors['card'],
        'edge': colors['card'],
        'tick': colors['foreground'],
        'grid': colors['foreground'],
    }


def css_overrides() -> str:
    """CSS variables for the colors that are set, empty when everything is default

    A color that differs in one mode is written for both, otherwise the light value
    would also win in dark mode, the stylesheet of the dashboard comes first.
    """
    keys = [key for key in KEYS if any(key in overrides(mode) for mode in MODES)]
    blocks = []
    for mode, selector in (('light', ':root'), ('dark', '.dark')):
        colors = palette(mode)
        declarations = ''.join(
            f"--{key.replace('_', '-')}:{colors[key]};" for key in keys
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
        configured = configured_theme()
    if not isinstance(configured, dict):
        return [
            (
                'insights.W009',
                'INSIGHTS_THEME must be a name like "blue", or a dict like '
                '{"base": "zinc", "accent": "blue", "dark": {"card": "#101010"}}.',
            )
        ]

    messages: list[tuple[str, str]] = []
    for key, value in configured.items():
        messages.extend(key_problems(key, value))
    return messages


def key_problems(key: str, value: object) -> list[tuple[str, str]]:
    if key == 'base':
        if isinstance(value, str) and value in BASES:
            return []
        return [
            (
                'insights.W008',
                f'INSIGHTS_THEME base {value!r} is not one of {", ".join(BASE_NAMES)}.',
            )
        ]
    if key == 'accent':
        if accent_colors(value):
            return []
        return [
            (
                'insights.W008',
                f'INSIGHTS_THEME accent {value!r} is not one of {", ".join(ACCENT_NAMES)} '
                'or a color like "#ec4899".',
            )
        ]
    if key in MODES and isinstance(value, dict):
        return color_problems(key, value)
    return [
        (
            'insights.W009',
            f"INSIGHTS_THEME has {key!r}, use 'base', 'accent', 'light' and 'dark'.",
        )
    ]


def color_problems(mode: str, colors: dict[str, Any]) -> list[tuple[str, str]]:
    return [
        (
            'insights.W009',
            f'INSIGHTS_THEME[{mode!r}] has {name!r}, known colors are {", ".join(KEYS)}.'
            if name not in KEYS
            else f'INSIGHTS_THEME[{mode!r}][{name!r}] must be a color like "#101010".',
        )
        for name, color in colors.items()
        if name not in KEYS or not (isinstance(color, str) and HEX.match(color))
    ]
