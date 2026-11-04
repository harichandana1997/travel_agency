from __future__ import annotations

import os
from datetime import date, timedelta

import pydeck as pdk
import requests
import streamlit as st
from dotenv import load_dotenv

from src import (
    DEFAULT_PREFERENCES,
    PRIORITIES,
    apply_chat_preference,
    build_itinerary,
    clear_memory,
    delete_saved_trip,
    estimate_bus_options,
    get_routes,
    get_road_route,
    langchain_is_configured,
    list_saved_trips,
    load_memory,
    rank_routes,
    save_preferences,
    save_trip,
    summarize_with_langchain,
)

load_dotenv()


st.set_page_config(
    page_title="Chandu TripMate — bus trips, your way",
    page_icon="🚌",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data(ttl=86400, show_spinner="Finding a road route…")
def _cached_road_route(origin: str, destination: str):
    return get_road_route(origin, destination)


def _show_road_route(origin: str, destination: str) -> None:
    road_route = _cached_road_route(origin.strip(), destination.strip())
    st.markdown(
        f"**{road_route.distance_km:,.0f} km** · estimated driving time "
        f"**{road_route.duration_text}**"
    )
    st.pydeck_chart(
        pdk.Deck(
            layers=[
                pdk.Layer(
                    "PathLayer",
                    data=[{"path": list(road_route.coordinates)}],
                    get_path="path",
                    get_color=[35, 116, 90],
                    width_scale=20,
                    width_min_pixels=3,
                ),
                pdk.Layer(
                    "ScatterplotLayer",
                    data=[
                        {"position": road_route.coordinates[0]},
                        {"position": road_route.coordinates[-1]},
                    ],
                    get_position="position",
                    get_fill_color=[216, 243, 106],
                    get_line_color=[35, 116, 90],
                    get_radius=6000,
                    line_width_min_pixels=2,
                    stroked=True,
                ),
            ],
            initial_view_state=pdk.ViewState(
                longitude=sum(point[0] for point in road_route.coordinates)
                / len(road_route.coordinates),
                latitude=sum(point[1] for point in road_route.coordinates)
                / len(road_route.coordinates),
                zoom=5,
                pitch=0,
            ),
            map_style=None,
            tooltip={"text": f"{origin} to {destination}"},
        ),
        use_container_width=True,
    )
    st.caption(
        "Road geometry and driving-time estimate from OpenStreetMap and OSRM. "
        "This is not a bus route, schedule, fare, or actual bus journey time."
    )


def _session_defaults() -> None:
    if "preferences" not in st.session_state:
        saved = load_memory()
        st.session_state.preferences = {**DEFAULT_PREFERENCES, **saved["preferences"]}
        st.session_state.memory_summary = saved["summary"]
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": (
                    "Hi! I can help find a bus that fits your budget and travel style, "
                    "then sketch out a flexible itinerary. Pick a sample route in the "
                    "sidebar, or tell me what kind of trip you have in mind."
                ),
            }
        ]


def _assistant_reply(message: str) -> str:
    preferences = st.session_state.preferences
    update = apply_chat_preference(message, preferences)
    if update:
        st.session_state.preferences = {**preferences, **update}
        changed = ", ".join(update["chat_updates"])
        return (
            f"Got it — I’ll keep {changed} in mind for this trip and future suggestions. "
            "You can review or clear saved preferences in the sidebar."
        )
    return (
        "I can adjust your suggestions if you share preferences such as “keep it under "
        "₹1,000”, “I prefer sleeper buses”, or “avoid transfers”. Choose your cities and "
        "travel date in the sidebar to see available sample routes."
    )


try:
    _session_defaults()
except Exception as error:
    st.error(f"Could not load saved travel data: {error}")
    st.stop()
preferences = st.session_state.preferences

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
    :root { --ink:#17231f; --muted:#75817b; --green:#23745a; --lime:#d8f36a; --line:#e6ebe7; }
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; color:var(--ink); }
    .stApp { background:#f7f8f5; }
    [data-testid="stSidebar"] { background:#fff; border-right:1px solid var(--line); }
    [data-testid="stSidebar"] > div:first-child { padding-top:1.2rem; }
    h1, h2, h3 { font-family:'Manrope',sans-serif; letter-spacing:-.04em; }
    .brand { font:800 1.28rem 'Manrope',sans-serif; letter-spacing:-.06em; margin:0 0 1.6rem; }
    .brand span { color:var(--green); }
    .eyebrow { color:var(--green); text-transform:uppercase; font-weight:700; font-size:.72rem; letter-spacing:.13em; }
    .hero { background:#e9f2e9; border:1px solid #dfe9df; border-radius:20px; padding:1.8rem 2rem; margin:.4rem 0 1.2rem; }
    .hero h1 { font-size:2rem; margin:.3rem 0 .4rem; }
    .hero p { color:#5f6e65; margin:0; max-width:650px; }
    .route-card { background:#fff; border:1px solid var(--line); border-radius:17px; padding:1.15rem 1.25rem; margin:.65rem 0; }
    .route-top { display:flex; align-items:center; justify-content:space-between; gap:1rem; }
    .operator { font:700 1rem 'Manrope',sans-serif; }
    .fare { font:800 1.25rem 'Manrope',sans-serif; color:var(--green); }
    .route-times { display:flex; align-items:center; gap:1rem; margin:.9rem 0; }
    .route-times strong { font:700 1.08rem 'Manrope',sans-serif; }
    .route-line { border-top:1px dashed #b5c5b9; flex:1; text-align:center; color:var(--muted); font-size:.74rem; padding-top:.35rem; }
    .chips { color:#647168; font-size:.82rem; }
    .sample-note { color:#7b847e; font-size:.78rem; }
    .section-title { font:700 1.2rem 'Manrope',sans-serif; margin:1.4rem 0 .4rem; }
    .memory-box { border:1px solid var(--line); background:#fbfcfa; padding:.9rem; border-radius:12px; color:#5f6c64; font-size:.86rem; }
    div[data-testid="stChatMessage"] { border:1px solid var(--line); border-radius:16px; }
    .stButton > button { border-radius:10px; font-weight:600; }
    @media (max-width: 700px) { .hero { padding:1.25rem; } .hero h1 { font-size:1.55rem; } }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown('<div class="brand">Chandu <span>TripMate</span></div>', unsafe_allow_html=True)
    st.markdown('<div class="eyebrow">Plan a bus trip</div>', unsafe_allow_html=True)
    origin = st.text_input("From", value="Delhi", placeholder="Any place in India")
    destination = st.text_input("To", value="Jaipur", placeholder="Any place in India")
    st.caption("Enter any city or place in India.")
    travel_date = st.date_input("Travel date", value=date.today() + timedelta(days=3))
    budget = st.number_input(
        "Max one-way fare (₹)",
        min_value=0,
        max_value=50000,
        value=int(preferences.get("budget_inr") or 0),
        step=100,
        help="Set 0 if you do not want a fare limit.",
    )
    selected_priorities = st.multiselect(
        "Rank what matters",
        options=list(PRIORITIES),
        default=[
            item
            for item in preferences.get("priorities", DEFAULT_PREFERENCES["priorities"])
            if item in PRIORITIES
        ],
        max_selections=3,
    )
    comfort_options = ["AC", "Seater", "Sleeper"]
    selected_comfort = st.multiselect(
        "Comfort preferences",
        options=comfort_options,
        default=[
            item
            for item in preferences.get("comfort", DEFAULT_PREFERENCES["comfort"])
            if item in comfort_options
        ],
    )
    st.caption("Sample schedules only — fares and times are illustrative.")

    st.divider()
    st.markdown("#### Your travel memory")
    summary = st.session_state.memory_summary
    if summary:
        st.markdown(f'<div class="memory-box">{summary}</div>', unsafe_allow_html=True)
    else:
        st.caption("Your preferences will appear here as you chat.")
    if st.button("Clear saved memory", use_container_width=True):
        try:
            clear_memory()
        except Exception as error:
            st.error(f"Could not clear saved memory: {error}")
        else:
            st.session_state.memory_summary = ""
            st.session_state.preferences = dict(DEFAULT_PREFERENCES)
            st.session_state.messages = st.session_state.messages[:1]
            st.rerun()
    with st.expander("Saved trips"):
        try:
            saved_trips = list_saved_trips()
        except Exception as error:
            st.error(f"Could not load saved trips: {error}")
        else:
            if not saved_trips:
                st.caption("No saved trips yet.")
            for trip in saved_trips:
                st.markdown(
                    f"**{trip['origin']} → {trip['destination']}**  \n"
                    f"{trip['travel_date']}"
                )
                if st.button("Delete trip", key=f"delete_trip_{trip['id']}"):
                    try:
                        delete_saved_trip(trip["id"])
                    except Exception as error:
                        st.error(f"Could not delete the trip: {error}")
                    else:
                        st.rerun()
    if langchain_is_configured():
        st.caption("LangChain summary memory is enabled.")
    else:
        st.caption("Local preference memory is active. Set GROQ_API_KEY to enable LangChain summaries.")

preferences = {
    **preferences,
    "budget_inr": int(budget) if budget else None,
    "priorities": selected_priorities or list(DEFAULT_PREFERENCES["priorities"]),
    "comfort": selected_comfort,
}
st.session_state.preferences = preferences
try:
    save_preferences(preferences, st.session_state.memory_summary)
except Exception as error:
    st.error(f"Could not save travel preferences: {error}")

st.markdown(
    """
    <div class="hero">
      <div class="eyebrow">A better way to get there</div>
      <h1>Your Comfort, Our Commitment.</h1>
      <p>Find a bus that fits your priorities, then make the most of every stop along the way.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

routes = get_routes(origin, destination)
ranked_routes = rank_routes(routes, preferences)
route_tab, map_tab, itinerary_tab, chat_tab = st.tabs(
    ["Bus options", "Route map", "Itinerary", "Travel chat"]
)

with route_tab:
    st.markdown(
        f'<div class="section-title">{origin} <span style="color:#9aa59e">→</span> {destination}</div>',
        unsafe_allow_html=True,
    )
    if routes:
        st.markdown(
            f'<div class="sample-note">For {travel_date.strftime("%A, %d %B %Y")} · '
            "Example schedule, not live availability</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div class="sample-note">For {travel_date.strftime("%A, %d %B %Y")} · '
            "Estimated options only — no live bus data connected</div>",
            unsafe_allow_html=True,
        )
    if not origin.strip() or not destination.strip():
        st.info("Enter an origin and destination to plan your trip.")
    elif origin.strip().casefold() == destination.strip().casefold():
        st.warning("Choose two different places for your trip.")
    elif not routes:
        st.info(
            "No live bus schedules are connected for this city pair. These planning "
            "estimates are based on road distance; they are not actual operator "
            "listings, confirmed departures, or booking fares."
        )
        try:
            road_route = _cached_road_route(origin.strip(), destination.strip())
        except (LookupError, ValueError, requests.RequestException) as error:
            st.error(f"Could not estimate bus options: {error}")
        else:
            st.caption(
                f"Road distance: {road_route.distance_km:,.0f} km · "
                f"estimated road driving time: {road_route.duration_text}"
            )
            estimated_options = estimate_bus_options(road_route, preferences)
            if not estimated_options:
                st.warning(
                    "No estimated option matches your budget and comfort filters. "
                    "Adjust those preferences to see planning estimates."
                )
            for option in estimated_options:
                hours_min, minutes_min = divmod(option["duration_min"], 60)
                hours_max, minutes_max = divmod(option["duration_max"], 60)
                duration = (
                    f"{hours_min}h {minutes_min:02d}m – "
                    f"{hours_max}h {minutes_max:02d}m"
                )
                st.markdown(
                    f"""
                    <div class="route-card">
                      <div class="route-top">
                        <div><div class="eyebrow">Estimated planning option</div>
                        <div class="operator">{option["bus_type"]}</div></div>
                        <div class="fare">₹{option["fare_min"]:,}–₹{option["fare_max"]:,}</div>
                      </div>
                      <div class="route-times">
                        <strong>{origin}</strong>
                        <div class="route-line">{duration}<br>estimated travel time</div>
                        <strong>{destination}</strong>
                      </div>
                      <div class="chips">Indicative estimate only · verify schedules, fares, transfers, and availability with a bus operator</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
    elif not ranked_routes:
        st.warning("No sample buses match your fare and comfort filters. Try raising the budget or changing comfort preferences.")
    else:
        for index, route in enumerate(ranked_routes, start=1):
            st.markdown(
                f"""
                <div class="route-card">
                  <div class="route-top">
                    <div><div class="eyebrow">Best fit #{index}</div>
                    <div class="operator">{route.operator}</div></div>
                    <div class="fare">₹{route.fare_inr:,}</div>
                  </div>
                  <div class="route-times">
                    <strong>{route.departure}</strong>
                    <div class="route-line">{route.duration_text}<br>{route.transfers} transfers</div>
                    <strong>{route.arrival}</strong>
                  </div>
                  <div class="chips">{route.bus_type} · {route.rating:.1f}★ operator rating</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.caption("Ranked by your selected priorities. Always confirm current times, fares, and operator details before booking.")

with map_tab:
    st.markdown('<div class="section-title">Your route on the map</div>', unsafe_allow_html=True)
    if not origin.strip() or not destination.strip():
        st.info("Enter an origin and destination to show the route.")
    elif origin.strip().casefold() == destination.strip().casefold():
        st.warning("Choose two different places to show a route.")
    else:
        st.caption(f"Estimated road route from {origin} to {destination}.")
        try:
            _show_road_route(origin, destination)
        except (LookupError, ValueError, requests.RequestException) as error:
            st.error(f"Could not display the route: {error}")

with itinerary_tab:
    st.markdown('<div class="section-title">A little more than the ride</div>', unsafe_allow_html=True)
    itinerary = build_itinerary(origin, destination)
    st.markdown(f"#### A flexible day in {destination}")
    for stop in itinerary:
        with st.container(border=True):
            st.markdown(f"**{stop['time']} · {stop['title']}**")
            st.write(stop["description"])
    if st.button("Save this trip", key="save_trip"):
        try:
            save_trip(
                origin=origin.strip(),
                destination=destination.strip(),
                travel_date=travel_date.isoformat(),
                preferences=preferences,
                itinerary=itinerary,
            )
        except Exception as error:
            st.error(f"Could not save this trip: {error}")
        else:
            st.success("Trip saved. You can find it under Saved trips in the sidebar.")
    st.caption("Suggestions are starting points; check local opening hours and transit times.")

with chat_tab:
    st.markdown('<div class="section-title">Tell me how you like to travel</div>', unsafe_allow_html=True)
    st.caption("Try: “I prefer sleeper buses”, “Keep my fare below ₹1,000”, or “Avoid transfers”.")
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Share a preference or ask for a trip idea…"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        reply = _assistant_reply(prompt)
        st.session_state.messages.append({"role": "assistant", "content": reply})
        if langchain_is_configured():
            try:
                st.session_state.memory_summary = summarize_with_langchain(
                    os.environ["GROQ_API_KEY"],
                    st.session_state.memory_summary,
                    prompt,
                    reply,
                )
                save_preferences(st.session_state.preferences, st.session_state.memory_summary)
            except Exception as error:
                st.error(f"Could not update the LangChain summary: {error}")
        st.rerun()
