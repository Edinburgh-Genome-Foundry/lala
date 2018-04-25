import appdirs
import os

data_dir = appdirs.user_data_dir('lala', 'EGF')
conf = {
    'data_dir': data_dir,
    'geolite_url': "http://geolite.maxmind.com/download/"
                   "geoip/database/GeoLiteCity.dat.gz",
    'geolite_path': os.path.join(data_dir, 'GeoLiteCity.dat')
}
