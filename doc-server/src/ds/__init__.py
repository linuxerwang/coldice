# -*- coding: utf-8 -*


from whoosh.analysis import StemmingAnalyzer
from whoosh.fields import Schema, TEXT, NUMERIC


STEM_ANALYZER = StemmingAnalyzer()


INDEX_SCHEMA = Schema(
    url = TEXT(stored = True),
    path = TEXT(analyzer=STEM_ANALYZER, stored = True),
    refer = NUMERIC(float, stored=True),
    referred = NUMERIC(float, stored=True),
    h1 = TEXT(analyzer=STEM_ANALYZER, stored = True),
    h2 = TEXT(analyzer=STEM_ANALYZER, stored = True),
    h3 = TEXT(analyzer=STEM_ANALYZER, stored = True),
    h4 = TEXT(analyzer=STEM_ANALYZER, stored = True),
    h5 = TEXT(analyzer=STEM_ANALYZER, stored = True),
    title = TEXT(analyzer=STEM_ANALYZER, stored = True),
    content = TEXT(analyzer=STEM_ANALYZER, stored = True)
)

