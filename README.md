# EV Charging Station Finder – Backend Module 🔌

This Python module helps find the **closest available EV charging station** based on the user’s current location using **TomTom APIs**.
and returns the

- Location
- Address
- Distance
- ETA
- Navigation Details

For the charging station
Optionally it can also return the raw data received which can be used for further processing

---

## What This Does

- Finds **nearby charging stations** using TOMTOMs Search API
- Checks **real-time availability** of chargers using TOMTOMs Charging Stations Avalaility API
- Calculates **distance** and **ETA**. using TOMTOMs Routing API (which takes into account Real Time Traffic as well)
- (Optional) Returns **turn-by-turn instructions** and **full routing data** for frontend use.

---

## How to Use

1. **Location format**:  
   The input location must be in this format:  
   ```python
   USER_LOCATION = (longitude, latitude)
   ```

2. **Call the function**:  
   In your Python script, simply call:

   ```python
   from find_station import find_station

   result = find_station(USER_LOCATION)
   ```

   By default it does not return Navigation Instrcutions and Raw JSON
   To include those, or for using your own API key you can add one or all of these options:

   ```python
   result = find_station(USER_LOCATION, TOMTOM_API_KEY="your_api_key", INCLUDE_NAVIGATION=True, RETURN_FULL_JSON=True)
   ```

4. **What it returns**:
   ```python
   {
       "Name": "Station Name",
       "Location": (longitude, latitude),
       "Address": "Full address",
       "Distance": 4.3,  # in km
       "ETA": 8.1,       # in minutes
       "Instructions": [ ... ]  # Only if INCLUDE_NAVIGATION=True
   }
   ```

5. **Full route JSON** (optional):  
   Set `RETURN_FULL_JSON=True` if the frontend needs raw routing data.

---

## Important Notes

- TomTom expects location as **(longitude, latitude)** — not the usual (lat, lon).
- If no station is available nearby, it tries again by expanding the search.
- The code avoids unnecessary API calls by limiting the number of iterations.

---

## For Frontend Teammates

You’ll get all the data you need from the output dict. Just call the function, pass the current user location, and render the output as needed.

