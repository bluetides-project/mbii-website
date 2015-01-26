from bottle import route, run, abort, view, post, request, response, static_file, Bottle, template, redirect
import os.path
import numpy
import hashlib
import dtype

app = application = Bottle()

userdtype = numpy.dtype([
    ('email', 'S256'),
    ('ip', 'S20'),
    ('count', 'i8')])

ROOT = '/var/www/uwsgi/mbiiweb/www'

def auth(email):
    users = loadusers()
    user = finduser(users, email)
    if user is not None:
        user['count'] = user['count'] + 1
        user['ip'] = request['REMOTE_ADDR']
        saveusers(users)
        return True
    else:
        return False
def makeurl(path):
    return os.path.join(request.script_name, path)

def loadusers():
    try:
        users = numpy.loadtxt(os.path.join(ROOT, 'datausers.txt'), dtype=userdtype, ndmin=1)
        return users
    except:
        return numpy.empty(0, userdtype)

def saveusers(users):
    users.sort(order=['email'])
    try:
        numpy.savetxt(os.path.join(ROOT, 'datausers.txt'), users, fmt='%s %s %d')
    except:
        pass
def finduser(users, email):
    print users
    print email
    ind = users['email'].searchsorted(email)
    if ind < len(users) and users['email'][ind] == email:
        return users[ind]
    else:
        return None

@app.route('/hello')
def hello():
    return "Hello World!"

@app.get('/')
@app.get('/signup')
@app.get('/signup/<email:re:[^/]*>')
@view('datasignup.html')
def signup(email=''):
    return dict(protected=True, email=email, 
        error=None,
        signup=makeurl('signup')
        )

@app.get('/denied/<email:re:[^/]*>')
@view('datasignup.html')
def signup(email):
    return dict(protected=True, email=email, 
        error="Please submit a valid email address and accept the agreement.", 
        signup=makeurl('signup'))

@app.post('/signup')
@view('datasignup.html')
def signup():
    f = request.params
    email = f.get("email")
    agree = f.get("agree")
    users = loadusers()
    if agree != 'on':
        redirect(makeurl('denied/' + email))
    if finduser(users, email) is None:
        from validate_email import validate_email
        verify = validate_email(email)
        if not verify:
            redirect(makeurl('denied/' + email))
            return 
        users = numpy.append(users, numpy.empty(1, dtype=userdtype))
        
        users[-1]['email'] = email
        users[-1]['ip'] = request['REMOTE_ADDR']
        users[-1]['count'] = 0
        saveusers(users)

    redirect(makeurl('d/' + email))

    return dict(protected=False, email=email, 
        error=None, 
        signup=makeurl('signup'))
    

@app.get('/d/<email:re:[^/]*>')
def access(email):
    redirect(makeurl('d/' + email + '/'))

@app.get('/d/<email:re:[^/]*>/')
@view('dataaccess.html')
def access(email):
    if auth(email):
        redshifts = numpy.loadtxt(ROOT + '/../internal/snapshots.txt', dtype=[
            ('snapid', 'S8'), ('redshift', 'S8')])
        redshifts.sort(order='snapid')
        return dict(email=email,
            prefix=makeurl('d/' + email),
            signup=makeurl('signup'), 
            fields=[(f, str(dtype.subhalo[f]))
                for f in dtype.subhalo.names], 
            descr=dtype.subhalodescr,
            snapshots=redshifts)
    else:
        redirect(makeurl('denied/' + email))
        return
        
@app.get('/d/<email:re:[^/]*>/<path:path>')
def feed(email, path):
    if auth(email):
        response.headers['X-Accel-Redirect'] = '/internal/' + path
        response.headers['Content-Type'] = 'text/plain'
        return
    else:
        redirect(makeurl('denied/' + email))
        return

@app.route('/<filename:path>')
def server_static(filename):
    return static_file(filename, root='../www/')

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=8080, debug=True)


