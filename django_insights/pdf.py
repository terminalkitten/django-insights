from __future__ import annotations

import io
import warnings
from functools import lru_cache
from pathlib import Path

from django.contrib.staticfiles import finders
from django.core.exceptions import ImproperlyConfigured

PAGE_BREAK = '<!--pagebreak-->'
MARGIN = 40
MAX_PAGES = 500


@lru_cache
def get_css() -> str:
    # finders work without collectstatic
    path = finders.find('insights/css/pdf.css')
    if not isinstance(path, str):
        raise ImproperlyConfigured(
            'insights/css/pdf.css not found, add django_insights to INSTALLED_APPS'
        )
    return Path(path).read_text()


def html_to_pdf(html: str) -> bytes:
    """Render an HTML body to PDF, one story per PAGE_BREAK part (Story restarts on CSS breaks)"""
    try:
        with warnings.catch_warnings():
            # SWIG import warnings segfault under -W error
            warnings.filterwarnings(
                'ignore',
                message='builtin type .* has no __module__',
                category=DeprecationWarning,
            )
            import pymupdf
    except ImportError as e:
        raise ImproperlyConfigured(
            "PDF export needs PyMuPDF (AGPL-3.0): pip install 'django-insights[pdf]'"
        ) from e

    body = html.split('<body>', 1)[-1].split('</body>', 1)[0]
    css = get_css()
    mediabox = pymupdf.paper_rect('a4')
    where = mediabox + (MARGIN, MARGIN, -MARGIN, -MARGIN)

    buffer = io.BytesIO()
    writer = pymupdf.DocumentWriter(buffer)
    pages = 0
    for part in body.split(PAGE_BREAK):
        if not part.strip():
            continue
        story = pymupdf.Story(html=f'<html><body>{part}</body></html>', user_css=css)
        more = True
        while more:
            pages += 1
            if pages > MAX_PAGES:
                raise RuntimeError(f'PDF export aborted, more than {MAX_PAGES} pages')
            device = writer.begin_page(mediabox)
            more, filled = story.place(where)
            if more and pymupdf.Rect(filled).is_empty:
                raise RuntimeError('PDF export aborted, content does not fit a page')
            story.draw(device)
            writer.end_page()
    writer.close()

    # no number on the cover
    document = pymupdf.open('pdf', buffer.getvalue())
    for number, page in enumerate(document.pages(), start=1):
        if number > 1:
            page.insert_text(
                (mediabox.width - MARGIN, mediabox.height - MARGIN / 2),
                str(number),
                fontsize=8,
            )
    return document.tobytes(garbage=3, deflate=True)
