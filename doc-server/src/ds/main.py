#!/usr/bin/python
# -*- coding: utf-8 -*-


import os
import sys
import threading

from SocketServer import ThreadingMixIn, TCPServer
from daemon import daemonize
from optparse import OptionParser
from indexing import SearchIndexer
from servlet import DocServlet


class DocServer(ThreadingMixIn, TCPServer):
    allow_reuse_address = True


def create_doc_archive(archive_file, index_file, source_files):
    if not source_files:
        print 'Error, no source files given.'
        exit(1)

    # check if file exists
    if os.path.exists(archive_file):
        print 'Error: doc archive file "%s" already exists.' % archive_file
        exit(1)

    # create doc archive
    import archive
    creator = archive.ArchiveCreator(archive_file, index_file)
    for source in source_files:
        creator.add_entry(source)
    creator.commit()


def extract_doc_archive(archive_file):
    # check if file exists
    if not os.path.exists(archive_file):
        print 'Error: doc archive file "%s" does not exist.' % archive_file
        exit(1)

    # extract doc archive
    import archive
    archive.extract_doc_archive(archive_file)


def walk_and_index(doc_base, sources):
    print 'indexing ......'
    indexer = SearchIndexer(os.path.abspath(doc_base))
    try:
        for source in sources:
            source = os.path.abspath(source)
            if os.path.isdir(source):
                for root, dirs, files in os.walk(source):
                    for one_file in files:
                        indexer.index(os.path.join(root, one_file))
            else:
                indexer.index(source)
    finally:
        indexer.done()


def do_start_server(params):
    directory, host, port, ext, daemon = params
    import servlet
    servlet.DAEMONIZED  = daemon
    if ext:
        servlet.DOC_ARC_EXT = ext
    servlet.HOME_FOLDER = os.path.abspath(directory)
    server_address = (host, port)
    httpd = DocServer(server_address, DocServlet)
    httpd.serve_forever()


def start_server(directory, host, port, ext, daemon):
    if daemon:
        # daemonize
        daemonize(do_start_server, (directory, host, port, ext, daemon))
    else:
        # interactive
        do_start_server((directory, host, port, ext, daemon))


def stop_server():
    # TODO: stop server
    print '"stop" has not been implemented yet.'


def main():
    usage = '''%prog [options] [start|stop]

Examples:
    python docserver.py -c foo.bar [--index=index.html] images scripts *.html
    python docserver.py -x foo.bar
    python docserver.py -w /opt/docserver path-to-doc-folder | foo.bar
    python docserver.py [-p 3456] [-h localhost] [-ext dar] [-nodaemon] -d /opt/docserver start
    python docserver.py [-p 3456] stop
'''
    parser = OptionParser(usage)
    parser.add_option('-c', '--create', dest='create_file',
        help='Create a docserver archive file.')
    parser.add_option('-d', '--directory', dest='directory',
        help='Directory of docserver archive files.')
    parser.add_option('-e', '--ext', dest='extension', default='dar',
        help='Extension of archive file.')
    parser.add_option('-H', '--host', dest='host', default='',
        help='Host name.')
    parser.add_option('-i', '--index', dest='index_file', help='Index file.')
    parser.add_option('-n', '--nodaemon', dest='daemon', action='store_false', default=True,
        help='Run as an interactive program.')
    parser.add_option('-p', '--port', dest='port', type=int, default=3456,
        help='Port number.')
    parser.add_option('-w', '--walk', dest='walk_index',
        help='Walk and create reverse index.')
    parser.add_option('-x', '--extract', dest='extract_file',
        help='Extract a docserver archive file.')
    (options, args) = parser.parse_args()

    cmd_num = 0
    if options.create_file:
        cmd_num += 1
    if options.extract_file:
        cmd_num += 1
    if options.walk_index:
        cmd_num += 1

    if cmd_num > 1:
        parser.error('options -c, -e, and -w are mutually exclusive')
    elif options.create_file:
        create_doc_archive(options.create_file, options.index_file, args)
    elif options.extract_file:
        extract_doc_archive(options.extract_file)
    elif options.walk_index:
        walk_and_index(options.walk_index, args)
    else:
        if len(args) != 1 or (args[0] != 'start' and args[0] != 'stop'):
            parser.error('Command "start" or "stop" is required.')
        if args[0] == 'start':
            if not options.directory:
                parser.error('option -d is required.')
            start_server(options.directory, options.host, options.port, options.extension,
                options.daemon)
        else:
            stop_server()

