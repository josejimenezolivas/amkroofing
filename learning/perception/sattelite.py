import requests
import os

def download_satellite_image(api_key, lat, lng, zoom=18, size="600x600", file_name="satellite_image.png"):
    """
    Fetches a satellite image from the Google Maps Static API and saves it to disk.
    """
    # Base URL for the Google Maps Static API
    url = "https://maps.googleapis.com/maps/api/staticmap"
    
    # Define the query parameters
    params = {
        "center": f"{lat},{lng}",
        "zoom": zoom,           
        "size": size,           
        "maptype": "satellite", 
        "key": api_key,         
        "scale": 2
    }
    
    # Execute the GET request
    response = requests.get(url, params=params)
    
    # 200 OK means the image was generated successfully
    if response.status_code == 200:
        with open(file_name, 'wb') as f:
            f.write(response.content)
        print(f"Success! Image saved as '{file_name}'.")
    else:
        print(f"Failed to retrieve image. HTTP Status: {response.status_code}")
        print(f"Error details: {response.text}")

# --- Example Usage ---
if __name__ == "__main__":
    # Replace with your actual Google Maps API Key
    API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "YOUR_API_KEY_HERE")
    
    # Coordinates for your target location
    LATITUDE = 37.3699778189365
    LONGITUDE = -121.82997718220432
    
    # Zoom levels typically range from 0 (world) to 21+ (individual buildings)
    download_satellite_image(API_KEY, LATITUDE, LONGITUDE, zoom=20, file_name="roof_scan.png")