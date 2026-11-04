from __future__ import annotations

from typing import Any

from .catalog import ITINERARIES
from .route import BusRoute, RoadRouteEstimate


PRIORITIES = ("Lowest price", "Fewer transfers", "Comfort")
DEFAULT_PREFERENCES: dict[str, Any] = {
    "budget_inr": None,
    "comfort": ["AC", "Seater", "Sleeper"],
    "priorities": ["Lowest price", "Fewer transfers", "Comfort"],
    "interests": ["local food", "nature", "cultural sights"],
    "chat_updates": [],
}

_PRIORITY_METRICS = {
    "Lowest price": "price",
    "Fewer transfers": "transfers",
    "Comfort": "comfort",
}
_PRIORITY_WEIGHTS = (0.6, 0.25, 0.15)


def estimate_bus_options(
    road_route: RoadRouteEstimate,
    preferences: dict[str, Any],
) -> list[dict[str, Any]]:
    """Create transparent planning estimates, not live bus listings or quotes."""
    comfort = preferences.get("comfort") or []
    seating_choices = [item for item in comfort if item in ("Seater", "Sleeper")]
    wants_ac = "AC" in comfort
    budget = preferences.get("budget_inr")
    distance_km = road_route.distance_km
    duration_minutes = road_route.duration_minutes
    options = []

    for seating, low_rate, high_rate, duration_factor in (
        ("Seater", 1.2, 2.2, 1.3),
        ("Sleeper", 1.6, 3.0, 1.4),
    ):
        if seating_choices and seating not in seating_choices:
            continue
        fare_min = round(distance_km * low_rate / 10) * 10
        fare_max = round(distance_km * high_rate / 10) * 10
        if budget and fare_max > budget:
            continue
        options.append(
            {
                "bus_type": f"{'AC ' if wants_ac else ''}{seating}",
                "fare_min": max(100, fare_min),
                "fare_max": max(100, fare_max),
                "duration_min": round(duration_minutes * duration_factor),
                "duration_max": round(duration_minutes * (duration_factor + 0.25)),
            }
        )

    priorities = preferences.get("priorities") or list(PRIORITIES)
    if "Comfort" in priorities and "Lowest price" not in priorities:
        options.reverse()
    return options


def rank_routes(
    routes: list[BusRoute],
    preferences: dict[str, Any],
) -> list[BusRoute]:
    budget = preferences.get("budget_inr")
    comfort = preferences.get("comfort") or []
    seating_choices = [item for item in comfort if item in ("Seater", "Sleeper")]
    eligible = [
        route
        for route in routes
        if (not budget or route.fare_inr <= budget)
        and ("AC" not in comfort or route.ac)
        and (not seating_choices or route.seating in seating_choices)
    ]
    if not eligible:
        return []

    priorities = preferences.get("priorities") or list(PRIORITIES)
    weights = {key: 0.0 for key in ("price", "transfers", "comfort")}
    valid_priorities = [priority for priority in priorities if priority in _PRIORITY_METRICS]
    for index, priority in enumerate(valid_priorities):
        weights[_PRIORITY_METRICS[priority]] = _PRIORITY_WEIGHTS[index]
    if not valid_priorities:
        weights["price"] = 1.0

    fares = [route.fare_inr for route in eligible]
    transfer_counts = [route.transfers for route in eligible]
    min_fare, fare_range = min(fares), max(fares) - min(fares)
    min_transfers = min(transfer_counts)
    transfer_range = max(transfer_counts) - min_transfers

    def score(route: BusRoute) -> tuple[float, int, str]:
        price_score = (route.fare_inr - min_fare) / fare_range if fare_range else 0
        transfer_score = (
            (route.transfers - min_transfers) / transfer_range if transfer_range else 0
        )
        comfort_score = (5 - route.rating) / 5
        return (
            weights["price"] * price_score
            + weights["transfers"] * transfer_score
            + weights["comfort"] * comfort_score,
            route.fare_inr,
            route.operator,
        )

    return sorted(eligible, key=score)


def build_itinerary(origin: str, destination: str) -> list[dict[str, str]]:
    del origin
    if destination in ITINERARIES:
        return ITINERARIES[destination]
    return [
        {
            "time": "Morning",
            "title": "Get oriented",
            "description": f"Take a gentle walk around {destination} and note nearby transport options.",
        },
        {
            "time": "Lunch",
            "title": "Find a local favorite",
            "description": "Choose a well-reviewed place that suits your dietary preferences.",
        },
        {
            "time": "Afternoon",
            "title": "Explore one local highlight",
            "description": "Pick a cultural or nature stop and leave a buffer for getting around.",
        },
    ]


def apply_chat_preference(message: str, preferences: dict[str, Any]) -> dict[str, Any]:
    text = message.lower().replace(",", "")
    updates: dict[str, Any] = {}
    words = text.replace("₹", " ").replace("rs.", " ").split()
    if "sleeper" in text:
        updates["comfort"] = list(dict.fromkeys([*preferences.get("comfort", []), "Sleeper"]))
    elif "seater" in text:
        updates["comfort"] = list(dict.fromkeys([*preferences.get("comfort", []), "Seater"]))
    if "non-ac" in text or "non ac" in text:
        updates["comfort"] = [
            item
            for item in updates.get("comfort", preferences.get("comfort", []))
            if item != "AC"
        ]
    elif "ac" in text:
        updates["comfort"] = list(
            dict.fromkeys([*updates.get("comfort", preferences.get("comfort", [])), "AC"])
        )
    if "transfer" in text and any(token in text for token in ("avoid", "fewer", "no ")):
        updates["priorities"] = ["Fewer transfers", "Lowest price", "Comfort"]
    for word in words:
        if word.isdigit():
            amount = int(word)
            if amount >= 100:
                updates["budget_inr"] = amount
                break
    if not updates:
        return {}
    updates["chat_updates"] = [
        "a fare limit" if "budget_inr" in updates else "",
        "bus comfort" if "comfort" in updates else "",
        "fewer transfers" if "priorities" in updates else "",
    ]
    updates["chat_updates"] = [item for item in updates["chat_updates"] if item]
    return updates
