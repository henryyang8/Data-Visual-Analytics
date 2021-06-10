# REFERENCE: https://github.com/kanishkan91/FAO-FBS-Data-Explorer/blob/master/app.py

import requests
from urllib.parse import urlencode, urlparse, parse_qsl
from flask import Flask, flash, redirect, render_template, request, session, abort,send_from_directory,send_file,jsonify
import json
import math as math


#1. Declare app
app= Flask(__name__)

GOOGLE_API_KEY = 'AIzaSyCXy1TpXWS-RcwfSBMp_RG6aSNEnd72tvg';
output = {}
 
@app.route('/')
def index():
    """Renders the index.html template"""
    # Renders the template (see the index.html template file for details). The
    # additional defines at the end (table, header, username) are the variables
    # handed to Jinja while it is processing the template.
    return render_template('index.html')

region_query = None

class GoogleMapsClient(object):
    lat = None
    lng = None
    data_type = 'json'
    location_query = None
    api_key = None
    name = None
    
    def __init__(self, api_key=None, address_or_postal_code=None, type = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if api_key == None:
            raise Exception("API key is required")
        self.api_key = api_key
        self.location_query = address_or_postal_code
        self.type = type;
        if self.location_query != None:
            self.extract_name()
            self.extract_lat_lng()
        
    def extract_lat_lng(self, location=None):
        global region_query
        loc_query = self.location_query
        if location != None:
            loc_query = location
        endpoint = f"https://maps.googleapis.com/maps/api/geocode/{self.data_type}"
        params = {"address": loc_query, "key": self.api_key, "region": region_query}
        url_params = urlencode(params)
        url = f"{endpoint}?{url_params}"
        r = requests.get(url)
        if r.status_code not in range(200, 299): 
            return {}
        latlng = {}
        try:
            latlng = r.json()['results'][0]['geometry']['location']
            for i in r.json()['results'][0]['address_components']:
                types = i['types']
                if types == ['country','political']:
                    region_query = i['short_name']
        except:
            pass
        lat,lng = latlng.get("lat"), latlng.get("lng")
        self.lat = lat
        self.lng = lng
        print(region_query)
        return lat, lng

    def extract_name(self, location=None):
        loc_query = self.location_query
        if location != None:
            loc_query = location
        endpoint = f"https://maps.googleapis.com/maps/api/place/textsearch/{self.data_type}"     
        params = {"query": loc_query, "key": self.api_key, "region": region_query}
        url_params = urlencode(params)
        url = f"{endpoint}?{url_params}"
        r = requests.get(url)
        if r.status_code not in range(200, 299): 
            return {}
        name=''
        try:
            name = r.json()['results'][0]['name']
        except:
            pass
        self.name = name
        return name

    def search(self, type=None, radius=5000, location=None):
        lat, lng = self.lat, self.lng
        if location != None:
            lat, lng = self.extract_lat_lng(location=location)
        endpoint = f"https://maps.googleapis.com/maps/api/place/nearbysearch/{self.data_type}"
        params = {
            "key": self.api_key,
            "location": f"{lat},{lng}",
            "radius": radius,
            "type": type 
        }
        params_encoded = urlencode(params)
        places_url = f"{endpoint}?{params_encoded}"
        r = requests.get(places_url)
        print(places_url)
        if r.status_code not in range(200, 299):
            return {}
        return r.json()

    def calc_distance(self, current_lat, current_lng, target_lat, target_lng):
        # find the Manhattan distance between two points given their long and lat
        # source: https://stackoverflow.com/questions/639695/how-to-convert-latitude-or-longitude-to-meters
        lat_diff = abs(target_lat - current_lat) * 111320
        lng_diff = abs((target_lng - current_lng) * 40075000 * math.cos(current_lat) / 360)
        return lat_diff + lng_diff

    def bayes(self, num_ratings, num_stars, confidence = 50, avg_rating = 3.25):
        return (confidence * avg_rating + num_ratings * num_stars)/(confidence + num_ratings)

    def dist_penalty(self, name, dist_required, bayes_score, user_radius = 200, minimum_radius = 10):
        dist_exceeded = max(dist_required - user_radius, 0)/3000
        penalty = math.e ** dist_exceeded
        if dist_required < minimum_radius:
            penalty = math.e ** 3
        return bayes_score / penalty

    def extract_features(self, location_dict, location=None):
        lat, lng = self.lat, self.lng
        if location != None:
            lat, lng = self.extract_lat_lng(location=location)
        required = ["name", "rating", "user_ratings_total"]
        location_dict = location_dict['results']
        extracted = []

        for loc in location_dict:
            if 'rating' in loc.keys():
                clean_dict = {i:v for i, v in loc.items() if i in required}
                clean_dict['lat'] = loc['geometry']['location']['lat']
                clean_dict['lng'] = loc['geometry']['location']['lng']
                clean_dict['dist'] = self.calc_distance(lat, lng, clean_dict['lat'], clean_dict['lng'])
                clean_dict['bayes'] = self.bayes(num_ratings = clean_dict['user_ratings_total'], num_stars = clean_dict['rating'])
                clean_dict['dist_adj_bayes'] = self.dist_penalty(clean_dict['name'], clean_dict['dist'], clean_dict['bayes'])
                extracted.append(clean_dict)
        res = sorted(extracted, key = lambda i:i['dist_adj_bayes'], reverse = True)
        #print(res)
        return res

    def get_five_children(place_name, type, radius=5000):
        print(place_name)
        print(type)
        parent=GoogleMapsClient(api_key=GOOGLE_API_KEY, address_or_postal_code=place_name)
        #print(parent)
        search_result=parent.search(type, radius)
        places=parent.extract_features(search_result)    
        # Returning the 5 places 
        five_places=[]
        if len(places)>5:
            l=5
        else:
            l=len(places)
        
        for i in range(l):
            place={}
            place['name']=places[i]['name']
            place['rating']=places[i]['rating']
            place['user_ratings_total']=places[i]['user_ratings_total']
            place['dist']=places[i]['dist']
            place['bayes']=places[i]['bayes']
            place['dist_adj_bayes']=places[i]['dist_adj_bayes']
            place['lat']=places[i]['lat']
            place['lng']=places[i]['lng']
            five_places.append(place)
        return five_places


@app.route("/get-data/<jsdata>")
def get_root(jsdata):
    split_array = jsdata.split("@");
    print(split_array)
    place = split_array[0];
    pref = split_array[1];
    root = GoogleMapsClient(api_key=GOOGLE_API_KEY, address_or_postal_code=place, type=pref)
    print(root.lat, root.lng, root.name)
    children=GoogleMapsClient.get_five_children(root.name, type=pref, radius=5000)
    #print(children)
    output['name']=root.name
    if root.lat == None and root.lng== None:
        output['lat'] = children[0]['lat']+0.001
        output['lng'] = children[0]['lng']+0.00
    else:
        output['lat'] = root.lat
        output['lng'] = root.lng
    output['children']=children
    return json.dumps(output)

@app.route("/get_children", methods=['GET', 'POST'])
def get_children():
    if request.method == 'POST':
        data = request.json
        #print("source ",data)
        children=GoogleMapsClient.get_five_children(data['source'], type="point_of_interest", radius=5000)
        output['name'] = data['source']
        output['all_children'] = children
        output['children'] = children
        #print("output ",output)
    return json.dumps(output)
    
@app.route('/map')
def vmd_timestamp():
    return render_template('map.html')

if __name__ == "__main__":
    app.run(threaded=True, port=5000)
    #app.run(debug=True)
