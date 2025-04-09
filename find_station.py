import requests
from pymongo import MongoClient, errors
from math import radians, sin, cos, sqrt, atan2

# Fixed options for limiting number of API calls
NUMBER_OF_RESULTS = 5  # Number of closest results to fetch per iteration
MAX_ITERATIONS = 3  # Maximum number of iterations to avoid excessive API calls
TOMTOM_API_KEY = "2p4OcGzjWEPmyw09G5I1hIDiwdX0Fd6i"

# Function to get route details from TomTom API
def get_route_details(USER_LOCATION, destination, TOMTOM_API_KEY):
    try:
        url = f"https://api.tomtom.com/routing/1/calculateRoute/{USER_LOCATION[1]},{USER_LOCATION[0]}:{destination[1]},{destination[0]}/json"
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

            # get distance and eta
            distance_km = route["summary"]["lengthInMeters"] / 1000  # Convert meters to km
            eta_minutes = route["summary"]["travelTimeInSeconds"] / 60  # Convert seconds to minutes

            # Prepare route instructions
            instructions = []
            for instruction in route["guidance"]["instructions"]:
                instructions.append(instruction["message"])
            
            route_summary = {
                "distance_km": distance_km,
                "eta_minutes": eta_minutes,
                "instructions": instructions,
                "full_json": data
            }
            return route_summary
        else:
            raise ValueError("No route data found.")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching route for {destination}: {e}")
        return None

# Function to fetch charging station availability
def get_charging_station_availability(station_id, TOMTOM_API_KEY):
    try:
        url = "https://api.tomtom.com/search/2/chargingAvailability.json"
        params = {
            "chargingAvailability": station_id,
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
def get_nearby_stations(USER_LOCATION, TOMTOM_API_KEY):
    try:
        url = f"https://api.tomtom.com/search/2/nearbySearch/.json"
        params = {
            "lat": USER_LOCATION[1],
            "lon": USER_LOCATION[0],
            "limit": NUMBER_OF_RESULTS,
            "categorySet" : 7309, # 7309 is code for EV Charging Stations in TOM TOM
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
def find_station(USER_LOCATION, TOMTOM_API_KEY=TOMTOM_API_KEY, INCLUDE_NAVIGATION=False, RETURN_FULL_JSON=False):

    available_stations = []
    iteration = 0

    while iteration < MAX_ITERATIONS:
        # Get nearby stations
        stations = get_nearby_stations(USER_LOCATION, TOMTOM_API_KEY)

        if not stations:
            print("No stations found.")
            break

        # Check availability for each station
        for station in stations:
            station_id = station["id"]
            availability = get_charging_station_availability(station_id, TOMTOM_API_KEY)
            if availability >= 1:
                route_details = get_route_details(USER_LOCATION, (station["position"]["lon"], station["position"]["lat"]), TOMTOM_API_KEY)
                if route_details and route_details.get("distance_km") and route_details.get("eta_minutes"):
                    available_stations.append((station, route_details))

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
        available_stations.sort(key=lambda x: x[1].get("eta_minutes", float('inf')))


        # Get the top station (the one with the best ETA)
        top_station = available_stations[0]

        # get variables to return
        lat = top_station[0]["position"]["lat"]
        lon = top_station[0]["position"]["lon"]
        address = top_station[0]["address"].get("freeformAddress", "Unknown address")
        name = top_station[0]["poi"].get("name")
        distance = top_station[1]["distance_km"]
        eta = top_station[1]["eta_minutes"]
        full_json = (station, top_station[1]["full_json"])

        return {
            "Name": name,
            "Location": (lon, lat),
            "Address": address,
            "Distance": distance,
            "ETA": eta,
            **({"Instructions": top_station[1]["instructions"]} if INCLUDE_NAVIGATION else {}),
            **({"full_json": full_json} if RETURN_FULL_JSON else {})
        }
    else:
        print("No available charging stations found after multiple iterations.")