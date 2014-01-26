import numpy
from gaepsi.compiledbase.geometry import Cubenoid
import readsubhalo
import os
import os.path
from dirarray import dirarray

boxsize = 100000.0
M = numpy.matrix("2,1,1.;1,4,-2 ; 1,0,1").T
print M
cub = Cubenoid(M, [0, 0, 0], [boxsize, boxsize, boxsize],
        center=0, neworigin=0)
width = cub.newboxsize[1]
height = cub.newboxsize[0]
print cub.edges
from sys import argv

snapid = int(argv[1])
output = '../data/%03d' % snapid
ROOT = '../MB-IIa'

def main():
    print 'making data to', output
    snap = readsubhalo.SnapDir(snapid, ROOT)

    try: 
        os.mkdir(output)
    except OSError:
        pass
    metadata = numpy.empty(
        (),
    [('redshift', 'f8')])

    metadata['redshift'] = snap.redshift
    numpy.savez(os.path.join(output, 'metadata.npz'), metadata=metadata)

#    makegroup(snap)
#    makesubhalo(snap)
    updatesubhalo(snap)

def makegroup(snap):
    g = snap.readgroup()
    outarray = dirarray(os.path.join(output, 'group'), 
        dtype=[('x', 'f4'), 
            ('y', 'f4'), 
            ('mass', 'f4'), 
            ('Nsubhalo', 'u4'),
            ('firstsubhalo', 'u4'),
            ], shape=len(g), mode='w+')

    x, y, z = g['pos'].T.copy()
    cub.apply(x, y, z)
    outarray['y'] = x / width
    outarray['x'] = y / width
    outarray['mass'] = g['mass']
    outarray['Nsubhalo'] = g['nhalo']
    outarray['firstsubhalo'] = numpy.concatenate([[0], g['nhalo'].cumsum()])[:-1]
    print outarray[0]

def makesubhalo(snap):
    sub = snap.load('subhalo', 'tab')
    g = snap.readgroup()
    type = snap.load('subhalo', 'type')
    mask = ~numpy.isnan(sub['mass'])
    outarray = dirarray(os.path.join(output, 'subhalo'), 
        dtype=[('x', 'f4'), 
            ('y', 'f4'), 
            ('groupid', 'u4'),
            ('iscentral', '?'),
            ('mass', 'f4'),
            ('gasmass', 'f4'),
            ('darkmass', 'f4'),
            ('starmass', 'f4'),
            ('bhmass', 'f4'),
            ('rcirc', 'f4'),
            ('SDSS.i', 'f4'),
            ('SDSS.r', 'f4'),
            ('SDSS.g', 'f4'),
            ('SDSS.u', 'f4'),
            ('SDSS.z', 'f4'),
            ], shape=mask.sum(), mode='w+')

    massbytype = sub['massbytype'][mask]

    x, y, z = numpy.float32(sub['pos'].T)
    x = x[mask]
    y = y[mask]
    z = z[mask]
    cub.apply(x, y, z)
    outarray['x'] = y / width
    outarray['y'] = x / width
    outarray['mass'] = sub['mass'][mask]
    outarray['groupid'] = sub['groupid'][mask]
    outarray['iscentral'] = outarray['mass'] > 0.1 * g['mass'][outarray['groupid']]
    outarray['gasmass'] = massbytype[:, 0]
    outarray['darkmass'] = massbytype[:, 1]
    outarray['starmass'] = massbytype[:, 4]
    outarray['bhmass'] = massbytype[:, 5]
    outarray['rcirc'] = sub['rcirc'][mask]
    for s in 'irguz':
        data = snap.load('subhalo', 'RfFilter/SDSS.SDSS/%s' %s)
        outarray['SDSS.%s' %s] = data[mask]
    print sub['pos'][0]
    print outarray[0]
    print outarray.dtype

def updatesubhalo(snap):
    sub = snap.load('subhalo', 'tab')
    type = snap.load('subhalo', 'type')
    mask = type == 0
    g = snap.readgroup()
    outarray = dirarray(os.path.join(output, 'subhalo'), 
        dtype=[('x', 'f4'), 
            ('y', 'f4'), 
            ('groupid', 'u4'),
            ('iscentral', '?'),
            ('mass', 'f4'),
            ('gasmass', 'f4'),
            ('darkmass', 'f4'),
            ('starmass', 'f4'),
            ('bhmass', 'f4'),
            ('rcirc', 'f4'),
            ('SDSS.i', 'f4'),
            ('SDSS.r', 'f4'),
            ('SDSS.g', 'f4'),
            ('SDSS.u', 'f4'),
            ('SDSS.z', 'f4'),
            ], shape=mask.sum(), mode='r+')

    outarray['iscentral'] = outarray['mass'] > 0.1 * g['mass'][outarray['groupid']]

main()
