import os
import urllib.request
import urllib.parse
import json
import argparse

def geocode_address(address: str, api_key: str = None) -> tuple[float, float]:
    """Geocodes an address string to (latitude, longitude) using Google Maps Geocoding API
    with a fallback to OpenStreetMap Nominatim.
    """
    # 1. Try Google Maps Geocoding API if key is available
    if api_key and api_key != "YOUR_API_KEY_HERE":
        url = f"https://maps.googleapis.com/maps/api/geocode/json?address={urllib.parse.quote(address)}&key={api_key}"
        try:
            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read().decode())
                if data.get("status") == "OK" and data.get("results"):
                    loc = data["results"][0]["geometry"]["location"]
                    print(f"Geocoded '{address}' via Google: {loc['lat']}, {loc['lng']}")
                    return loc["lat"], loc["lng"]
                else:
                    print(f"Google Geocoding status: {data.get('status')}. Trying fallback...")
        except Exception as e:
            print(f"Google Geocoding error: {e}. Trying fallback...")

    # 2. Fallback to OpenStreetMap Nominatim
    url = f"https://nominatim.openstreetmap.org/search?format=json&limit=1&q={urllib.parse.quote(address)}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "amkroofing-solar-cache/1.0 (amkroofing@amkroofing.com)"}
    )
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            if data:
                lat = float(data[0]["lat"])
                lng = float(data[0]["lon"])
                print(f"Geocoded '{address}' via Nominatim: {lat}, {lng}")
                return lat, lng
            else:
                print(f"Nominatim Geocoding found no results for '{address}'")
    except Exception as e:
        print(f"Nominatim Geocoding error: {e}")

    return None, None

def get_solar_insights(api_key: str, lat: float, lng: float):
    from google.maps import solar_v1
    from google.api_core.client_options import ClientOptions

    # 1. Configure the client with your API key
    client_options = ClientOptions(api_key=api_key)
    client = solar_v1.SolarClient(client_options=client_options)

    # 2. Construct the request
    # You can specify HIGH, MEDIUM, or LOW for the required imagery quality.
    request = solar_v1.FindClosestBuildingInsightsRequest(
        location={"latitude": lat, "longitude": lng},
        required_quality=solar_v1.ImageryQuality.HIGH
    )

    # 3. Make the API call
    try:
        response = client.find_closest_building_insights(request=request)
        
        # 4. Extract and print useful data
        print(f"Resource Name: {response.name}")
        print(f"Max Array Panels: {response.solar_potential.max_array_panels_count}")
        print(f"Max Array Area (sq meters): {response.solar_potential.max_array_area_meters2}")
        
        return response
        
    except Exception as e:
        print(f"An error occurred: {e}")

def get_val(obj, path, default=None):
    """Safely gets value from a nested object (dict or class instance) using a dot-separated path."""
    curr = obj
    for key in path.split('.'):
        if curr is None:
            return default
        if isinstance(curr, dict):
            curr = curr.get(key)
        else:
            curr = getattr(curr, key, None)
    return curr if curr is not None else default

def download_satellite_with_polygons(api_key: str, lat: float, lng: float, insights, file_name: str = "roof_scan_polygons.png"):
    """
    Downloads a satellite image of the location from Google Maps Static API,
    overlaying the building bounding box and roof segment polygons.
    """
    # Base URL for the Google Maps Static API
    url = "https://maps.googleapis.com/maps/api/staticmap"
    
    # Start params
    params = [
        ("center", f"{lat},{lng}"),
        ("zoom", "20"),
        ("size", "600x600"),
        ("maptype", "satellite"),
        ("key", api_key),
        ("scale", "2")
    ]
    
    # 1. Add Building Bounding Box path if available
    sw_lat = get_val(insights, "bounding_box.sw.latitude")
    sw_lng = get_val(insights, "bounding_box.sw.longitude")
    ne_lat = get_val(insights, "bounding_box.ne.latitude")
    ne_lng = get_val(insights, "bounding_box.ne.longitude")
    
    if all(v is not None for v in [sw_lat, sw_lng, ne_lat, ne_lng]):
        # Coordinates in order: SW -> SE -> NE -> NW -> SW (closed loop)
        coords_str = (
            f"{sw_lat},{sw_lng}|"
            f"{sw_lat},{ne_lng}|"
            f"{ne_lat},{ne_lng}|"
            f"{ne_lat},{sw_lng}|"
            f"{sw_lat},{sw_lng}"
        )
        # Red outline, semi-transparent red fill
        params.append(("path", f"color:0xff0000ff|fillcolor:0xff000018|weight:3|{coords_str}"))

    # 2. Add Roof Segments if available
    roof_segments = get_val(insights, "solar_potential.roof_segment_stats", [])
    for segment in roof_segments:
        sw_lat_s = get_val(segment, "bounding_box.sw.latitude")
        sw_lng_s = get_val(segment, "bounding_box.sw.longitude")
        ne_lat_s = get_val(segment, "bounding_box.ne.latitude")
        ne_lng_s = get_val(segment, "bounding_box.ne.longitude")
        
        if all(v is not None for v in [sw_lat_s, sw_lng_s, ne_lat_s, ne_lng_s]):
            # Coordinates in order: SW -> SE -> NE -> NW -> SW (closed loop)
            coords_str_s = (
                f"{sw_lat_s},{sw_lng_s}|"
                f"{sw_lat_s},{ne_lng_s}|"
                f"{ne_lat_s},{ne_lng_s}|"
                f"{ne_lat_s},{sw_lng_s}|"
                f"{sw_lat_s},{sw_lng_s}"
            )
            # Cyan outline, semi-transparent cyan fill
            params.append(("path", f"color:0x00ffffff|fillcolor:0x00ffff10|weight:2|{coords_str_s}"))

    # Encode query parameters manually to handle multiple 'path' keys properly
    query_string = urllib.parse.urlencode(params)
    full_url = f"{url}?{query_string}"
    
    print(f"Downloading static map with overlays to '{file_name}'...")
    try:
        req = urllib.request.Request(
            full_url,
            headers={"User-Agent": "amkroofing-solar-cache/1.0 (amkroofing@amkroofing.com)"}
        )
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                with open(file_name, 'wb') as f:
                    f.write(response.read())
                print(f"Success! Satellite image with overlays saved as '{file_name}'.")
            else:
                print(f"Failed to retrieve image. HTTP Status: {response.status}")
    except Exception as e:
        print(f"Error downloading satellite image: {e}")

# Example usage:
if __name__ == "__main__":
    # Fetch the API key from an environment variable
    API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "YOUR_API_KEY_HERE")
    
    parser = argparse.ArgumentParser(
        description="Fetch Google Solar API insights for an address or coordinates."
    )
    parser.add_argument(
        "-a", "--address",
        type=str,
        help="The address to query."
    )
    parser.add_argument(
        "--lat",
        type=float,
        help="Latitude coordinates."
    )
    parser.add_argument(
        "--lng",
        type=float,
        help="Longitude coordinates."
    )
    args = parser.parse_args()

    # Determine input type and validate
    if args.address:
        if args.lat is not None or args.lng is not None:
            parser.error("Specify either --address OR both --lat and --lng, not both.")
        print(f"Geocoding address: {args.address}")
        lat, lng = geocode_address(args.address, API_KEY)
    elif args.lat is not None and args.lng is not None:
        lat, lng = args.lat, args.lng
    else:
        parser.error("You must specify either --address (-a) OR both --lat and --lng.")

    if lat is not None and lng is not None:
        print(f"Fetching solar insights for coordinates: {lat}, {lng}")
        insights = get_solar_insights(API_KEY, lat, lng)
        if insights:
            filename = "roof_scan_polygons.png"
            if args.address:
                import re
                slug = re.sub(r'[^a-zA-Z0-9]+', '-', args.address).strip('-').lower()
                filename = f"roof_scan_{slug}.png"
            download_satellite_with_polygons(API_KEY, lat, lng, insights, filename)
    else:
        print("Error: Could not resolve coordinates.")