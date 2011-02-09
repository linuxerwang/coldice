# -*- coding: utf-8 -*


from whoosh.fields import Schema, TEXT


INDEX_SCHEMA = Schema(
    title = TEXT(stored = True),
    url = TEXT(stored = True),
    category = TEXT(stored = False),
    body = TEXT(stored = True),
    content = TEXT(stored = False)
)
