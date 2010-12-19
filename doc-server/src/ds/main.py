#!/usr/bin/python
# -*- coding: utf-8 -*-


import os
import sys
import threading

from SocketServer import ThreadingMixIn, TCPServer
from daemon import daemonize
from servlet import DocServlet


class DocServer(ThreadingMixIn, TCPServer):
    allow_reuse_address = True


def create_doc_archive(params):
    # check if file exists
    if os.path.exists(params['archive']):
        print 'Error: doc archive file "%s" already exists.' % params['archive']
        exit(0)

    # create doc archive
    import archive
    creator = archive.ArchiveCreator(params['archive'], params['index'])
    for source in params['sources']:
        creator.add_entry(source)
    creator.commit()


def extract_doc_archive(params):
    # extract doc archive
    import archive
    archive.extract_doc_archive(params['archive'])


def do_start_server(params, daemonized=True):
    import servlet
    servlet.DAEMONIZED  = daemonized
    if 'extension' in params:
        servlet.DOC_ARC_EXT = params['extension']
    servlet.HOME_FOLDER = os.path.abspath(params['directory'])
    server_address = (params['host'], params['port'])
    httpd = DocServer(server_address, DocServlet)
    httpd.serve_forever()


def start_server(params):
    # start server
    if 'port' not in params:
        params['port'] = 3456
    if 'host' not in params:
        params['host'] = ''

    if params['daemon']:
        # daemonize
        daemonize(do_start_server, params)
    else:
        do_start_server(params, False)


def stop_server(params):
    # TODO: stop server
    pass


ACTIONS = {
    'create' : create_doc_archive,
    'extract': extract_doc_archive,
    'start'  : start_server,
    'stop'   : stop_server,
}


def extract_command(arguments):
    if len(arguments)==0: raise Exception('unknown command')

    i = -1
    cmd = ''
    params = {'sources':[], 'daemon':True, 'host':'localhost'}

    while True:
        i = i+1
        if i>=len(arguments): break
        if arguments[i].startswith('-'):
            if arguments[i]=='-c':
                cmd = 'create'
                if i<len(arguments)-1:
                    i = i+1
                    params['archive'] = arguments[i]
                else:
                    raise Exception('-c without archive given')
            elif arguments[i]=='-x':
                cmd = 'extract'
                if i<len(arguments)-1:
                    i = i+1
                    params['archive'] = arguments[i]
                else:
                    raise Exception('-x without archive given')
            elif arguments[i]=='-p':
                if i<len(arguments)-1:
                    try:
                        i = i+1
                        params['port'] = int(arguments[i])
                    except:
                        raise Exception('wrong port number')
                else:
                    raise Exception('-p without port given')
            elif arguments[i]=='-index':
                if i<len(arguments)-1:
                    i = i+1
                    params['index'] = arguments[i]
                else:
                    raise Exception('-index without index given')
            elif arguments[i]=='-d':
                if i<len(arguments)-1:
                    i = i+1
                    params['directory'] = os.path.abspath(arguments[i])
                else:
                    raise Exception('-index without directory given')
            elif arguments[i]=='-ext':
                if i<len(arguments)-1:
                    i = i+1
                    params['extension'] = arguments[i]
                else:
                    raise Exception('-ext without extension')
            elif arguments[i]=='-h':
                if i<len(arguments)-1:
                    i = i+1
                    params['host'] = arguments[i]
                else:
                    raise Exception('-h without host given')
            elif arguments[i]=='-nodaemon':
                params['daemon'] = False
            else:
                raise Exception('unknow switch "%s"' % arguments[i])
        else:
            if arguments[i]=='start':
                if cmd not in ('create', 'extract', 'stop'):
                    cmd = 'start'
                    if 'directory' not in params:
                        raise Exception('directory is required for starting server')
                else:
                    raise Exception('command conflict: "%s" and "start"' % cmd)
            elif arguments[i]=='stop':
                if cmd not in ('create', 'extract', 'start'):
                    cmd = 'stop'
                else:
                    raise Exception('command conflict: "%s" and "stop"' % cmd)
            else:
                params['sources'].append(arguments[i])

    if cmd=='':
        raise Exception('unknown command')
    elif cmd=='create':
        if len(params['sources'])==0:
            raise Exception('no source listed')
        elif 'archive' not in params:
            raise Exception('-c without archive given')

        if 'index' not in params:
            params['index'] = None
    elif cmd=='extract':
        if 'archive' not in params:
            raise Exception('-x without archive given')

    return cmd, params


def print_help():
    print 'Usage:'
    print '    python docserver.py -c foo.bar [-index index.html] images scripts *.html'
    print '    python docserver.py -x foo.bar'
    print '    python docserver.py [-p 3456] [-h localhost] [-ext dar] [-nodaemon] -d /opt/docserver start'
    print '    python docserver.py [-p 3456] stop'


def main():
    try:
        cmd, params = extract_command(sys.argv[1:])
    except Exception, e:
        print 'Error:', e
        print_help()
        exit(0)

    ACTIONS[cmd](params)

