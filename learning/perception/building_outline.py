import os
import math
import urllib.request
import urllib.parse
import json
import argparse
from PIL import Image, ImageDraw, ImageFont

# Web Mercator constants
TILE_SIZE = 256
MAX_LAT = 85.05112878

def latlng_to_norm(lat: float, lng: float) -> tuple[float, float]:
    """Projects lat/lng to normalized [0, 1] Web Mercator coordinates."""
    lat = max(min(lat, MAX_LAT), -MAX_LAT)
    nx = (lng + 180.0) / 360.0
    lat_rad = math.radians(lat)
    ny = (1.0 - math.log(math.tan(lat_rad) + 1.0 / math.cos(lat_rad)) / math.pi) / 2.0
    return nx, ny

def project_latlng_to_pixel(
    lat: float, 
    lng: float, 
    center_lat: float, 
    center_lng: float, 
    zoom: int, 
    width: int, 
    height: int, 
    scale: int
) -> tuple[float, float]:
    """Projects a lat/lng coordinate to physical pixel coordinates on the static map image."""
    world_size = TILE_SIZE * (2 ** zoom)
    
    # Get world coordinates of the center point
    cnx, cny = latlng_to_norm(center_lat, center_lng)
    cwx, cwy = cnx * world_size, cny * world_size
    
    # Get world coordinates of the target point
    nx, ny = latlng_to_norm(lat, lng)
    wx, wy = nx * world_size, ny * world_size
    
    # Compute logical pixel offsets from center
    lx = wx - cwx + width / 2.0
    ly = wy - cwy + height / 2.0
    
    # Scale to physical pixels
    return lx * scale, ly * scale

def geocode_with_building_outlines(address: str, api_key: str) -> dict:
    """Queries the Google Geocoding API with extra_computations=BUILDING_AND_ENTRANCES."""
    encoded_address = urllib.parse.quote(address)
    url = (
        f"https://maps.googleapis.com/maps/api/geocode/json"
        f"?address={encoded_address}"
        f"&extra_computations=BUILDING_AND_ENTRANCES"
        f"&key={api_key}"
    )
    
    print(f"Geocoding address: '{address}' via Geocoding API...")
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "AMKRoofing-GeocodingClient/1.0"}
    )
    
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode())
        
    status = data.get("status")
    if status != "OK":
        raise ValueError(f"Geocoding API failed with status: {status}. Response: {data}")
        
    return data

def download_satellite_image(
    lat: float, 
    lng: float, 
    zoom: int, 
    size_str: str, 
    scale: int, 
    api_key: str
) -> bytes:
    """Downloads a satellite image centered at (lat, lng) from Google Static Maps API."""
    url = (
        f"https://maps.googleapis.com/maps/api/staticmap"
        f"?center={lat},{lng}"
        f"&zoom={zoom}"
        f"&size={size_str}"
        f"&scale={scale}"
        f"&maptype=satellite"
        f"&key={api_key}"
    )
    
    print(f"Downloading static satellite map at zoom={zoom}, size={size_str}...")
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "AMKRoofing-SatelliteDownloader/1.0"}
    )
    
    with urllib.request.urlopen(req) as response:
        if response.status != 200:
            raise ValueError(f"Static Maps API failed with status code {response.status}")
        return response.read()

def draw_overlay_and_legend(
    image_bytes: bytes,
    center_lat: float,
    center_lng: float,
    zoom: int,
    width: int,
    height: int,
    scale: int,
    buildings_data: list,
    entrances_data: list,
    address: str
) -> Image.Image:
    """Draws building footprints and entrances on the image and adds a legend."""
    # Load base image
    base_img = Image.open(io_bytes := io_byte_stream(image_bytes)).convert("RGBA")
    
    # Create layers
    overlay = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    # 1. Draw Building Footprints (outlines and fills)
    # Color Palette: Neon Green (#39FF14)
    # RGB: (57, 255, 20)
    neon_green_fill = (57, 255, 20, 60)       # Semi-transparent fill
    neon_green_outline = (57, 255, 20, 255)   # Opaque outline
    
    polygon_count = 0
    for building in buildings_data:
        outlines = building.get("building_outlines", [])
        for outline in outlines:
            polygon = outline.get("display_polygon", {})
            coords = polygon.get("coordinates", [])
            if not coords:
                continue
            
            # GeoJSON coordinates can be nested: [[[lng, lat], [lng, lat], ...]]
            # We take the exterior ring (index 0)
            exterior_ring = coords[0]
            
            # Map lat/lng coordinates to pixel coordinates
            pixel_points = []
            for pt in exterior_ring:
                lng, lat = pt[0], pt[1]
                px, py = project_latlng_to_pixel(lat, lng, center_lat, center_lng, zoom, width, height, scale)
                pixel_points.append((px, py))
                
            if len(pixel_points) < 3:
                continue
                
            # Draw semi-transparent fill
            draw.polygon(pixel_points, fill=neon_green_fill)
            # Draw solid, thick outline
            draw.line(pixel_points + [pixel_points[0]], fill=neon_green_outline, width=3 * scale, joint="round")
            polygon_count += 1

    # 2. Draw Entrances (if any are returned)
    # Color: Neon Cyan (#00F0FF)
    # RGB: (0, 240, 255)
    neon_cyan_fill = (0, 240, 255, 200)
    neon_cyan_outline = (0, 240, 255, 255)
    
    entrance_count = 0
    for entrance in entrances_data:
        loc = entrance.get("location")
        if loc:
            lat, lng = loc.get("lat"), loc.get("lng")
            px, py = project_latlng_to_pixel(lat, lng, center_lat, center_lng, zoom, width, height, scale)
            
            # Draw entrance as a small circle
            r = 5 * scale
            draw.ellipse([px - r, py - r, px + r, py + r], fill=neon_cyan_fill, outline=neon_cyan_outline, width=1 * scale)
            entrance_count += 1

    # Composite building overlays onto the base image
    final_img = Image.alpha_composite(base_img, overlay)
    
    # 3. Draw Legend Card
    # We will draw a dark slate card in the bottom-left corner with modern glassmorphism aesthetic
    legend_draw = ImageDraw.Draw(final_img)
    
    img_w, img_h = final_img.size
    
    # Define Legend Card dimensions (scaled for scale=2)
    card_w = 260 * scale
    card_h = 110 * scale if entrance_count > 0 else 85 * scale
    
    # Position: bottom-left corner, slightly offset from the edges and Google logo area
    # Google logo is usually at the bottom-left, occupying about 45 logical px height.
    # We offset y coordinates by 50 logical px from bottom.
    card_x1 = 15 * scale
    card_y2 = img_h - (50 * scale)
    card_y1 = card_y2 - card_h
    card_x2 = card_x1 + card_w
    
    # Dark slate background with high opacity (glassmorphism/dashboard card style)
    card_bg = (15, 23, 42, 220)        # slate-900 with alpha
    card_border = (255, 255, 255, 45)  # white border with low alpha
    
    # Draw card background
    legend_draw.rounded_rectangle(
        [card_x1, card_y1, card_x2, card_y2],
        radius=8 * scale,
        fill=card_bg,
        outline=card_border,
        width=1 * scale
    )
    
    # Load fonts
    font_title = None
    font_body = None
    font_subtitle = None
    
    # Try to load standard macOS Helvetica font paths, fallback to default
    font_paths = [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial.ttf"
    ]
    
    for path in font_paths:
        if os.path.exists(path):
            try:
                font_title = ImageFont.truetype(path, size=11 * scale)
                font_body = ImageFont.truetype(path, size=10 * scale)
                font_subtitle = ImageFont.truetype(path, size=8 * scale)
                break
            except Exception:
                pass
                
    if font_title is None:
        # Fallback to default PIL font
        font_title = ImageFont.load_default()
        font_body = ImageFont.load_default()
        font_subtitle = ImageFont.load_default()
        
    # Text offsets
    padding_x = 12 * scale
    padding_y = 10 * scale
    text_x = card_x1 + padding_x
    curr_y = card_y1 + padding_y
    
    # Header: "MAP LAYERS & LEGEND"
    legend_draw.text((text_x, curr_y), "MAP LEGEND", fill=(148, 163, 184, 255), font=font_title)
    
    # Subtle separator line under header
    curr_y += 16 * scale
    legend_draw.line([text_x, curr_y, card_x2 - padding_x, curr_y], fill=(255, 255, 255, 25), width=1)
    
    # Row 1: Building Outline Swatch & Label
    curr_y += 10 * scale
    swatch_size = 12 * scale
    swatch_r = 2 * scale
    
    # Building outline sample box
    legend_draw.rounded_rectangle(
        [text_x, curr_y, text_x + swatch_size, curr_y + swatch_size],
        radius=swatch_r,
        fill=(57, 255, 20, 60),
        outline=(57, 255, 20, 255),
        width=2 * scale
    )
    
    # Building outline label
    legend_draw.text(
        (text_x + swatch_size + 8 * scale, curr_y - 1 * scale), 
        "Building Outline", 
        fill=(255, 255, 255, 255), 
        font=font_body
    )
    
    # Row 2: Entrance Swatch & Label (only if entrances exist)
    if entrance_count > 0:
        curr_y += 18 * scale
        # Entrance circle sample
        legend_draw.ellipse(
            [text_x, curr_y + 1 * scale, text_x + swatch_size, curr_y + swatch_size - 1 * scale],
            fill=(0, 240, 255, 200),
            outline=(0, 240, 255, 255),
            width=1 * scale
        )
        # Entrance label
        legend_draw.text(
            (text_x + swatch_size + 8 * scale, curr_y - 1 * scale), 
            f"Building Entrance ({entrance_count})", 
            fill=(255, 255, 255, 255), 
            font=font_body
        )
        
    # Metadata footer: address/source
    curr_y += 18 * scale
    legend_draw.text(
        (text_x, curr_y), 
        f"Source: Google Geocoding API", 
        fill=(100, 116, 139, 255), 
        font=font_subtitle
    )
    
    return final_img.convert("RGB")

def io_byte_stream(b: bytes):
    import io
    return io.BytesIO(b)

def main():
    parser = argparse.ArgumentParser(
        description="Fetch building outlines via Geocoding API and draw them on satellite imagery."
    )
    parser.add_argument(
        "-a", "--address",
        type=str,
        default="184 Talmadge Ave, San Jose, CA",
        help="Address to geocode and draw."
    )
    parser.add_argument(
        "-z", "--zoom",
        type=int,
        default=20,
        help="Satellite map zoom level (typically 19 or 20 for buildings)."
    )
    parser.add_argument(
        "-s", "--size",
        type=str,
        default="640x640",
        help="Satellite map logical dimensions (e.g. 600x600, 640x640)."
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default="learning/perception/building_outline_overlay.png",
        help="Filename for the generated output image."
    )
    
    args = parser.parse_args()
    
    api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not api_key:
        print("Error: GOOGLE_MAPS_API_KEY environment variable is not set.")
        return
        
    try:
        # 1. Call Geocoding API
        geocoding_data = geocode_with_building_outlines(args.address, api_key)
        
        results = geocoding_data.get("results", [])
        if not results:
            print("No results returned by Geocoding API.")
            return
            
        result = results[0]
        formatted_address = result.get("formatted_address", args.address)
        print(f"Resolved formatted address: {formatted_address}")
        
        # Center coordinates
        loc = result.get("geometry", {}).get("location", {})
        center_lat = loc.get("lat")
        center_lng = loc.get("lng")
        if center_lat is None or center_lng is None:
            print("Error: Geocoding result did not contain location coordinates.")
            return
            
        print(f"Location coordinates: lat={center_lat}, lng={center_lng}")
        
        # Extract buildings and entrances
        buildings = result.get("buildings", [])
        entrances = result.get("entrances", [])
        
        if not buildings:
            print("Warning: No 'buildings' data returned by the Geocoding API for this address.")
            print("Please try a different address or ensure the parameter extra_computations=BUILDING_AND_ENTRANCES is fully enabled.")
            
        # Parse map size
        try:
            w_str, h_str = args.size.lower().split('x')
            width, height = int(w_str), int(h_str)
        except Exception:
            width, height = 640, 640
            
        scale = 2
        
        # 2. Download Static Map
        image_bytes = download_satellite_image(
            center_lat, 
            center_lng, 
            args.zoom, 
            args.size, 
            scale, 
            api_key
        )
        
        # 3. Draw outline, entrances, and legend
        final_image = draw_overlay_and_legend(
            image_bytes,
            center_lat,
            center_lng,
            args.zoom,
            width,
            height,
            scale,
            buildings,
            entrances,
            formatted_address
        )
        
        # Save output image
        # Create directories if they do not exist
        out_dir = os.path.dirname(args.output)
        if out_dir and not os.path.exists(out_dir):
            os.makedirs(out_dir, exist_ok=True)
            
        final_image.save(args.output)
        print(f"Success! Output image with outlines and legend saved to '{args.output}'.")
        
    except Exception as e:
        print(f"An error occurred during execution: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
