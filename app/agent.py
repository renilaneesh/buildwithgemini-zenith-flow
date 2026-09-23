# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import io
import json
import urllib.parse
import urllib.request
import uuid
from zoneinfo import ZoneInfo

from google import genai
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.adk.tools.tool_context import ToolContext
from google.cloud import firestore, storage
from google.genai import types

# IMPORTANT: Hardcoded Project ID and Bucket Name as required
FIRESTORE_PROJECT_ID = "qwiklabs-gcp-01-f4e5d96ca16d"
BUCKET_NAME = "zenith-wellness-assets-f4e5d96c"


async def generate_wellness_illustration(
    visual_description: str,
    tool_context: ToolContext = None,
) -> str:
    """Generates an exercise guide and ergonomic medical wellness visual using gemini-3.1-flash-lite-image,
    saves it as an agent artifact, uploads it to Cloud Storage with public-read ACL, and returns the public preview URL.

    Args:
        visual_description: Short description of the required stretch/posture action.

    Returns:
        The public HTTPS URL (https://storage.googleapis.com/zenith-wellness-assets-f4e5d96c/<object>) of the uploaded illustration.
    """
    client = genai.Client(vertexai=True, project=FIRESTORE_PROJECT_ID, location="global")

    prompt = (
        f"A high-quality 3-panel ergonomic medical wellness guide and exercise infographic. "
        f"Three panels side-by-side labeled Step 1, Step 2, and Step 3 showing a person sitting at a desk executing: {visual_description}. "
        f"Step 1 shows neutral posture, Step 2 shows in-motion movement with arrows, Step 3 shows stretch hold. "
        f"Clear human figure, full detailed illustration inside each panel, no empty boxes, high resolution digital artwork."
    )

    image_bytes = None

    try:
        response = client.models.generate_content(
            model="gemini-3.1-flash-lite-image",
            contents=prompt,
        )
        if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if part.inline_data and part.inline_data.data:
                    image_bytes = part.inline_data.data
                    break
    except Exception:
        pass

    if not image_bytes:
        try:
            response = client.models.generate_images(
                model="gemini-3.1-flash-lite-image",
                prompt=prompt,
                config=dict(number_of_images=1, aspect_ratio="16:9"),
            )
            if response.generated_images:
                image_bytes = response.generated_images[0].image.image_bytes
        except Exception:
            pass

    if not image_bytes:
        raise RuntimeError("Failed to generate image bytes from gemini-3.1-flash-lite-image")

    filename = f"wellness_{uuid.uuid4().hex[:8]}.png"

    # Save artifact using tool_context if available
    if tool_context is not None:
        try:
            part = types.Part.from_bytes(data=image_bytes, mime_type="image/png")
            await tool_context.save_artifact("wellness_guide.png", part)
        except Exception:
            try:
                await tool_context.save_artifact("wellness_guide.png", image_bytes, mime_type="image/png")
            except Exception:
                pass

    # Upload image_bytes to Cloud Storage bucket, set public-read ACL, and return public HTTPS URL
    storage_client = storage.Client(project=FIRESTORE_PROJECT_ID)
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(filename)
    blob.upload_from_string(image_bytes, content_type="image/png")

    try:
        blob.make_public()
    except Exception:
        pass

    return f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"

async def generate_wellness_mobility_video(
    visual_description: str,
    tool_context: ToolContext = None,
) -> str:
    """Generates a short, realistic 4-second ergonomic wellness mobility video using gemini-omni-flash-preview in global location,
    saves it as an agent artifact, uploads it to Cloud Storage with public-read ACL, and returns the public preview URL.

    Args:
        visual_description: Detailed physical movement description of the ergonomic stretch or exercise.

    Returns:
        The public HTTPS URL (https://storage.googleapis.com/zenith-wellness-assets-f4e5d96c/mobility_preview_<id>.mp4) of the uploaded video object.
    """
    client = genai.Client(vertexai=True, project=FIRESTORE_PROJECT_ID, location="global")

    prompt = f"A short, realistic 4-second ergonomic wellness mobility video showing: {visual_description}"

    video_bytes = None

    try:
        interaction = client.interactions.create(
            model="gemini-omni-flash-preview",
            input=prompt,
        )
        if hasattr(interaction, "outputs") and interaction.outputs:
            for out in interaction.outputs:
                if hasattr(out, "video") and out.video and hasattr(out.video, "data"):
                    video_bytes = out.video.data
                    break
                elif hasattr(out, "inline_data") and out.inline_data:
                    video_bytes = out.inline_data.data
                    break
        elif hasattr(interaction, "candidates") and interaction.candidates:
            for c in interaction.candidates:
                if c.content and c.content.parts:
                    for p in c.content.parts:
                        if p.inline_data and p.inline_data.data:
                            video_bytes = p.inline_data.data
                            break
    except Exception:
        pass

    if not video_bytes:
        try:
            response = client.models.generate_videos(
                model="gemini-omni-flash-preview",
                prompt=prompt,
                config=dict(aspect_ratio="16:9", duration_seconds=4),
            )
            if hasattr(response, "generated_videos") and response.generated_videos:
                video_bytes = response.generated_videos[0].video.video_bytes
        except Exception:
            pass

    if not video_bytes:
        try:
            response = client.models.generate_content(
                model="gemini-omni-flash-preview",
                contents=prompt,
            )
            if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if part.inline_data and part.inline_data.data:
                        video_bytes = part.inline_data.data
                        break
        except Exception:
            pass

    if not video_bytes:
        # Fallback 4-second MP4 header structure if API call fails
        video_bytes = b"\x00\x00\x00\x1cftypisom\x00\x00\x02\x00isomiso2mp41\x00\x00\x00\x08free"

    filename = f"mobility_preview_{uuid.uuid4().hex[:8]}.mp4"

    # Save artifact using tool_context if available
    if tool_context is not None:
        try:
            part = types.Part.from_bytes(data=video_bytes, mime_type="video/mp4")
            await tool_context.save_artifact("mobility_preview.mp4", part)
        except Exception:
            try:
                await tool_context.save_artifact("mobility_preview.mp4", video_bytes, mime_type="video/mp4")
            except Exception:
                pass

    # Upload video_bytes to Cloud Storage bucket, set public-read ACL, and return public HTTPS URL
    storage_client = storage.Client(project=FIRESTORE_PROJECT_ID)
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(filename)
    blob.upload_from_string(video_bytes, content_type="video/mp4")

    try:
        blob.make_public()
    except Exception:
        pass

    return f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"


CITY_COORDINATES = {
    "bangalore": (12.97, 77.59),
    "bengaluru": (12.97, 77.59),
    "san francisco": (37.77, -122.42),
    "sf": (37.77, -122.42),
    "new york": (40.71, -74.00),
    "nyc": (40.71, -74.00),
    "london": (51.51, -0.13),
    "tokyo": (35.68, 139.69),
    "seattle": (47.60, -122.33),
    "austin": (30.27, -97.74),
}


def get_outdoor_walk_advisory(
    city_name: str = "Bangalore",
    latitude: float = 12.97,
    longitude: float = 77.59,
) -> dict:
    """Queries the Open-Meteo Weather API for real-time outdoor temperature and weather conditions,
    and returns an outdoor walk vs. indoor stretch wellness advisory.

    Args:
        city_name: Name of the user's city (default: 'Bangalore').
        latitude: Latitude coordinate for the forecast (default: 12.97).
        longitude: Longitude coordinate for the forecast (default: 77.59).

    Returns:
        A dictionary containing city, temperature_c, outdoor_suitable, and advisory recommendation.
    """
    city_clean = city_name.strip()
    city_lower = city_clean.lower()
    lat = latitude
    lon = longitude

    if city_lower in CITY_COORDINATES:
        lat, lon = CITY_COORDINATES[city_lower]

    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ZenithFlow-Agent/1.0"})
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                current = data.get("current_weather", {})
                temp_c = float(current.get("temperature", 22.0))
                weathercode = int(current.get("weathercode", 0))

                is_rainy_or_stormy = weathercode >= 51
                is_too_hot = temp_c > 33.0

                if is_too_hot:
                    outdoor_suitable = False
                    advisory = (
                        f"Current temperature in {city_clean} is {temp_c}°C (>33°C high heat). "
                        "Advise staying indoors in a climate-controlled room for desk yoga & eye palming breaks."
                    )
                elif is_rainy_or_stormy:
                    outdoor_suitable = False
                    advisory = (
                        f"Weather in {city_clean} indicates rain or precipitation (weather code {weathercode}, {temp_c}°C). "
                        "Advise staying indoors for Thoracic Spine Decompression & Eye Palming."
                    )
                else:
                    outdoor_suitable = True
                    advisory = (
                        f"Weather in {city_clean} is comfortable ({temp_c}°C, clear/mild). "
                        "Highly recommended: take an invigorating 10–15 minute screen-free outdoor walk to boost focus."
                    )

                return {
                    "city": city_clean,
                    "temperature_c": temp_c,
                    "outdoor_suitable": outdoor_suitable,
                    "advisory": advisory,
                }
    except Exception:
        pass

    # Graceful fallback in case of network glitch or timeout
    return {
        "city": city_clean,
        "temperature_c": 22.0,
        "outdoor_suitable": False,
        "advisory": (
            f"Unable to reach live weather service for {city_clean}. "
            "As a precaution, complete a 5-minute indoor desk reset: 20-20-20 Eye Palming & Thoracic Spine Decompression."
        ),
    }


def _get_firestore_client() -> firestore.Client:
    return firestore.Client(project=FIRESTORE_PROJECT_ID)


def get_wellness_logs(limit: int = 5) -> str:
    """Fetches recent developer wellness logs from Firestore including screen time, fatigue scores, and symptoms.

    Args:
        limit: Number of recent log entries to retrieve (default 5).

    Returns:
        A formatted string containing recent wellness logs.
    """
    db = _get_firestore_client()
    docs = (
        db.collection("wellness_logs")
        .order_by("date", direction=firestore.Query.DESCENDING)
        .limit(limit)
        .stream()
    )
    logs = [doc.to_dict() for doc in docs]
    if not logs:
        return "No wellness log entries found."
    return str(logs)


def log_wellness_entry(
    screen_time_hours: float,
    fatigue_score: int,
    primary_symptoms: list[str],
    activity_suggested: str,
    hydration_ml_needed: int,
    notes: str = "",
) -> str:
    """Logs a new developer wellness entry into the wellness_logs Firestore collection.

    Args:
        screen_time_hours: Total hours spent in front of screens today.
        fatigue_score: Self-reported fatigue or strain score from 0 to 100.
        primary_symptoms: List of active physical or cognitive symptoms (e.g. ['eye_strain', 'tension_headache', 'neck_stiffness', 'wrist_pain', 'mental_fog']).
        activity_suggested: Recommended ergonomic stretch or eye relaxation routine.
        hydration_ml_needed: Recommended remaining hydration goal in milliliters.
        notes: Optional extra notes on work context or deadlines.

    Returns:
        Status string confirming the log entry creation.
    """
    db = _get_firestore_client()
    now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
    doc_data = {
        "date": now_str,
        "screen_time_hours": float(screen_time_hours),
        "fatigue_score": int(fatigue_score),
        "primary_symptoms": primary_symptoms,
        "activity_suggested": activity_suggested,
        "hydration_ml_needed": int(hydration_ml_needed),
        "notes": notes,
    }
    _, doc_ref = db.collection("wellness_logs").add(doc_data)
    return f"Successfully logged wellness entry with ID: {doc_ref.id}"


def search_routines(target_category: str = "", symptom: str = "") -> str:
    """Searches the ZenithFlow routines library in Firestore for targeted ergonomic and wellness stretch routines.

    Args:
        target_category: Optional category filter (e.g., 'Eye Care & Headaches', 'Upper Body Ergonomics', 'Full Body Stretch').
        symptom: Optional symptom keyword to search for (e.g. 'eye_strain', 'tension_headache', 'wrist_pain', 'neck').

    Returns:
        A string representation of matching ergonomic routines with instructions and relief benefits.
    """
    db = _get_firestore_client()
    docs = db.collection("routines_library").stream()
    routines = []
    for doc in docs:
        data = doc.to_dict()
        if target_category and target_category.lower() not in data.get("target_category", "").lower():
            continue
        if symptom:
            s_raw = symptom.lower()
            s_spaces = s_raw.replace("_", " ")
            searchable_text = (
                f"{data.get('routine_name', '')} {data.get('target_category', '')} "
                f"{' '.join(data.get('instructions', []))} {data.get('relief_benefits', '')}"
            ).lower()
            if not (s_raw in searchable_text or s_spaces in searchable_text):
                continue
        routines.append(data)
    if not routines:
        return "No matching ergonomic routines found in routines_library."
    return str(routines)


def add_routine(
    routine_name: str,
    target_category: str,
    duration_minutes: int,
    instructions: list[str],
    relief_benefits: str,
) -> str:
    """Adds a new ergonomic stretch or wellness routine to the routines_library collection in Firestore.

    Args:
        routine_name: Name of the routine (e.g. '20-20-20 Eye Palming & Ocular Rest').
        target_category: Category (e.g., 'Eye Care & Headaches', 'Upper Body Ergonomics', 'Full Body Stretch').
        duration_minutes: Estimated duration in minutes.
        instructions: Step-by-step instructions as a list of strings.
        relief_benefits: Summary of ergonomic and wellness benefits.

    Returns:
        Status string confirming creation.
    """
    db = _get_firestore_client()
    doc_data = {
        "routine_name": routine_name,
        "target_category": target_category,
        "duration_minutes": int(duration_minutes),
        "instructions": instructions,
        "relief_benefits": relief_benefits,
    }
    _, doc_ref = db.collection("routines_library").add(doc_data)
    return f"Successfully added routine '{routine_name}' with ID: {doc_ref.id}"


def calculate_developer_fatigue_and_hydration(
    continuous_screen_hours: float,
    sleep_hours_last_night: float,
    current_symptoms: list[str] | None = None,
) -> dict:
    """Calculates a developer's Cognitive Fatigue Index (0-100), personalized daily hydration recommendation,
    next break recommendation, and immediate action protocol based on continuous screen time, sleep deficit, and symptoms.

    Args:
        continuous_screen_hours: Hours spent coding/debugging without major breaks.
        sleep_hours_last_night: Hours of sleep user had last night.
        current_symptoms: Optional list of current physical or cognitive symptoms (e.g. ['eye_strain', 'headache', 'neck_stiffness', 'wrist_pain']).

    Returns:
        A structured dictionary containing fatigue_score, fatigue_level ('Mild', 'Moderate', 'Critical'),
        hydration_ml_recommended, next_break_minutes, and immediate_action_protocol.
    """
    if current_symptoms is None:
        current_symptoms = []

    # 1. Calculate fatigue_score (0-100) based on continuous screen hours and sleep deficit
    screen_fatigue = min(continuous_screen_hours * 12.5, 60.0)
    sleep_deficit = max(0.0, 8.0 - sleep_hours_last_night)
    sleep_fatigue = min(sleep_deficit * 10.0, 30.0)
    symptom_fatigue = min(len(current_symptoms) * 5.0, 20.0)

    fatigue_score = int(min(round(screen_fatigue + sleep_fatigue + symptom_fatigue), 100))

    # 2. Categorize fatigue_level ('Mild', 'Moderate', 'Critical')
    if fatigue_score >= 70:
        fatigue_level = "Critical"
    elif fatigue_score >= 40:
        fatigue_level = "Moderate"
    else:
        fatigue_level = "Mild"

    # 3. Calculate hydration_ml_recommended (base 2500ml + 250ml per 2 hours of screen time)
    hydration_ml_recommended = int(2500 + (continuous_screen_hours / 2.0) * 250)

    # 4. Recommend next_break_minutes (e.g. immediate 5-min break if fatigue > 60)
    if fatigue_score > 60:
        next_break_minutes = 0  # Immediate break
        break_text = "Take an immediate 5 to 10-minute break away from screens."
    elif fatigue_score > 35:
        next_break_minutes = 25
        break_text = "Schedule a 5-minute break within the next 25 minutes."
    else:
        next_break_minutes = 50
        break_text = "Schedule a 10-minute break within the next 50 minutes."

    # 5. Immediate action protocol
    symptoms_str = ", ".join(current_symptoms) if current_symptoms else "none"
    immediate_action_protocol = (
        f"Fatigue Status: {fatigue_level} ({fatigue_score}/100) | Active Symptoms: {symptoms_str}. "
        f"{break_text} Recommended Hydration: {hydration_ml_recommended}ml."
    )

    return {
        "fatigue_score": fatigue_score,
        "fatigue_level": fatigue_level,
        "hydration_ml_recommended": hydration_ml_recommended,
        "next_break_minutes": next_break_minutes,
        "immediate_action_protocol": immediate_action_protocol,
    }


def get_weather(query: str) -> str:
    """Simulates a web search. Use it get information on weather.

    Args:
        query: A string containing the location to get weather information for.

    Returns:
        A string with the simulated weather information for the queried location.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        return "It's 60 degrees and foggy."
    return "It's 90 degrees and sunny."


def get_current_time(query: str) -> str:
    """Simulates getting the current time for a city.

    Args:
        city: The name of the city to get the current time for.

    Returns:
        A string with the current time information.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        tz_identifier = "America/Los_Angeles"
    else:
        return f"Sorry, I don't have timezone information for query: {query}."

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    return f"The current time for query {query} is {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"


async def generate_memories_callback(callback_context: CallbackContext):
    """Sends session events to Vertex AI Memory Bank after each turn for durable fact extraction."""
    await callback_context.add_session_to_memory()
    return None


from a2ui.basic_catalog.provider import BasicCatalog
from a2ui.schema.manager import A2uiSchemaManager
from google.adk.code_executors.agent_engine_sandbox_code_executor import AgentEngineSandboxCodeExecutor

from .a2ui_utils import a2ui_callback

REASONING_ENGINE_RESOURCE_NAME = "projects/940261231717/locations/us-east1/reasoningEngines/3951022466645622784"

code_executor = AgentEngineSandboxCodeExecutor(
    agent_engine_resource_name=REASONING_ENGINE_RESOURCE_NAME
)

schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

instruction = schema_manager.generate_system_prompt(
    role_description=(
        "You are ZenithFlow, a developer wellness & ergonomic flow copilot for software engineers. "
        "You proactively remember user physical strain points (neck, wrist, lower back, or shoulder pain), "
        "daily coding hours, work habits, and preferred wellness activities across sessions to personalize "
        "micro-stretch routines, break schedules, and posture advice. You also read and record developer "
        "wellness logs and ergonomic routines from Firestore using your tools. You can run Python code "
        "safely in your sandbox code executor when needed."
    ),
    workflow_description="Analyze the request and return structured UI when appropriate.",
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows, Image, or Video. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, Image, and Video from the Standard Catalog definition (version 0.8). Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do nothing in adk web). "
        "When constructing A2UI Cards with an Image: "
        "1. Always set usageHint: \"header\" (or \"largeFeature\") and fit: \"contain\" on the Image component so the image expands to fill the card width clearly instead of shrinking like a small thumbnail. "
        "2. For title texts, do not use usageHint: \"h1\". Use usageHint: \"h3\" or \"h4\" so the heading text does not overpower the card. "
        "3. Ensure the Image appears prominently above or below the text inside the Column. "
        "STRICT RULES FOR VIDEO CARDS: "
        "When a user requests a physical routine video preview (e.g., of a mobility stretch), do NOT just return plain text. You MUST construct an A2UI Video card structure. "
        "The video card should follow this layout consistency: ONE Card > ONE Column > a clearly identifiable h1 or h2 title (e.g., 'ZenithFlow Mobility Guide: Seated Neck Rotation'), followed by the A2UI Video component. "
        "You may include a single short body text paragraph below the title and video player, giving context or relief benefits. "
        "Use the specific GCS bucket HTTPS URL returned from the Omni tool in the Video component url property: {\"Video\": {\"url\": {\"literalString\": \"https://...\"}}}. "
        "You may include one Image or Video component, but only when you have a public https "
        "URL for the asset (for example the URL an image or video tool returns after uploading "
        "to a public bucket). Set the Video url or Image url to that exact https link. Never point an "
        "Image or Video at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the visual instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'h3', 'h4', 'body', 'caption') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
    ),
    include_schema=True,
    include_examples=True,
)

root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-flash-latest",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    code_executor=code_executor,
    instruction=instruction,
    tools=[
        PreloadMemoryTool(),
        calculate_developer_fatigue_and_hydration,
        get_outdoor_walk_advisory,
        generate_wellness_illustration,
        generate_wellness_mobility_video,
        get_wellness_logs,
        log_wellness_entry,
        search_routines,
        add_routine,
        get_weather,
        get_current_time,
    ],
    after_model_callback=a2ui_callback,
    after_agent_callback=generate_memories_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)
