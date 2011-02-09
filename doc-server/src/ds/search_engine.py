#!/usr/bin/python
# -*- coding: utf-8 -*-

import archive
import os
from whoosh.index import create_in, exists_in, open_dir
from BeautifulSoup import BeautifulSoup
from ds import INDEX_SCHEMA


IGNORE_TAGS = set([
    'meta',
    'link',
    'script',
    'style',
])


class SearchIndexer(object):
    def __init__(self, doc_base, categories=None):
        self.__doc_base = doc_base
        self.__categories = categories
        self.__index_folder = os.path.join(self.__doc_base, '.indices')

        if not os.path.exists(self.__index_folder):
            print '    Create index directory', self.__index_folder
            os.mkdir(self.__index_folder)

        if not exists_in(self.__index_folder):
            create_in(self.__index_folder, INDEX_SCHEMA)

        self.__index_write = open_dir(self.__index_folder).writer()


    def __index_dar(self, path):
        print '\tIndexing "%s"' % path
        archive.walk_doc_archive(path, self.__index_dar_html)


    def __index_dar_html(self, archive_name, file_name, file_len, data):
        lowered_name = file_name.lower()
        if lowered_name.endswith('.html') or lowered_name.endswith('.htm'):
            print '\tIndexing "%s:%s"' % (archive_name, file_name)
            parser = BeautifulSoup(data)
            title = u''
            if parser.title:
                title = parser.title.text
            content = title
            body = u''
            if parser.body:
                body = parser.body.getText(' ')
                content += ' ' + body
            url = unicode(archive_name[len(self.__doc_base):-4]) + '/' + file_name
            self.__index_write.add_document(title = title, content = content, body = body,
                category = self.__categories, url = url)


    def __index_html(self, path):
        print '\tIndexing "%s"' % path


    def index(self, path):
        if path.endswith('.dar'):
            self.__index_dar(path)
        elif path.endswith('.htm') or path.endswith('.html'):
            self.__index_html(path)

    def done(self):
        self.__index_write.commit()

