# reading dir like a numpy record array
import os.path
import os
import numpy

class dirarray(object):
    def __init__(self, path, shape=None, dtype=None, mode='r+'):
        self.mode = mode
        if shape is None and dtype is None:
            self._open(path)
        else:
            self._create(path, shape, dtype)

    def _open(self, path):
        metafile = os.path.join(path, '_meta.npz')
        meta = numpy.load(metafile)
        self.dtype = meta['dummy'].dtype     
        self.shape = meta['shape']

        self.path = path
        self.cache = {}

    def _create(self, path, shape, dtype):
        try:
            os.mkdir(path)
        except OSError:
            pass
        self.migrate(path, shape, dtype)

    def migrate(self, path, shape, dtype):
        """ migrate the scheme in path to the given dtype and shape"""
        metafile = os.path.join(path, '_meta.npz')
        dummy = numpy.empty((), dtype=dtype)
        numpy.savez(metafile, dummy=dummy, shape=shape)
        self._open(path)

    def filename(self, key):
        return os.path.join(self.path, key)

    def _openfield(self, key, mode, shape):
        if key not in self.dtype.names:
            raise KeyError("%s not found in dtype" % key)
        # create a new file in r+ mode if it doesn't exist.
        path = self.filename(key)
        if not os.path.exists(path) and mode == 'r+':
            mode = 'w+'

        return numpy.memmap(path, 
                  mode=mode, 
                  dtype=self.dtype[key], shape=shape)

    def __len__(self):
        return self.shape

    def __getitem__(self, key):
        """ always returns a copy if key is numpy array indexing.
            always returns a reference if key is a string indexing.
        """
        if isinstance(key, basestring):
            if key not in self.dtype.names:
                raise KeyError("%s not found in dtype" % key)
            if key not in self.cache:
                arr = self._openfield(key, self.mode, shape=self.shape)
                self.cache[key] = arr

            return self.cache[key]
        else:
            if isinstance(key, slice):
                start, end, step = key.indices(len(self))
                l = (end - start) // step
            else:
                key = numpy.asarray(key)
                if key.dtype == numpy.dtype('?'):
                    l = key.sum()
                else:
                    l = key.shape

            rt = numpy.empty(l, dtype=self.dtype)
            for field in self.dtype.names:
                rt[field][...] = self[field][key]
            return rt

    def __setitem__(self, key, value):
        if isinstance(key, basestring):
            item = self[key]
            item[...] = value
        else:
            for field in self.dtype.names:
                self[field][key] = value[field]

    def __str__(self):
        return '%s * %s' % (str(self.dtype), self.shape)

def main():
    a = dirarray(shape=10, 
            dtype=[('f1', 'f4'), ('f2', 'f4')], 
            path='test', mode='w+')
    a['f1'][2:4] = 3
    print a['f1']
    print a['f2']

    a = dirarray(path='test', mode='r+')
    print a
    print a[2:4]['f2']
if __name__ == '__main__':
    main()
