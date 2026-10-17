import sys

import pymupdf
import pytest
from django.contrib.staticfiles import finders
from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse

from django_insights import pdf
from django_insights.pdf import PAGE_BREAK, get_css, html_to_pdf


@pytest.mark.django_db(databases=['default', 'insights'])
def test_pdf_view_renders_numbered_pages(viewer_client, collected):
    response = viewer_client.get(reverse('insights:insight_pdf'))
    assert response.status_code == 200
    assert response['Content-Type'] == 'application/pdf'

    document = pymupdf.open('pdf', response.content)
    assert 3 <= len(document) < 100
    assert 'Insights' in document[0].get_text()
    assert any(page.get_images() for page in document)
    assert document[0].get_text().strip().endswith('Insights Finq')
    assert document[1].get_text().strip().endswith('2')


def test_html_to_pdf_starts_new_page_at_marker():
    html = f'<body><p>one</p>{PAGE_BREAK}<p>two</p></body>'
    document = pymupdf.open('pdf', html_to_pdf(html))
    assert len(document) == 2


def test_html_to_pdf_requires_pymupdf(monkeypatch):
    monkeypatch.setitem(sys.modules, 'pymupdf', None)
    with pytest.raises(ImproperlyConfigured, match='PyMuPDF'):
        html_to_pdf('<body>x</body>')


def test_stylesheet_is_required(monkeypatch):
    get_css.cache_clear()
    monkeypatch.setattr(finders, 'find', lambda path: None)
    try:
        with pytest.raises(ImproperlyConfigured, match=r'pdf\.css'):
            get_css()
    finally:
        get_css.cache_clear()


def test_page_limit_stops_runaway_documents(monkeypatch):
    monkeypatch.setattr(pdf, 'MAX_PAGES', 1)
    html = f'<body><p>one</p>{PAGE_BREAK}<p>two</p></body>'
    with pytest.raises(RuntimeError, match='more than 1 pages'):
        html_to_pdf(html)
