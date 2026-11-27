from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlsplit

import airportsdata
import folium
from geopy.distance import geodesic

AIRPORTS = airportsdata.load("IATA")
DESTINATIONS = ["BER", "BRE", "AMS", "CDG", "LHR", "CPH", "VIE", "PRG", "FCO", "BCN", "LIS"]

FORM = """
<h1>Weekend Escape Finder</h1>
<form>
    <label>Departure airport <input name="origin" placeholder="BER" required></label>
    <label>Maximum distance (km)
        <input name="distance" type="number" min="1" value="800" required>
    </label>
    <button>Find destinations</button>
</form>
"""


def find_destinations(origin, limit):
    airport = AIRPORTS[origin]
    start = (airport["lat"], airport["lon"])
    results = []

    for code in DESTINATIONS:
        if code == origin:
            continue
        airport = AIRPORTS[code]
        point = (airport["lat"], airport["lon"])
        distance = geodesic(start, point).km
        if distance <= limit:
            results.append((distance, code, point))

    results.sort()
    return start, results[:3]


class TravelApp(BaseHTTPRequestHandler):
    def do_GET(self):
        url = urlsplit(self.path)
        if url.path != "/":
            self.send_error(404)
            return

        page = FORM
        if url.query:
            fields = parse_qs(url.query)
            origin = fields.get("origin", [""])[0].strip().upper()
            distance = fields.get("distance", [""])[0]
            page += self.show_results(origin, distance)

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(page.encode("utf-8"))

    def show_results(self, origin, distance):
        if origin not in AIRPORTS:
            return "<p>Enter a valid airport code, such as BER.</p>"

        try:
            limit = int(distance)
        except ValueError:
            return "<p>Enter a whole number for the distance.</p>"

        if limit < 1:
            return "<p>Enter a distance of at least 1 km.</p>"

        start, results = find_destinations(origin, limit)
        if not results:
            return "<p>No destinations found within that distance.</p>"

        travel_map = folium.Map(location=start, zoom_start=5)
        folium.Marker(start, tooltip=origin).add_to(travel_map)
        points = [start]
        page = "<h2>Closest destinations</h2><p>Straight-line distances</p>"

        for distance, code, point in results:
            page += f"<p>{code}: {distance:.0f} km</p>"
            folium.Marker(point, tooltip=code).add_to(travel_map)
            points.append(point)

        travel_map.fit_bounds(points)
        return page + travel_map._repr_html_()


if __name__ == "__main__":
    with HTTPServer(("127.0.0.1", 1234), TravelApp) as server:
        print("Open http://localhost:1234")
        server.serve_forever()