import numpy
import dirarray
import os.path
import os
import glob
ROOT = '/var/www/uwsgi/mbiiweb/internal'

def getmeta(snapid):
    meta = numpy.load(os.path.join(ROOT, '%03d' % snapid, 'metadata.npz'))
    return meta['metadata']

def symlinkf(src, dest):
    try:
        os.unlink(dest);
    except OSError as e:
        pass
    os.symlink(src, dest);

def main():
    for dir in glob.glob(os.path.join(ROOT, '[0-9][0-9][0-9]')):
        basename = os.path.basename(dir)
        dest = os.path.join(ROOT, 'by-snapid', basename);
        src = os.path.join('..', basename)
        symlinkf(src, dest)

        meta = getmeta(int(basename))
        dest = os.path.join(ROOT, 'by-redshift', '%05.2f' % meta['redshift']);
        symlinkf(src, dest)
        
main() 
