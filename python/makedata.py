import numpy
from gaepsi.compiledbase.geometry import Cubenoid
import readsubhalo
import os
import os.path
from dirarray import dirarray
from dtype import subhalo as subhalodtype

boxsize = 100000.0
M = numpy.matrix("2,1,1.;1,4,-2 ; 1,0,1").T
print M
cub = Cubenoid(M, [0, 0, 0], [boxsize, boxsize, boxsize],
        center=0, neworigin=0)
width = cub.newboxsize[1]
height = cub.newboxsize[0]
print cub.newboxsize
from sys import argv

snapid = int(argv[1])
output = '../internal/%03d' % snapid
ROOT = '../MB-IIa'

def main():
    print 'making data to', output
    snap = readsubhalo.SnapDir(snapid, ROOT)
    update = len(argv) > 2 and argv[2] == "update"
    try: 
        os.mkdir(output)
    except OSError:
        pass
    metadata = numpy.empty(
        (),
    [('redshift', 'f8')])

    metadata['redshift'] = snap.redshift
    numpy.savez(os.path.join(output, 'metadata.npz'), metadata=metadata)

    makegroup(snap, update=update)
    makesubhalo(snap, update=update)

def makegroup(snap, update=False):
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
            ], shape=len(g), mode='r+' if update else 'w+')

    if not update:
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
    print outarray[0]

def makesubhalo(snap, update=False):
    sub = snap.load('subhalo', 'tab')
    g = snap.readgroup()
    type = snap.load('subhalo', 'type')
    sfr = snap.load('subhalo', 'sfr')
    bhmass = snap.load('subhalo', 'bhmass')
    bhmdot = snap.load('subhalo', 'bhmdot')

    mask = ~numpy.isnan(sub['mass'])
    outarray = dirarray(os.path.join(output, 'subhalo'), 
        dtype=subhalodtype, shape=mask.sum(), mode='r+' if update else 'w+')

    outarray['sfr'] = sfr[mask]
    outarray['bhmass'] = bhmass[mask]
    outarray['bhmdot'] = bhmdot[mask]
    if not update:
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
        outarray['rcirc'] = sub['rcirc'][mask]
        outarray['vcirc'] = sub['vcirc'][mask]
        outarray['vdisp'] = sub['vdisp'][mask]
        outarray['size'] = outarray['rcirc'] / width * 10
        for s in ['1500', '2000', '2500', 'Un', 'V', 'Vn', 'Vw']:
            data = snap.load('subhalo', 'RfFilter/FAKE.FAKE/%s' %s)
            outarray['FAKE.%s' %s] = data[mask]
        for s in ['FUV', 'NUV']:
            data = snap.load('subhalo', 'RfFilter/GALEX.GALEX/%s' %s)
            outarray['GALEX.%s' %s] = data[mask]
        for s in ['H', 'J', 'K', 'Y']:
            data = snap.load('subhalo', 'RfFilter/UKIRT.WFCAM/%s' %s)
            outarray['UKIRT.WFCAM.%s' %s] = data[mask]
        for s in 'irguz':
            data = snap.load('subhalo', 'RfFilter/SDSS.SDSS/%s' %s)
            outarray['SDSS.%s' %s] = data[mask]
    print sub['pos'][0]
    print outarray[0]
    print outarray.dtype


main()
