# -*- coding: utf-8 -*-
from geopy.distance import vincenty
import requests


def search_suspect_place(lat, lng):
    ''' Return a dictonary containt information of a
        suspect place arround a given position.

        A suspect place is some company that match a suspect keyword
        in a Google Places search.

        input:
            - lat : latitude
            - lng : longitude

        output: closest_suspect_place:

            closest_suspect_place is a dict with the keys:
                - name : The name of suspect place
                - latitude : The latitude of suspect place
                - longitude : The longitude of suspect place
                - distance : The distance of suspect place and the given lat, lng
                - address : The address  of suspect place
                - phone : The phone of suspect place
                - id : The Google Place ID of suspect place
                - keyword : The Keyword that generate the place
                            in Google Place Search

    '''

    GOOGLE_PLACES_API_KEY = 'AIzaSyBl9nXOIiycM2JRRmdGof86vZuCwL_jJDM'

    suspect_keywords = ["Acompanhantes", "Motel",
                        "Adult Entertainment Club",
                        "Night Club",
                        "Sex Shop",
                        "Massagem",
                        "Swinger clubs"
                        "Sex Club",
                        "Gay Sauna",
                        "Strip Club"]

    # A string formating the entry.
    latlong = "{},{}".format(lat, lng)

    suspect_places = []

    # For each keyword append the closest result to suspect_places:
    for keyword in suspect_keywords:
        # Create the request for the Nearby Search Api
        # The Parameter rankby=distance will return a ordered list by
        # distance
        nearbysearch_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={}&keyword={}&rankby=distance&key={}".format(
            latlong, keyword, GOOGLE_PLACES_API_KEY)
        nearbysearch = requests.get(nearbysearch_url).json()

        # If have some result for this keywork, get first
        # result otherwise go to next keyword

        # TODO: CREATE DISTINCTS MESSAGES ERROS FOR THE API RESULTS
        if nearbysearch['status'] == 'OK':
            place = nearbysearch['results'][0]
        elif nearbysearch['status'] == 'ZERO_RESULTS':
            continue
        else:
            raise Exception("GooglePlacesAPIException:" +
                            nearbysearch['status'])

        # Parse the result information:
        suspect_place = {}
        suspect_place['id'] = place['place_id']
        suspect_place['keyword'] = keyword

        suspect_place['latitude'] = float(place['geometry']['location']['lat'])
        suspect_place['longitude'] = float(
            place['geometry']['location']['lng'])

        # Measure the distance between the result and the input location
        suspect_place['distance'] = vincenty(
            (lat, lng), (suspect_place['latitude'],
                         suspect_place['longitude'])).meters
        suspect_places.append(suspect_place)

    # Get the closest place inside all the searched keywords
    if suspect_places:
        closest_suspect_place = min(
            suspect_places, key=lambda x: x['distance'])
    else:
        # If all the keywords not returned results suspect_places is a empty list,
        # then return a empty dict, i.e, not suspect place found around.
        closest_suspect_place = {}
        closest_suspect_place['name'] = ""
        closest_suspect_place['distance'] = ""
        closest_suspect_place['phone'] = ""
        closest_suspect_place['latitude'] = ""
        closest_suspect_place['longitude'] = ""
        return closest_suspect_place

    # The Nearby Search Api not return details about the
    # address and phone in the results
    # For this we need to make another call for
    # Place Details API using the suspect closest_suspect_place[id].

    details_url = "https://maps.googleapis.com/maps/api/place/details/json?placeid={}&key={}".format(
        suspect_place['id'], GOOGLE_PLACES_API_KEY)

    details = requests.get(details_url).json()

    # Parse the results of the Place Details API .
    closest_suspect_place['name'] = details['result']['name']
    if 'formatted_phone_number' in details['result']:
        closest_suspect_place['address'] = details[
            'result']['formatted_address']
    else:
        closest_suspect_place['address'] = ""

    if "formatted_phone_number" in details['result']:
        closest_suspect_place['phone'] = details[
            'result']['formatted_phone_number']
    else:
        closest_suspect_place['phone'] = ""

    return closest_suspect_place