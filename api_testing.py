import requests
from pymongo import MongoClient, errors
from math import radians, sin, cos, sqrt, atan2

# TomTom API key
TOMTOM_API_KEY = "2p4OcGzjWEPmyw09G5I1hIDiwdX0Fd6i"

# User location ; using Melbourne City Center coordinates for now
user_location = (144.9631, -37.9)

# Configurable options
NUMBER_OF_RESULTS = 5  # Number of closest results to fetch per iteration
MAX_ITERATIONS = 3  # Maximum number of iterations to avoid excessive API calls
RETURN_FULL_JSON = False  # Whether to return full route JSON or just the ETA/Route details


# Function to get route details from TomTom API
def get_route_details(destination):
    try:
        url = f"https://api.tomtom.com/routing/1/calculateRoute/{user_location[1]},{user_location[0]}:{destination[1]},{destination[0]}/json"
        params = {
            "routeType": "fastest",
            "instructionsType": "text",
            "traffic": "true",
            "travelMode": "car",
            "key": TOMTOM_API_KEY
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()  # Raise exception for HTTP errors

        data = response.json()
        if "routes" in data and data["routes"]:
            route = data["routes"][0]
            distance_km = route["summary"]["lengthInMeters"] / 1000  # Convert meters to km
            eta_minutes = route["summary"]["travelTimeInSeconds"] / 60  # Convert seconds to minutes
            if RETURN_FULL_JSON:
                return data  # Return the entire routing detail
            return distance_km, eta_minutes
        else:
            raise ValueError("No route data found.")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching route for {destination}: {e}")
        return None, None

# Function to fetch charging station availability
def get_charging_station_availability(station_id):
    try:
        url = "https://api.tomtom.com/search/2/chargingAvailability.json"
        params = {
            "chargingAvailability": station_id,
            # "chargingAvailability": "KKNNUbU4ReDT0LrLVSLjVg", # replace with stations id
            "key": TOMTOM_API_KEY
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()

        connectors = data.get("connectors", [])
        if not connectors:
            print(f"No connectors found for station {station_id}")
            return 0

        total_available = 0
        for connector in connectors:
            current = connector.get("availability", {}).get("current", {})
            total_available += current.get("available", 0)

        return total_available

    except requests.exceptions.RequestException as e:
        print(f"Error fetching availability for station {station_id}: {e}")
        return 0


# Function to get nearby charging stations from TomTom API
def get_nearby_stations():
    try:
        url = f"https://api.tomtom.com/search/2/nearbySearch/.json"
        params = {
            "lat": user_location[1],
            "lon": user_location[0],
            "limit": NUMBER_OF_RESULTS,
            "categorySet" : 7309,
            "key": TOMTOM_API_KEY
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        if "results" in data:
            return data["results"]
        else:
            print("No nearby stations found.")
            return []
    except requests.exceptions.RequestException as e:
        print(f"Error fetching nearby stations: {e}")
        return []

# Main logic to find the best available charging station
def find_best_station():
    available_stations = []
    iteration = 0
    while iteration < MAX_ITERATIONS:
        print(f"Iteration {iteration + 1}/{MAX_ITERATIONS}...")

        # Get nearby stations
        stations = get_nearby_stations()

        if not stations:
            print("No stations found.")
            break

        # Check availability for each station
        for station in stations:
            station_id = station["id"]
            availability = get_charging_station_availability(station_id)
            if availability >= 1:
                distance, eta = get_route_details((station["position"]["lon"], station["position"]["lat"]))
                if distance and eta:
                    available_stations.append((station, distance, eta))

        # If we have available stations, break out of the loop
        if available_stations:
            break

        iteration += 1
        # If no stations available, try again with more stations
        if iteration < MAX_ITERATIONS:
            global NUMBER_OF_RESULTS
            NUMBER_OF_RESULTS += 3  # Fetch more stations in the next iteration

    if available_stations:
        # Sort the available stations by ETA (shortest travel time first)
        available_stations.sort(key=lambda x: x[2])

        # Get the top station (the one with the best ETA)
        top_station = available_stations[0]

        # get variables to return
        lat = top_station[0]["position"]["lat"]
        lon = top_station[0]["position"]["lon"]
        address = top_station[0]["address"].get("freeformAddress", "Unknown address")
        distance = top_station[1]
        eta = top_station[2]
        return {"Location": (lon,lat), "Address": address, "Distance": distance, "ETA": eta, "top_station": top_station}
    else:
        print("No available charging stations found after multiple iterations.")

# Main execution
if __name__ == "__main__":
    top_station = find_best_station()
    if top_station:
        print("Top charging station:")
        print(f"Location: {top_station['Location'][1]}, {top_station['Location'][0]} , Address: {top_station['Address']}, Distance: {top_station['Distance']:.2f} km, ETA: {top_station['ETA']:.2f} min", top_station['top_station'])

    else:
        print("No available charging stations found.")
