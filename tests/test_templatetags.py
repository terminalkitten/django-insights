import pytest

from django_insights.choices import BucketType
from django_insights.models import App, Bucket
from django_insights.templatetags.insight_chart import base64img, chart, pdf_chart
from django_insights.templatetags.nice_format import nice_float


@pytest.mark.parametrize(
    ('value', 'expected'),
    [(1234567.0, '1.234.567'), (0.0, '0'), (5, 5), ('text', 'text'), (None, None)],
)
def test_nice_float(value, expected):
    assert nice_float(value) == expected


def test_chart_tag_escapes_question_and_overlay():
    html = chart(Bucket(pk=7, question='"><script>x</script>'), overlay='a"b')
    assert '<script>' not in html
    assert '&quot;&gt;&lt;script&gt;' in html
    assert 'a&quot;b' in html


@pytest.mark.django_db(databases=['default', 'insights'])
def test_pdf_chart_renders_inline_png(collected):
    bucket = Bucket.objects.earliest('pk')
    assert 'data:image/png;base64,' in pdf_chart(bucket.pk)


@pytest.mark.django_db(databases=['default', 'insights'])
def test_unsupported_bucket_type_is_rejected():
    app = App.objects.create(module='tests.unsupported')
    bucket = Bucket.objects.create(app=app, label='odd', type=BucketType.HISTOGRAM)
    with pytest.raises(ValueError, match='Unsupported bucket type'):
        base64img(bucket)
