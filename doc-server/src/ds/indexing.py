#!/usr/bin/python
# -*- coding: utf-8 -*-

import archive
import os
import re
from whoosh.index import create_in, exists_in, open_dir
from BeautifulSoup import BeautifulSoup, Comment
from ds import INDEX_SCHEMA


IGNORE_TAGS = set([
    'meta',
    'link',
    'script',
    'style',
])

H_TAGS = set(['h1', 'h2', 'h3', 'h4', 'h5'])


class HTMLExtractor(object):
    def __init__(self, data, url):
        self.__parser = BeautifulSoup(data)
        self.__url = url

        # remove all comments
        comments = self.__parser.findAll(text=lambda text:isinstance(text, Comment))
        [comment.extract() for comment in comments]
        # remove all those tags
        for tag in ('script', 'a'):
            [one.extract() for one in self.__parser.findAll(tag)]


    def __cleanup(self, text):
        return re.sub('\s{2,}|-|\|', ' ', text)


    def extract(self):
        path = self.__url.replace('/', ' ').replace('.', ' ')
        info = {
            'url' : self.__url, 'path' : path, 'refer' : 0, 'referred' : 0,
            'h1' : u'', 'h2' : u'', 'h3' : u'', 'h4' : u'', 'h5' : u'',
            'title' : u'', 'content' : u'',
        }

        for tag in H_TAGS:
            for one in self.__parser.findAll(tag):
                info[tag] += ' ' + one.text
                one.extract()

        if self.__parser.title:
            info['title'] = self.__cleanup(self.__parser.title.text)
        if self.__parser.body:
            info['content'] = self.__cleanup(self.__parser.body.getText(' '))

        return info


class SearchIndexer(object):
    def __init__(self, doc_base):
        self.__doc_base = doc_base
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
            url = unicode(archive_name[len(self.__doc_base):-4]) + '/' + file_name
            extractor = HTMLExtractor(data, url)
            info_map = extractor.extract()
            self.__index_write.add_document(**info_map)


    def __index_html(self, path):
        print '\tIndexing "%s"' % path


    def index(self, path):
        if path.endswith('.dar'):
            self.__index_dar(path)
        elif path.endswith('.htm') or path.endswith('.html'):
            self.__index_html(path)

    def done(self):
        self.__index_write.commit(optimize=True)

