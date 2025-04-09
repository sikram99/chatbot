# EV Charging Station Finder – Backend Module 🔌

This Python module helps find the **closest available EV charging station** based on the user’s current location using **TomTom APIs**.

---

## What This Does

- Finds **nearby charging stations** (using coordinates).
- Checks **real-time availability** of chargers.
- Calculates **distance** and **ETA**.
- (Optional) Returns **turn-by-turn instructions** and **full routing data** for frontend use.

---

## How to Use

1. **Location format**:  
   The input location must be in this format:  
   ```python
   USER_LOCATION = (longitude, latitude)
   ```

2. **Call the function**:  
   In your Python script, call:

   ```python
   from find_station import find_station

   result = find_station(USER_LOCATION, INCLUDE_NAVIGATION=True, RETURN_FULL_JSON=False)
   ```

3. **What it returns**:
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

4. **Full route JSON** (optional):  
   Set `RETURN_FULL_JSON=True` if the frontend needs raw routing data.

---

## Important Notes

- TomTom expects location as **(longitude, latitude)** — not the usual (lat, lon).
- If no station is available nearby, it tries again by expanding the search.
- The code avoids unnecessary API calls by limiting the number of iterations.

---

## For Frontend Teammates

You’ll get all the data you need from the output dict. Just call the function, pass the current user location, and render the output as needed.

