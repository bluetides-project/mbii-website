Accessing MassiveBlack-II data.

1. First, did you agree to the User Agreement and provide your email address yet?

    If not so, please read http://mbii.phys.cmu.edu/data/. 
    Please acknowledge the MassiveBlack-II simulation if the data is used 
    in published works.

2. Directory strcture.

    You can access the snapshots either by-redshift or by-snapid.
    Redshift decreases with time; snap-id increases with time.
 
    Each snapshot is contained in one directory.

    "metadata.npz" contains the redshift of the snapshot.

    There are two sub-directories: "Group" and "Subhalo".

    Group contains the group properties.
    Subhalo contains the subhalo properties. 

    Each property is stored in one binary file.

3. You can mirror the data to your own local server with:

   lftp -c mirror http://mbii.phys.cmu.edu/data/by-redshift/ MB-II

3. The easiest way to use snapshots is to access them with the provided
    dirarray.py python module.

    wget http://mbii.phys.cmu.edu/data/dirarray.py

    then, (assuming ROOT is where the data is synced)

    from dirarray import dirarray
    def getgroup(snap):
        return dirarray(os.path.join(ROOT, snap, 'group'), mode='r')
    def getsubhalo(snap):
        return dirarray(os.path.join(ROOT, snap, 'subhalo'), mode='r')

    g0006 = getgroup('00.06')
    s0006 = getsubhalo('00.06')

    The type of the properties are stored in _meta.npz in each directory.
  
    Here is the list of subhalo properties:

    ('x', 'f4'), # visualization x coordinate
    ('y', 'f4'), # visualization y coordinate
    ('size', 'f4'), # visualization size
    ('pos', ('f4', 3)),  # position in the simulation Kpc/h
    ('vel', ('f4', 3)),  # peculiar velocity in the simulation km/s
    ('groupid', 'u4'),   # group that owns this subhalo
    ('iscentral', '?'),  # if the mass >= 40% of the host group
    ('mass', 'f4'),      # total mass 1e10 Msun/h
    ('massbytype', ('f4', 6)),  # mass per species 1e10 Msun/h
    ('lenbytype', ('u4', 6)),   # number of particles per species
    ('vdisp', 'f4'),    # velocity dispersion km/s
    ('vcirc', 'f4'),    # max circular velocity in km/s
    ('rcirc', 'f4'),    # radius of max circular velocity in km/s

    # These are Rest Frame filter luminosities in 1e28 ergs/Hz/s/h:

    ('SDSS.i', 'f4'), ('SDSS.r', 'f4'), ('SDSS.g', 'f4'), ('SDSS.u', 'f4'), ('SDSS.z', 'f4'),
    ('GALEX.FUV', 'f4'), ('GALEX.NUV', 'f4'),
    ('UKIRT.WFCAM.H', 'f4'), ('UKIRT.WFCAM.J', 'f4'), ('UKIRT.WFCAM.K', 'f4'), ('UKIRT.WFCAM.Y', 'f4'),
    ('FAKE.1500', 'f4'), ('FAKE.2000', 'f4'), ('FAKE.2500', 'f4'), 
    ('FAKE.Un', 'f4'), ('FAKE.V', 'f4'), ('FAKE.Vn', 'f4'), ('FAKE.Vw', 'f4'),
 
