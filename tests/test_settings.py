from django.test import override_settings

from django_insights.settings import settings


def test_defaults_apply_when_django_setting_is_missing():
    assert settings.INSIGHT_DASHBOARD_PERMISSIONS is None
    assert settings.INSIGHT_CHARTS_USE_MEDIA_CACHE is False
    assert settings.INSIGHTS_DEFAULT_THEME == 'dark'


def test_django_settings_take_precedence():
    assert settings.INSIGHTS_APP_NAME == 'Finq'
    with override_settings(INSIGHTS_CHART_DPI=72):
        assert settings.INSIGHTS_CHART_DPI == 72


def test_unknown_setting_raises():
    assert not hasattr(settings, 'INSIGHTS_DOES_NOT_EXIST')
