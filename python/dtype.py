import numpy
subhalo = numpy.dtype([
            ('x', 'f4'), 
            ('y', 'f4'), 
            ('pos', ('f4', 3)), 
            ('vel', ('f4', 3)), 
            ('size', 'f4'),
            ('groupid', 'u4'),
            ('iscentral', '?'),
            ('mass', 'f4'),
            ('sfr', 'f4'),
            ('bhmass', 'f4'),
            ('bhmdot', 'f4'),
            ('massbytype', ('f4', 6)), 
            ('lenbytype', ('u4', 6)), 
            ('vdisp', 'f4'),  
            ('vcirc', 'f4'),  
            ('rcirc', 'f4'),
            ('SDSS.i', 'f4'), ('SDSS.r', 'f4'), ('SDSS.g', 'f4'), ('SDSS.u', 'f4'), ('SDSS.z', 'f4'),
            ('FAKE.1500', 'f4'), ('FAKE.2000', 'f4'), ('FAKE.2500', 'f4'), 
            ('FAKE.Un', 'f4'), ('FAKE.V', 'f4'), ('FAKE.Vn', 'f4'), ('FAKE.Vw', 'f4'),
            ('GALEX.FUV', 'f4'), ('GALEX.NUV', 'f4'),
            ('UKIRT.WFCAM.H', 'f4'), ('UKIRT.WFCAM.J', 'f4'), ('UKIRT.WFCAM.K', 'f4'), ('UKIRT.WFCAM.Y', 'f4'),
            ])