from django_insights.models import App


def test_app_name_prefers_label():
    assert App(module='pkg.insights', label='Shop').name == 'Shop'
    assert App(module='pkg.insights').name == 'pkg.insights'
