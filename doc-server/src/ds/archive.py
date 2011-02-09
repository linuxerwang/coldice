# -*- coding: utf-8 -*-


import os
from os.path import exists
import struct
import zlib
from ds.lru import LRUCache


LRU_CACHE = LRUCache(10)


class DocArchive(object):
    def __init__(self, arch_path, statinfo):
        self.arch_path = arch_path
        self.load_time = statinfo.st_mtime
        self.index_file = ''

        self.indices   = {}

        fh = open(arch_path)
        try:
            header = fh.read(40)
            self.version = header[3:5]
            index_addr, file_count, index_file_addr = struct.unpack_from('<LLL', header, 7)

            fh.seek(index_addr, os.SEEK_SET)
            counter = 0
            for addr in range(file_count):
                counter += 1

                file_addr, file_len, file_name_len = struct.unpack('<LLL', fh.read(12))
                file_name = fh.read(file_name_len)
                self.indices[file_name] = (file_len, file_addr)

                if counter==index_file_addr:
                    self.index_file = file_name
        finally:
            if fh: fh.close()

    def contains(self, page_path):
        return page_path in self.indices

    def get_page(self, path):
        return Page(self.version, self.arch_path, *self.indices[path])


class Page(object):
    def __init__(self, version, arch_path, file_len, file_addr):
        if version=='01' or version=='02':
            self.chunk_size = 512*1024
        elif version=='03':
            self.chunk_size = 32*1024
        else:
            raise Exception('unknown doc archive version: "%s"' % version)

        self.arch_path = arch_path
        self.length = file_len
        self.file_addr = file_addr

    def __iter__(self):
        self.file_handle = open(self.arch_path)
        self.file_handle.seek(self.file_addr, os.SEEK_SET)
        self.chunks = self.length//self.chunk_size
        if self.length%self.chunk_size !=0:
            self.chunks += 1

        return self

    def next(self):
        self.chunks -= 1

        if self.chunks<0:
            try:
                self.file_handle.close()
            finally:
                raise StopIteration

        zlen, = struct.unpack('<L', self.file_handle.read(4))
        zbuffer = self.file_handle.read(zlen)

        return zlib.decompress(zbuffer)


def get_doc_archive(arch_path):
    if os.access(arch_path, os.F_OK) and exists(arch_path) and os.access(arch_path, os.R_OK):
        doc_archive = LRU_CACHE.get(arch_path)
        statinfo = os.stat(arch_path)
        if doc_archive and doc_archive.load_time < statinfo.st_mtime:
            doc_archive = None

        if not doc_archive:
            doc_archive = DocArchive(arch_path, statinfo)
            LRU_CACHE.put(arch_path, doc_archive)

        return doc_archive
    else:
        return None


import os.path


class ArchiveCreator(object):
    def __init__(self, archive_name, index_file=None):
        self.archive_name = archive_name
        self.index_file = index_file
        self.file_handle = open(archive_name, 'w')
        self.chunk_size = 32*1024

        self.index_addr = 0
        self.file_count = 0
        self.index_file_addr = 0

        self.header = [chr(0x00) for i in range(40)]
        self.header[0:5] = 'bar03'

        self.file_handle.write(''.join(self.header))

        self.entry_list = []

        self._couter = 0

    def _add_files(self, arg, dir_name, file_names):
        for file_name in file_names:
            file_path = file_name
            if dir_name:
                file_path = os.path.join(dir_name, file_name)

            if os.path.isdir(file_path):
                continue

            print 'Adding', file_path

            self._couter += 1
            if self.index_file==file_path:
                self.index_file_addr = self._couter

            self.file_handle.seek(0, os.SEEK_END)
            file_addr = self.file_handle.tell()
            fh = open(file_path)
            try:
                while True:
                    chunk = fh.read(self.chunk_size)

                    if len(chunk)==0: break

                    zbuffer = zlib.compress(chunk)

                    self.file_handle.write(struct.pack('<L', len(zbuffer)))
                    self.file_handle.write(zbuffer)
            finally:
                fh.close()

            statinfo = os.stat(file_path)
            file_len = statinfo.st_size
            self.entry_list.append((file_addr, file_len, file_path))

    def add_entry(self, entry):
        if os.access(entry, os.F_OK) and exists(entry):
            if os.access(entry, os.R_OK):
                if os.path.isdir(entry):
                    os.path.walk(entry, self._add_files, None)
                elif os.path.isfile(entry):
                    self._add_files(None, None, [entry])
                else:
                    print 'unknow entry type to "%s", ignore.' % entry
            else:
                print 'no access right to "%s", ignore.' % entry
        else:
            print 'entry "%s" does not exist, ignore.' % entry

    def commit(self):
        self.file_handle.seek(0, os.SEEK_END)
        self.index_addr = self.file_handle.tell()
        self.file_count = len(self.entry_list)

        for file_addr, file_len, file_name in self.entry_list:
            self.file_handle.write(struct.pack('<LLL', file_addr, file_len, len(file_name)))
            self.file_handle.write(file_name)

        self.header[7:19] = struct.pack('<LLL', self.index_addr, self.file_count, self.index_file_addr)
        self.file_handle.seek(0, os.SEEK_SET)
        self.file_handle.write(''.join(self.header))

        self.file_handle.close()


def extract_doc_archive(archive_name):
    output_folder = os.path.basename(archive_name) + '-extract'

    input_fh = open(archive_name)
    try:
        header = input_fh.read(40)

        version = header[3:5]
        if version=='01' or version=='02':
            chunk_size = 512*1024
        elif version=='03':
            chunk_size = 32*1024
        else:
            raise Exception('unknown doc archive version: "%s"' % version)

        index_addr, file_count, index_file_addr = struct.unpack_from('<LLL', header, 7)

        file_list = []

        input_fh.seek(index_addr, os.SEEK_SET)
        for addr in range(file_count):
            file_addr, file_len, file_name_len = struct.unpack('<LLL', input_fh.read(12))
            file_name = input_fh.read(file_name_len)
            file_list.append((file_name, file_len, file_addr))

        for file_name, file_len, file_addr in file_list:
            input_fh.seek(file_addr, os.SEEK_SET)

            chunks = file_len//chunk_size
            if file_len%chunk_size !=0:
                chunks += 1

            output_fh = None
            try:
                output_file = os.path.join(output_folder, file_name)
                output_dir = os.path.dirname(output_file)
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)

                output_fh = open(output_file, 'w')
                for i in range(chunks):
                    zlen, = struct.unpack('<L', input_fh.read(4))
                    zbuffer = input_fh.read(zlen)
                    output_fh.write(zlib.decompress(zbuffer))
            finally:
                if output_fh: output_fh.close()
    finally:
        if input_fh: input_fh.close()


def walk_doc_archive(archive_name, callback):
    input_fh = open(archive_name)
    try:
        header = input_fh.read(40)

        version = header[3:5]
        if version=='01' or version=='02':
            chunk_size = 512*1024
        elif version=='03':
            chunk_size = 32*1024
        else:
            raise Exception('unknown doc archive version: "%s"' % version)

        index_addr, file_count, index_file_addr = struct.unpack_from('<LLL', header, 7)

        file_list = []

        input_fh.seek(index_addr, os.SEEK_SET)
        for addr in range(file_count):
            file_addr, file_len, file_name_len = struct.unpack('<LLL', input_fh.read(12))
            file_name = input_fh.read(file_name_len)
            file_list.append((file_name, file_len, file_addr))

        for file_name, file_len, file_addr in file_list:
            input_fh.seek(file_addr, os.SEEK_SET)

            chunks = file_len // chunk_size
            if file_len%chunk_size !=0:
                chunks += 1

            file_body = []
            for i in range(chunks):
                zlen, = struct.unpack('<L', input_fh.read(4))
                file_body.append(zlib.decompress(input_fh.read(zlen)))

            callback(archive_name, file_name, file_len, ''.join(file_body))
    finally:
        if input_fh: input_fh.close()

