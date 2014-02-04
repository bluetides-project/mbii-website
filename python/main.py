from bottle import route, run, abort, view, post, request, response, static_file, Bottle, template
import numpy
from dirarray import dirarray
import os.path


app = application = Bottle()

ROOT = '/var/www/uwsgi/mbiiweb/data'
BOXSIZE = numpy.array([244948.94607753,  428174.36999344 ])

def getmeta(snapid):
    meta = numpy.load(os.path.join(ROOT, '%03d' % snapid, 'metadata.npz'))
    return meta['metadata']

def getgroup(snapid):
    return dirarray(os.path.join(ROOT, '%03d' % snapid, 'group'), mode='r')
def getsubhalo(snapid):
    return dirarray(os.path.join(ROOT, '%03d' % snapid, 'subhalo'), mode='r')

@app.route('/hello')
def hello():
    return "Hello World!"

@app.route('/snap/<snapid:int>')
def snap(snapid):
    meta = getmeta(snapid)
    return dict(redshift=float(meta['redshift']))

@app.route('/<mime:re:(html|json)>/<snapid:int>/group/<gid:int>')
def group(mime, snapid, gid):
    tab = getgroup(snapid)
    if gid >= len(tab) or gid < 0:
        return abort(404, "Group %d not found in snapid %d" % (gid, snapid))
    return template('group.%s' % mime, groups=[tab[gid]], id=[gid])

@app.route('/<mime:re:(html|json)>/<snapid:int>/group/<gid:int>/subhalo/<sid:int>')
def subhaloingroup(mime, snapid, gid, sid):
    tab = getgroup(snapid)
    if gid >= len(tab) or gid < 0:
        return abort(404, "Group %d not found in snapid %d" % (gid, snapid))
    first = tab[gid]['firstsubhalo']
    nhalo = tab[gid]['Nsubhalo']
    if sid < 0 or sid >= nhalo:
        return abort(404, "Subhalo %d / %d not found in snapid %d" % (gid, sid, snapid))
        
    tab = getsubhalo(snapid)
    sel = tab[first + sid]
    return template('subhalo.%s' % mime, subhalos=[sel], id=[first + sid])

@app.route('/<mime:re:(html|json)>/<snapid:int>/subhalo/<sid:int>')
@view('subhalo.html')
def subhalo(mime, snapid, sid):
    tab = getsubhalo(snapid)
    if sid >= len(tab) or sid < 0:
        return abort(404, "Subhalo %d not found in snapid %d" % (sid,
snapid))
    return template('subhalo.%s' % mime, subhalos=[tab[sid]], id=[sid])

@app.get('/search/<snapid:int>/<type:re:(group|subhalo)>')
@view('search.html')
def search(snapid, type):
    return dict(snapid=snapid, type=type)

def makeselection(snapid, type, f):
    if type == 'group':
        tab = getgroup(snapid)
    else:
        tab = getsubhalo(snapid)
    xmin = numpy.float64(f.get('xmin')) 
    ymin = numpy.float64(f.get('ymin'))
    xmax = numpy.float64(f.get('xmax'))
    ymax = numpy.float64(f.get('ymax'))
    MassMin = numpy.float64(f.get('MassMin'))
    
    x = tab['x']
    y = tab['y']

    mask = numpy.ones_like(x, dtype='?')
    mask &= x >= xmin
    mask &= x <= xmax
    mask &= y >= ymin
    mask &= y <= ymax

    mask0 = tab['mass'] > MassMin
    mask &= mask0

    print 'massmin = ', MassMin
    print 'mass0', mask0.sum(), 'mask', mask.sum()
    return mask.nonzero()[0], tab[mask]

@app.post('/search/<snapid:int>/<type:re:(group|subhalo)>')
def do_search(snapid, type):
    response.content_type = 'application/json'
    response.headers['Access-Control-Allow-Origin'] = '*'
    f = request.params
    Nmax = numpy.int(f.get('Nmax'))
    
    id, sel = makeselection(snapid, type, f)
    mass = sel['mass']
    arg = mass.argsort()[::-1][:Nmax]
    sel = sel[arg]
    id = id[arg]
    if type == 'group':
        return template('group.json', groups=sel, id=id)
    else:
        return template('subhalo.json', subhalos=sel, id=id)

@app.route('/<filename:path>')
def server_static(filename):
    return static_file(filename, root='/var/www/uwsgi/mbiiweb/www/')

#@app.route('/')
#def server_static():
#    return static_file('index.html', root='/var/www/uwsgi/mbiiweb/www/')

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=8080, debug=True)


