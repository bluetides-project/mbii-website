import numpy
from gaepsi.compiledbase.geometry import Cubenoid
import readsubhalo
import os
import os.path
from dirarray import dirarray
from dtype import subhalo as subhalodtype
from argparse import ArgumentParser

boxsize = 100000.0
M = numpy.matrix("2,1,1.;1,4,-2 ; 1,0,1").T
print M
cub = Cubenoid(M, [0, 0, 0], [boxsize, boxsize, boxsize],
        center=0, neworigin=0)
width = cub.newboxsize[1]
height = cub.newboxsize[0]
print cub.newboxsize
from sys import argv

parser = ArgumentParser()

parser.add_argument('--migrate', action='store_true')
parser.add_argument('--dry', action='store_true', 
        help="only check if any of the public dataset is bad")
parser.add_argument('--force', action='store_true', 
        help="force rewrite, do not check timestamp")
parser.add_argument('--private-dataset-root', default='../MB-IIa', required=False)
parser.add_argument('--public-dataset-root', default='../internal/', required=False)
parser.add_argument('snapid', nargs='*', type=int)

ROOT = '../MB-IIa'

args = parser.parse_args()

def isnewer(file1, otherfiles):
    
    oldest = min([os.path.getmtime(file) 
            if os.path.exists(file) else 0 
            for file in otherfiles])
    return os.path.getmtime(file1) > oldest

def main():
    for snapid in args.snapid:
        doone(snapid)
 
def doone(snapid):
    output = os.path.join(args.public_dataset_root, '%03d' % snapid)
    print 'making data to', output
    snap = readsubhalo.SnapDir(snapid, args.private_dataset_root)
    try: 
        os.mkdir(output)
    except OSError:
        pass
    metadata = numpy.empty(
        (),
    [('redshift', 'f8')])

    metadata['redshift'] = snap.redshift
    numpy.savez(os.path.join(output, 'metadata.npz'), metadata=metadata)

    makegroup(snap, output)
    makesubhalo(snap, output)

def necessary(reffilename, outarray, fields):
    if args.force:
        return True
    tooold = isnewer(reffilename, 
        [
            outarray.filename(field) 
            for field in fields]
        )
    return tooold
 
def makegroup(snap, output):
    g = snap.readgroup()
    outarray = dirarray(os.path.join(output, 'group'), 
        dtype=[('x', 'f4'), 
            ('y', 'f4'), 
            ('mass', 'f4'), 
            ('pos', ('f4', 3)), 
            ('massbytype', ('f4', 6)), 
            ('lenbytype', ('u4',6)), 
            ('Nsubhalo', 'u4'),
            ('firstsubhalo', 'u4'),
            ], shape=len(g), mode='r+')

    if necessary(snap.groupfile, outarray, ['x', 'y']):
        print 'converting tab'
        if not args.dry:
            x, y, z = g['pos'].T.copy()
            cub.apply(x, y, z)
            outarray['y'] = x / width
            outarray['x'] = y / width
        
            outarray['pos'] = g['pos']
            outarray['mass'] = g['mass']
            outarray['massbytype'] = g['massbytype']
            outarray['lenbytype'] = g['lenbytype']
            outarray['Nsubhalo'] = g['nhalo']
            outarray['firstsubhalo'] = numpy.concatenate([[0], g['nhalo'].cumsum()])[:-1]

def makesubhalo(snap, output):
    sub = snap.load('subhalo', 'tab')
    g = snap.readgroup()
    type = snap.load('subhalo', 'type')

    outarray = dirarray(os.path.join(output, 'subhalo'), 
        dtype=subhalodtype, shape=len(sub) - len(g), mode='r+')

    def getmask(s={}):
        if 'mask' not in s:
            s['mask'] = ~numpy.isnan(sub['mass'])
        return s['mask']

    if necessary(snap.subhalofile, outarray,
            ['x', 'y', 'lenbytype']):
        print 'converting tab'
        if not args.dry:
            mask = getmask()
            assert mask.sum() == len(outarray)
            outarray['vel'] = sub['vel'][mask]
            x, y, z = numpy.float32(sub['pos'].T)
            x = x[mask]
            y = y[mask]
            z = z[mask]
            cub.apply(x, y, z)
            outarray['x'] = y / width
            outarray['y'] = x / width
        
            outarray['pos'] = sub['pos'][mask]
            outarray['mass'] = sub['mass'][mask]
            outarray['groupid'] = sub['groupid'][mask]
            massbytype = sub['massbytype'][mask]
            outarray['iscentral'] = outarray['mass'] > 0.3 * g['mass'][outarray['groupid']]
            outarray['massbytype'] = massbytype
            outarray['lenbytype'] = sub['lenbytype'][mask]
            outarray['rcirc'] = sub['rcirc'][mask]
            outarray['vcirc'] = sub['vcirc'][mask]
            outarray['vdisp'] = sub['vdisp'][mask]
            outarray['size'] = outarray['rcirc'] / width * 10
    SRC = []
    DST = []
    for s in ['sfr', 'bhmass', 'bhmdot']:
        DST.append(s)
        SRC.append(s)

    for s in ['1500', '2000', '2500', 'Un', 'V', 'Vn', 'Vw']:
        DST.append('FAKE.%s' % s)
        SRC.append('RfFilter/FAKE.FAKE/%s' % s)

    for s in ['FUV', 'NUV']:
        DST.append('GALEX.%s' % s)
        SRC.append('RfFilter/GALEX.GALEX/%s' % s)
    for s in ['H', 'J', 'K', 'Y']:
        DST.append('UKIRT.WFCAM.%s' % s)
        SRC.append('RfFilter/UKIRT.WFCAM/%s' % s)

    for s in 'irguz':
        DST.append('SDSS.%s' % s)
        SRC.append('RfFilter/SDSS.SDSS/%s' % s)

    for src, dst in zip(SRC, DST):
        if necessary(snap.filename('subhalo', src), outarray, [dst]):
            print 'converting', src, 'to', dst
            if not args.dry:
                mask = getmask()
                outarray[dst] = snap.load('subhalo', src)[mask]


main()
