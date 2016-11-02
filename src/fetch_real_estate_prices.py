## pegar as coordenadas dos quadrantes
## pegar a informação de todos os quadrantes da área (possivelmente brasilia)
## juntar todos os IDs retornados e pegar os detalhes de cada imovel

## import geocoder

## def main():
##     geo_location = geocoder.google("Distrito Federal, Brasil")
##     location_boundingbox = geolocation.bbox
import numpy as np

# bbox = {'northeast': [-15.5001711, -47.3081926],
#        'southwest': [-16.0517623, -48.2870948]}

def slice_quadrants(northeast, southwest, size=0.125):
    quadrants = []
    for lat in np.arange(southwest[0], northeast[0], size):
        for long in np.arange(southwest[1], northeast[1], size):
            quadrant = ((lat, long), (lat + size, long + size))
            quadrants.append(quadrant)
    return quadrants

if __name__ == '__main__':
    from unittest import TestCase

    t = TestCase()
    northeast, southwest = [-15, -47], [-16, -48]

    t.assertEqual(type(slice_quadrants(northeast, southwest)), list)
    t.assertEqual(type(slice_quadrants(northeast, southwest)[0]), tuple)
    t.assertEqual(slice_quadrants(northeast, southwest)[0], ((-16.0, -48.0),(-15.875,-47.875)))
    t.assertEqual(slice_quadrants(northeast, southwest)[1], ((-16.0, -47.875),(-15.875,-47.75)))
    t.assertEqual(slice_quadrants(northeast, southwest)[8], ((-15.875, -48.0),(-15.75,-47.875)))
    t.assertEqual(slice_quadrants(northeast, southwest)[-1], ((-15.125, -47.125),(-15.0,-47.0)))
