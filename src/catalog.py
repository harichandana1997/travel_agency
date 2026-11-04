from __future__ import annotations

from .route import BusRoute


def _route(
    origin: str,
    destination: str,
    operator: str,
    departure: str,
    arrival: str,
    duration_minutes: int,
    fare_inr: int,
    transfers: int,
    ac: bool,
    seating: str,
    rating: float,
) -> BusRoute:
    return BusRoute(
        origin,
        destination,
        operator,
        departure,
        arrival,
        duration_minutes,
        fare_inr,
        transfers,
        ac,
        seating,
        rating,
    )


SAMPLE_ROUTES: dict[tuple[str, str], list[BusRoute]] = {
    ("Delhi", "Jaipur"): [
        _route("Delhi", "Jaipur", "Pink City Express", "06:30", "11:30", 300, 520, 0, True, "Seater", 4.4),
        _route("Delhi", "Jaipur", "Rajasthan Roadlines", "22:15", "04:45", 390, 680, 0, True, "Sleeper", 4.6),
        _route("Delhi", "Jaipur", "Highway Travels", "08:00", "14:00", 360, 390, 1, False, "Seater", 4.0),
    ],
    ("Bengaluru", "Mysuru"): [
        _route("Bengaluru", "Mysuru", "Southern Star", "07:00", "10:30", 210, 280, 0, True, "Seater", 4.6),
        _route("Bengaluru", "Mysuru", "Karnataka Express", "09:15", "13:15", 240, 190, 0, False, "Seater", 4.1),
        _route("Bengaluru", "Mysuru", "Comfort Coach", "22:00", "01:45", 225, 420, 0, True, "Sleeper", 4.7),
    ],
    ("Mumbai", "Pune"): [
        _route("Mumbai", "Pune", "Deccan Link", "08:00", "11:45", 225, 360, 0, True, "Seater", 4.5),
        _route("Mumbai", "Pune", "Sahyadri Travels", "10:30", "14:30", 240, 240, 0, False, "Seater", 4.0),
        _route("Mumbai", "Pune", "Night Owl", "23:00", "03:30", 270, 550, 0, True, "Sleeper", 4.7),
    ],
    ("Chennai", "Puducherry"): [
        _route("Chennai", "Puducherry", "Coastal Cruiser", "07:30", "11:00", 210, 320, 0, True, "Seater", 4.5),
        _route("Chennai", "Puducherry", "East Coast Bus", "09:00", "13:15", 255, 220, 0, False, "Seater", 4.1),
        _route("Chennai", "Puducherry", "Blue Bay Travels", "22:00", "02:00", 240, 480, 0, True, "Sleeper", 4.6),
    ],
    ("Delhi", "Agra"): [
        _route("Delhi", "Agra", "Taj Express", "06:00", "10:00", 240, 400, 0, True, "Seater", 4.4),
        _route("Delhi", "Agra", "Yamuna Roadways", "08:30", "13:15", 285, 250, 1, False, "Seater", 3.9),
        _route("Delhi", "Agra", "Golden Route", "23:00", "03:15", 255, 590, 0, True, "Sleeper", 4.6),
    ],
    ("Hyderabad", "Vijayawada"): [
        _route("Hyderabad", "Vijayawada", "Krishna Travels", "07:15", "12:45", 330, 540, 0, True, "Seater", 4.5),
        _route("Hyderabad", "Vijayawada", "Telangana Roadlines", "09:00", "15:00", 360, 390, 0, False, "Seater", 4.1),
        _route("Hyderabad", "Vijayawada", "Night Comfort", "22:00", "04:00", 360, 720, 0, True, "Sleeper", 4.7),
    ],
    ("Mumbai", "Goa"): [
        _route("Mumbai", "Goa", "Konkan Coastliner", "18:00", "07:00", 780, 1100, 0, True, "Sleeper", 4.7),
        _route("Mumbai", "Goa", "Western Star", "17:00", "08:00", 900, 850, 1, True, "Seater", 4.2),
        _route("Mumbai", "Goa", "Coastal Budget", "19:30", "09:00", 810, 680, 0, False, "Sleeper", 4.0),
    ],
    ("Bengaluru", "Goa"): [
        _route("Bengaluru", "Goa", "Western Ghats Express", "18:30", "08:30", 840, 1050, 0, True, "Sleeper", 4.6),
        _route("Bengaluru", "Goa", "Deccan Night Bus", "20:00", "11:00", 900, 760, 1, True, "Seater", 4.0),
        _route("Bengaluru", "Goa", "Konkan Budget", "19:00", "10:00", 900, 620, 0, False, "Sleeper", 4.1),
    ],
    ("Pune", "Goa"): [
        _route("Pune", "Goa", "Sahyadri Sleeper", "20:00", "07:30", 690, 790, 0, True, "Sleeper", 4.5),
        _route("Pune", "Goa", "Konkan Roadways", "21:15", "09:00", 705, 560, 0, False, "Seater", 4.0),
        _route("Pune", "Goa", "Western Connect", "19:30", "08:30", 780, 480, 1, True, "Seater", 4.2),
    ],
    ("Delhi", "Rishikesh"): [
        _route("Delhi", "Rishikesh", "Ganga Valley Travels", "21:00", "05:30", 510, 750, 0, True, "Sleeper", 4.6),
        _route("Delhi", "Rishikesh", "Uttarakhand Express", "06:00", "14:00", 480, 440, 0, True, "Seater", 4.2),
        _route("Delhi", "Rishikesh", "Himalayan Budget", "22:00", "07:00", 540, 350, 1, False, "Seater", 3.9),
    ],
}

CITIES = tuple(sorted({city for pair in SAMPLE_ROUTES for city in pair}))

ITINERARIES: dict[str, list[dict[str, str]]] = {
    "Jaipur": [
        {"time": "Morning", "title": "Explore the old city", "description": "Take an easy walk near Hawa Mahal and the colorful bazaars. Leave time for chai and breakfast."},
        {"time": "Lunch", "title": "Taste local Rajasthani food", "description": "Look for a well-reviewed local thali spot; ask about vegetarian and spice options."},
        {"time": "Afternoon", "title": "Choose a fort or a slower afternoon", "description": "Visit Amer Fort if you have the energy, or take a relaxed break at a garden or museum."},
    ],
    "Mysuru": [
        {"time": "Morning", "title": "Mysore Palace", "description": "Visit the palace early and check the day's opening hours before setting out."},
        {"time": "Lunch", "title": "A Mysuru-style meal", "description": "Try a local thali or dosa and leave room for the city's well-known sweets."},
        {"time": "Afternoon", "title": "Green space or Chamundi Hills", "description": "Choose a gentle garden visit or head to the hills if the weather and timing suit."},
    ],
    "Pune": [
        {"time": "Morning", "title": "Walk through the old city", "description": "Explore a historic neighborhood at an unhurried pace and check local opening hours."},
        {"time": "Lunch", "title": "Try a local lunch spot", "description": "Sample a Maharashtrian thali or a neighborhood favorite."},
        {"time": "Afternoon", "title": "A fort, museum, or café break", "description": "Pick one nearby cultural stop rather than overloading the day."},
    ],
    "Puducherry": [
        {"time": "Morning", "title": "Stroll the heritage quarter", "description": "Explore the French Quarter on foot before the day gets warm."},
        {"time": "Lunch", "title": "Coastal flavors", "description": "Choose a local café or restaurant, checking current opening times."},
        {"time": "Afternoon", "title": "Seafront and a quiet break", "description": "Take a relaxed seaside walk and leave room for rest."},
    ],
    "Agra": [
        {"time": "Morning", "title": "Taj Mahal visit", "description": "Check ticket requirements and visiting hours in advance; allow time for security."},
        {"time": "Lunch", "title": "Local lunch break", "description": "Pause for a nearby meal and hydrate before the afternoon."},
        {"time": "Afternoon", "title": "Agra Fort or a garden", "description": "Choose one cultural stop and keep travel time between sights in mind."},
    ],
    "Vijayawada": [
        {"time": "Morning", "title": "Riverside and local landmarks", "description": "Start with a relaxed visit to a local landmark; check conditions and opening times."},
        {"time": "Lunch", "title": "Andhra flavors", "description": "Ask for the spice level that suits you and try a local meal."},
        {"time": "Afternoon", "title": "A viewpoint or cultural stop", "description": "Pick one nearby place of interest and avoid scheduling too tightly."},
    ],
    "Goa": [
        {"time": "Morning", "title": "A slow start by the coast", "description": "Choose a nearby beach or nature spot and check local conditions."},
        {"time": "Lunch", "title": "Goan food", "description": "Try a local restaurant and ask about dietary needs and spice."},
        {"time": "Afternoon", "title": "Heritage or nature", "description": "Choose a heritage walk or a green escape, leaving time to return before evening."},
    ],
    "Rishikesh": [
        {"time": "Morning", "title": "Riverside walk", "description": "Enjoy a relaxed walk by the Ganges; follow local safety and access guidance."},
        {"time": "Lunch", "title": "A simple local meal", "description": "Find a nearby café or vegetarian meal and take a break from the road."},
        {"time": "Afternoon", "title": "Explore at your own pace", "description": "Visit a nearby cultural site or spend extra time in nature; check local conditions."},
    ],
}
