from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

import requests


@dataclass(frozen=True)
class BusRoute:
    origin: str
    destination: str
    operator: str
    departure: str
    arrival: str
    duration_minutes: int
    fare_inr: int
    transfers: int
    ac: bool
    seating: str
    rating: float

    @property
    def duration_text(self) -> str:
        hours, minutes = divmod(self.duration_minutes, 60)
        return f"{hours}h {minutes:02d}m"

    @property
    def bus_type(self) -> str:
        return f"{'AC' if self.ac else 'Non-AC'} {self.seating}"


@dataclass(frozen=True)
class RoadRouteEstimate:
    origin: str
    destination: str
    distance_km: float
    duration_minutes: int
    coordinates: tuple[tuple[float, float], ...]

    @property
    def duration_text(self) -> str:
        hours, minutes = divmod(self.duration_minutes, 60)
        if hours:
            return f"{hours}h {minutes:02d}m"
        return f"{minutes}m"


def get_routes(origin: str, destination: str) -> list[BusRoute]:
    from .catalog import SAMPLE_ROUTES

    return list(SAMPLE_ROUTES.get((origin.strip(), destination.strip()), []))


@lru_cache(maxsize=256)
def _geocode_indian_place(place: str) -> tuple[float, float]:
    response = requests.get(
        "https://nominatim.openstreetmap.org/search",
        params={"q": f"{place}, India", "format": "jsonv2", "limit": 1, "countrycodes": "in"},
        headers={"User-Agent": "WayfarerBusPlanner/1.0 (route lookup)"},
        timeout=(5, 20),
    )
    response.raise_for_status()
    results = response.json()
    if not results:
        raise LookupError(f"Could not find '{place}' in India. Check the place name and try again.")
    try:
        return float(results[0]["lon"]), float(results[0]["lat"])
    except (KeyError, TypeError, ValueError, IndexError) as error:
        raise ValueError(f"Location lookup returned invalid coordinates for '{place}'.") from error


def get_road_route(origin: str, destination: str) -> RoadRouteEstimate:
    """Get an illustrative road route; this does not represent a bus timetable."""
    origin = origin.strip()
    destination = destination.strip()
    if not origin or not destination:
        raise ValueError("Enter both an origin and a destination.")
    if origin.casefold() == destination.casefold():
        raise ValueError("Origin and destination must be different places.")

    start = _geocode_indian_place(origin)
    end = _geocode_indian_place(destination)
    response = requests.get(
        f"https://router.project-osrm.org/route/v1/driving/"
        f"{start[0]},{start[1]};{end[0]},{end[1]}",
        params={"overview": "full", "geometries": "geojson"},
        timeout=(5, 30),
    )
    response.raise_for_status()
    result = response.json()
    routes = result.get("routes", [])
    if result.get("code") != "Ok" or not routes:
        message = result.get("message", "No road route was found between these places.")
        raise LookupError(message)
    route = routes[0]
    try:
        coordinates = tuple(
            (float(longitude), float(latitude))
            for longitude, latitude in route["geometry"]["coordinates"]
        )
        distance_km = float(route["distance"]) / 1000
        duration_minutes = round(float(route["duration"]) / 60)
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("The road routing service returned an invalid route.") from error
    if not coordinates:
        raise LookupError("The road routing service returned an empty route.")
    return RoadRouteEstimate(
        origin=origin,
        destination=destination,
        distance_km=distance_km,
        duration_minutes=duration_minutes,
        coordinates=coordinates,
    )
