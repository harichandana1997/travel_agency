# Chandu TripMate — personalized bus trip planner

A Streamlit chat-style prototype for Indian bus-trip planning. It ranks illustrative bus options against fare, transfer, and comfort preferences, then suggests a flexible day itinerary.

Application logic is organized in `src/`: `catalog.py` holds sample data, `route.py` defines bus routes, `planner.py` ranks options and builds itineraries, `memory.py` stores local preferences, and `llm.py` integrates LangChain summary memory.

## Run locally

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

The prototype includes sample bus schedules for selected Indian city pairs. Schedules, fares, ratings, and operator names are examples only—not live inventory or booking advice. For other Indian place pairs, the app shows clearly labeled seater/sleeper planning estimates based on road distance, not real operator listings, confirmed departures, or booking fares. The **Route map** tab looks up an illustrative road route via OpenStreetMap Nominatim and OSRM. The route and bus estimates require internet access and depend on public services with no availability guarantee.

## Database setup

The app uses local SQLite by default. To enable Supabase, first rotate any secret key that was exposed, then copy `.env.example` to `.env` and set `SUPABASE_URL` and `SUPABASE_SECRET_KEY` to your own project values. Keep the secret key server-side: never commit `.env`, put the key in client-side code, or deploy this single-user setup publicly. The publishable key is not used by this local backend.

Run the SQL in `supabase/migrations/202611050001_initial.sql` in the Supabase SQL Editor before starting the app. It creates the preference-memory and saved-trip tables with row-level security enabled and no public policies. The local Streamlit server connects using the secret key. This mode is for a trusted, single-user local prototype only; add Supabase Auth and per-user RLS policies before sharing or deploying it.

Without both Supabase settings, the app continues to store data in `~/.wayfarer/travel_memory.sqlite3`. Supabase errors are shown rather than silently switching backends.

## Preference memory and saved trips

Preferences and the LangChain summary are stored in the selected database. Use **Your travel memory** in the sidebar to review or clear them. Save an itinerary from the **Itinerary** tab, then review or delete it under **Saved trips** in the sidebar.

To use LangChain's `ConversationSummaryMemory` with Groq for chat summaries, set `GROQ_API_KEY` in `.env` before launching Streamlit. The default Groq model is `llama-3.3-70b-versatile`; override it with `GROQ_MODEL` if needed. Summaries are sent to Groq. Do not enter sensitive personal information in chat.

This single-user local-storage design is a prototype. A public deployment needs per-user authentication, scoped storage, and a real-time bus schedule provider.

## Tests

```powershell
python -m unittest discover -s tests
```
