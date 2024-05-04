from flask import Flask, jsonify
from flask_cors import CORS
from geopy.geocoders import Photon
from geopy.exc import GeocoderTimedOut, GeocoderInsufficientPrivileges

app = Flask(__name__)
CORS(app)

@app.route('/location')
def get_location():
    try:
        # Use geopy to retrieve geolocation based on IP address
        geolocator = Photon(user_agent="measurements")
        location = geolocator.geocode("172.26.165.246")
        if location:
            return jsonify({'latitude': location.latitude, 'longitude': location.longitude})
        else:
            return jsonify({'error': 'Location not found'}), 404
    except GeocoderTimedOut:
        return jsonify({'error': 'Geocoder service timed out'}), 500
    except GeocoderInsufficientPrivileges:
        return jsonify({'error': 'Insufficient privileges to access geocoding service'}), 403

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)