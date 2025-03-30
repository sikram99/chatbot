import requests
from pymongo import MongoClient, errors
from math import radians, sin, cos, sqrt, atan2


# MongoDB connection string
MONGO_URI = "mongodb+srv://EVAT:EVAT123@cluster0.5axoq.mongodb.net/"

# TomTom API key
TOMTOM_API_KEY = "2p4OcGzjWEPmyw09G5I1hIDiwdX0Fd6i"

# User location ; using Melbourne City Center coordinates for now
user_location = (144.9631, -37.8136)

# Haversine formula to calculate distance in km
def haversine(lon1, lat1, lon2, lat2):
    R = 6371  # Radius of Earth in km
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

# Function to get route details from TomTom API
def get_route_details(destination):
    try:
        url = f"https://api.tomtom.com/routing/1/calculateRoute/{user_location[1]},{user_location[0]}:{destination[1]},{destination[0]}/json"
        params = {
            "routeType": "fastest",
            "traffic": "true",
            "travelMode": "car",
            "vehicleCommercial": "false",
            "key": TOMTOM_API_KEY
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()  # Raise exception for HTTP errors

        data = response.json()
        if "routes" in data and data["routes"]:
            route = data["routes"][0]
            distance_km = route["summary"]["lengthInMeters"] / 1000  # Convert meters to km
            eta_minutes = route["summary"]["travelTimeInSeconds"] / 60  # Convert seconds to minutes
            return distance_km, eta_minutes
        else:
            raise ValueError("No route data found.")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching route for {destination}: {e}")
        return None, None

try:
    # Connect to MongoDB
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client["EVAT"]
    collection = db["charging_stations"]
    
    try:
        # Fetch all charging stations
        stations = list(collection.find({}, {"longitude": 1, "latitude": 1, "_id": 0}))

        if not stations:
            raise ValueError("No charging stations found in the database.")

        # Compute distances and sort
        stations = sorted(stations, key=lambda s: haversine(
            user_location[0], user_location[1],
            s["longitude"], s["latitude"]
        ))

        # Get the 5 closest stations
        closest_stations = [(s["longitude"], s["latitude"]) for s in stations[:5]]

        # Get road distances and ETAs from TomTom API
        results = []
        for station in closest_stations:
            distance, eta = get_route_details(station)
            if distance is not None and eta is not None:
                results.append((distance, eta, station))

        # Sort results by ETA (shortest travel time first)
        results.sort(key=lambda x: x[1])

        # Print the final sorted results
        print("Charging stations sorted by ETA:")
        for distance, eta, location in results:
            print(f"Location: {location}, Distance: {distance:.2f} km, ETA: {eta:.2f} min")

    except Exception as e:
        print("Error retrieving data:", str(e))

except errors.ConnectionFailure:
    print("Error: Could not connect to MongoDB. Check your connection string or network.")

except Exception as e:
    print("Unexpected error:", str(e))
