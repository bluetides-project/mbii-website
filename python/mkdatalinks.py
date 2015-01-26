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
    dirs = list(glob.glob(os.path.join(ROOT, '[0-9][0-9][0-9]')))
    dirs = sorted(dirs) 
    basenames = [os.path.basename(dir) for dir in dirs]
    redshifts = ['%05.2f' % getmeta(int(basename))['redshift'] 
            for basename in basenames]
    unique='abcdefghijk'
    redshifts = [
        redshift
        if redshifts.count(redshift) == 1 else 
        redshift + unique[redshifts[:i].count(redshift)]
        for i, redshift in enumerate(redshifts)
        ]
   
    with file(os.path.join(ROOT, 'snapshots.txt'), 'w') as logfile:
        for basename, redshift in zip(basenames, redshifts):
            dest = os.path.join(ROOT, 'by-snapid', basename);
            src = os.path.join('..', basename)
            symlinkf(src, dest)

            dest = os.path.join(ROOT, 'by-redshift', redshift);
            symlinkf(src, dest)
            logfile.write("%s %s\n" % (basename, redshift)) 

main() 
