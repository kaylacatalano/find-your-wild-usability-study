import base64
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import pandas as pd
import requests
import streamlit as st


# ---------------------------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------------------------

st.set_page_config(
    page_title="Find Your Wild Usability Study",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ---------------------------------------------------------
# CONSTANTS AND STUDY FLOW
# ---------------------------------------------------------

STUDY_STEPS = [
    "Welcome",
    "Consent",
    "Demographics",
    "Introduction",
    "Task 1",
    "Task 1 Reflection",
    "Task 2",
    "Task 2 Reflection",
    "Task 3",
    "Task 3 Reflection",
    "Exit Survey",
    "Thank You",
]

STATE_CODES = {
    "Alaska": "AK",
    "Arizona": "AZ",
    "California": "CA",
    "Colorado": "CO",
    "Florida": "FL",
    "Idaho": "ID",
    "Montana": "MT",
    "Nevada": "NV",
    "New Mexico": "NM",
    "Oregon": "OR",
    "South Dakota": "SD",
    "Texas": "TX",
    "Utah": "UT",
    "Washington": "WA",
    "Wyoming": "WY",
}

ACTIVITY_OPTIONS = [
    "Boating",
    "Camping",
    "Fishing",
    "Hiking",
    "Photography",
    "Rock Climbing",
    "Scenic Driving",
    "Wildlife Watching",
]

PARTICIPANT_DEFAULTS = {
    "consent": False,
    "age_range": "",
    "visited_national_park": "",
    "travel_app_frequency": "",
    "device_type": "",
    "browser": "",
    "task1_ease": 3,
    "task1_completion": "",
    "task1_confusion": "",
    "task1_comments": "",
    "task2_ease": 3,
    "task2_completion": "",
    "task2_confusion": "",
    "task2_comments": "",
    "task3_ease": 3,
    "task3_completion": "",
    "task3_confusion": "",
    "task3_comments": "",
    "overall_satisfaction": 3,
    "most_useful_feature": "",
    "least_useful_feature": "",
    "would_use_again": "",
    "improvement_suggestion": "",
}


# ---------------------------------------------------------
# SESSION STATE
# ---------------------------------------------------------

if "current_step" not in st.session_state:
    st.session_state.current_step = 0

if "participant" not in st.session_state:
    st.session_state.participant = {}

for field, default_value in PARTICIPANT_DEFAULTS.items():
    st.session_state.participant.setdefault(field, default_value)

if "participant_id" not in st.session_state:
    st.session_state.participant_id = f"P-{uuid4().hex[:8].upper()}"

if "study_submitted" not in st.session_state:
    st.session_state.study_submitted = False


# ---------------------------------------------------------
# VISUAL STYLING
# ---------------------------------------------------------

st.markdown(
    """
    <style>
        .stApp {
            background-color: #f4f1e8;
            color: #243126;
        }

        [data-testid="stHeader"] {
            background: transparent;
        }

        [data-testid="stToolbar"] {
            right: 1rem;
        }

        .block-container {
            max-width: 1120px;
            padding-top: 2rem;
            padding-bottom: 4rem;
        }

        h1, h2, h3 {
            color: #1f3a2e;
            letter-spacing: -0.02em;
        }

        h1 {
            font-size: 3.4rem !important;
            font-weight: 750 !important;
            line-height: 1.05 !important;
        }

        h2 {
            font-size: 2rem !important;
            font-weight: 700 !important;
        }

        p, li, label {
            color: #33443a;
            font-size: 1.03rem;
            line-height: 1.7;
        }

        [data-testid="stProgressBar"] > div > div {
            background-color: #2f654d;
        }

        [data-testid="stProgressBar"] > div {
            background-color: #d8ded4;
        }

        .stButton > button {
            min-height: 3.1rem;
            border-radius: 8px;
            border: 1px solid #2f654d;
            background-color: #1f2933;
            color: #f4f1e8 !important;
            font-weight: 650;
            transition: all 0.2s ease;
        }

        .stButton > button:hover {
            border-color: #1f4937;
            transform: translateY(-1px);
        }

        .stButton > button[kind="primary"] {
            background-color: #2f654d;
            color: #f4f1e8 !important;
            border-color: #2f654d;
        }

        .stButton > button p {
            color: #f4f1e8 !important;
        }

        .stButton > button[kind="primary"]:hover {
            background-color: #244f3c;
            border-color: #244f3c;
        }

        .study-progress-label {
            color: #607066;
            font-size: 0.86rem;
            font-weight: 650;
            letter-spacing: 0.08em;
            margin-bottom: 0.45rem;
            text-transform: uppercase;
        }

        .step-caption {
            color: #6a786f;
            font-size: 0.9rem;
            margin-top: 0.45rem;
        }

        .hero-shell {
            background-color: rgba(255, 255, 255, 0.74);
            border: 1px solid #d9ddd4;
            border-radius: 18px;
            padding: 1.2rem;
            margin-top: 1.2rem;
            margin-bottom: 1.6rem;
            box-shadow: 0 18px 45px rgba(27, 45, 34, 0.12);
        }

        .hero-eyebrow {
            color: #5f7467;
            font-size: 0.82rem;
            font-weight: 700;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            margin-bottom: 0.6rem;
        }

        .hero-copy {
            color: #33443a;
            font-size: 1.2rem;
            line-height: 1.65;
        }

        .study-details {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1rem;
            margin: 1rem 0 1.7rem 0;
        }

        .study-detail {
            background-color: rgba(255, 255, 255, 0.72);
            border: 1px solid #d9ddd4;
            border-radius: 12px;
            padding: 1.1rem;
        }

        .study-detail-label {
            color: #6a786f;
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            margin-bottom: 0.35rem;
            text-transform: uppercase;
        }

        .study-detail-value {
            color: #233b2f;
            font-size: 1.05rem;
            font-weight: 650;
        }

        [data-testid="stImage"] img {
            border-radius: 14px;
        }

        @media (max-width: 800px) {
            .block-container {
                padding-left: 1rem;
                padding-right: 1rem;
            }

            .study-details {
                grid-template-columns: 1fr;
            }
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# GENERAL HELPERS
# ---------------------------------------------------------

def get_local_image_data(image_path: str):
    path = Path(image_path)
    if not path.exists():
        return None

    encoded_image = base64.b64encode(path.read_bytes()).decode()
    file_extension = path.suffix.lower().replace(".", "")
    if file_extension == "jpg":
        file_extension = "jpeg"
    return f"data:image/{file_extension};base64,{encoded_image}"


def go_next():
    if st.session_state.current_step < len(STUDY_STEPS) - 1:
        st.session_state.current_step += 1


def go_back():
    if st.session_state.current_step > 0:
        st.session_state.current_step -= 1


def show_progress():
    current = st.session_state.current_step + 1
    total = len(STUDY_STEPS)

    st.markdown(
        '<div class="study-progress-label">Study Progress</div>',
        unsafe_allow_html=True,
    )
    st.progress(current / total)
    st.markdown(
        f'<div class="step-caption">Step {current} of {total}</div>',
        unsafe_allow_html=True,
    )


def show_navigation(show_back=True, next_label="Continue"):
    st.write("")
    left, spacer, right = st.columns([1, 2.5, 1])

    with left:
        if show_back:
            st.button(
                "Back",
                on_click=go_back,
                use_container_width=True,
            )

    with right:
        st.button(
            next_label,
            on_click=go_next,
            use_container_width=True,
            type="primary",
        )


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_parks(api_key: str, params_items: tuple):
    params = dict(params_items)
    response = requests.get(
        "https://developer.nps.gov/api/v1/parks",
        params={"api_key": api_key, **params},
        timeout=15,
    )
    response.raise_for_status()
    return response.json().get("data", [])


def get_hero_image_url():
    """Return a scenic image from the exact Yellowstone park record."""
    try:
        api_key = st.secrets["NPS_API_KEY"]
        parks = fetch_parks(
            api_key,
            tuple(sorted({"parkCode": "yell", "limit": 1}.items())),
        )
        if parks and parks[0].get("images"):
            images = parks[0]["images"]
            # Prefer a later image when available; the first image is sometimes
            # a building or visitor center rather than a landscape.
            preferred_index = 1 if len(images) > 1 else 0
            return images[preferred_index].get("url")
    except (KeyError, requests.RequestException):
        return None

    return None


def normalize_activity_name(value):
    return " ".join(str(value).lower().replace("-", " ").split())


def filter_parks_by_activities(parks, selected_activities):
    """Match any selected activity using case-insensitive normalized names."""
    if not selected_activities:
        return parks

    selected = {
        normalize_activity_name(activity)
        for activity in selected_activities
    }

    filtered = []
    for park in parks:
        available = {
            normalize_activity_name(activity.get("name", ""))
            for activity in park.get("activities", [])
            if activity.get("name")
        }

        # OR behavior is more natural for a discovery tool and avoids a search
        # failing simply because a park lacks one of several optional interests.
        if selected.intersection(available):
            filtered.append(park)

    return filtered


def filter_and_rank_parks_by_name(parks, park_name):
    """Keep results whose park names match the participant's search terms.

    The NPS q parameter searches descriptions and other text too, so a query
    such as "Yellowstone National Park" can otherwise return unrelated sites.
    """
    query = " ".join(park_name.lower().split())
    if not query:
        return parks

    query_tokens = [
        token for token in query.split()
        if token not in {"national", "park", "site", "monument", "preserve"}
    ]

    ranked = []
    for park in parks:
        full_name = " ".join(park.get("fullName", "").lower().split())
        score = 0

        if full_name == query:
            score = 100
        elif full_name.startswith(query):
            score = 90
        elif query in full_name:
            score = 80
        elif query_tokens and all(token in full_name for token in query_tokens):
            score = 70
        elif query_tokens and any(token in full_name for token in query_tokens):
            score = 50

        if score:
            ranked.append((score, full_name, park))

    ranked.sort(key=lambda item: (-item[0], item[1]))
    return [park for _, _, park in ranked]


def display_park_results(parks):
    st.subheader("Matching Parks")
    st.write(
        "Review the parks below. Each result includes basic information "
        "from the National Park Service."
    )

    for park in parks:
        with st.container(border=True):
            image_url = None
            if park.get("images"):
                image_url = park["images"][0].get("url")

            image_column, detail_column = st.columns([1, 2])

            with image_column:
                if image_url:
                    st.image(
                        image_url,
                        use_container_width=True,
                    )
                else:
                    st.caption("No park image is available for this result.")

            with detail_column:
                park_name = park.get("fullName", "Unnamed park")
                st.subheader(park_name)

                location_parts = [
                    value
                    for value in [
                        park.get("states", ""),
                        park.get("designation", ""),
                    ]
                    if value
                ]
                if location_parts:
                    st.caption(" | ".join(location_parts))

                description = park.get("description", "")
                if description:
                    st.write(description)

                activity_names = [
                    activity.get("name", "")
                    for activity in park.get("activities", [])
                    if activity.get("name")
                ]
                if activity_names:
                    st.write(
                        "**Activities:** " + ", ".join(activity_names[:10])
                    )

                official_url = park.get("url")
                if official_url:
                    st.markdown(f"[View the official park page]({official_url})")


def save_study_results():
    if st.session_state.study_submitted:
        return

    project_directory = Path(__file__).resolve().parent
    data_directory = project_directory / "data"
    data_directory.mkdir(parents=True, exist_ok=True)

    results_file = data_directory / "usability_results.csv"

    participant_record = {
        "participant_id": st.session_state.participant_id,
        "submitted_at": datetime.now().isoformat(timespec="seconds"),
        **st.session_state.participant,
    }

    new_record_df = pd.DataFrame([participant_record])

    if results_file.exists():
        new_record_df.to_csv(
            results_file,
            mode="a",
            header=False,
            index=False,
        )
    else:
        new_record_df.to_csv(
            results_file,
            index=False,
        )

    st.session_state.study_submitted = True


def submit_study():
    save_study_results()
    go_next()


# ---------------------------------------------------------
# PAGE COMPONENTS
# ---------------------------------------------------------

def welcome_page():
    hero_image = get_hero_image_url()

    st.markdown('<div class="hero-shell">', unsafe_allow_html=True)

    if hero_image:
        st.image(
            hero_image,
            use_container_width=True,
        )

    st.markdown(
        '<div class="hero-eyebrow">Remote Usability Study</div>',
        unsafe_allow_html=True,
    )
    st.title("Find Your Wild")
    st.markdown(
        '<div class="hero-copy">'
        "Help us improve a digital experience designed to make discovering "
        "and exploring United States National Parks easier and more engaging."
        "</div>",
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown(
        """
        <div class="study-details">
            <div class="study-detail">
                <div class="study-detail-label">Estimated Time</div>
                <div class="study-detail-value">10 to 15 minutes</div>
            </div>
            <div class="study-detail">
                <div class="study-detail-label">Activities</div>
                <div class="study-detail-value">Three guided tasks</div>
            </div>
            <div class="study-detail">
                <div class="study-detail-label">Format</div>
                <div class="study-detail-value">Self-guided and remote</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        st.subheader("Thank you for participating")
        st.write(
            "During this study, you will explore the Find Your Wild National "
            "Parks application and complete three short activities. After "
            "each activity, you will answer a few questions about your experience."
        )
        st.info(
            "Please complete the study in one sitting and move through each "
            "section in order. We are evaluating the application, not your "
            "personal performance."
        )

    st.button(
        "Begin Study",
        on_click=go_next,
        use_container_width=True,
        type="primary",
    )


def consent_page():
    st.title("Participant Consent")
    st.write("Before beginning the study, please review the information below.")

    with st.container(border=True):
        st.subheader("Study Purpose")
        st.write(
            "This study evaluates the usability of Find Your Wild, a web "
            "application designed to help people discover and explore United "
            "States National Parks."
        )
        st.write(
            "Your feedback will help identify opportunities to improve "
            "navigation, clarity, and the overall user experience."
        )

        st.divider()
        st.subheader("What You Will Do")
        st.markdown(
            """
            - Complete three short activities using the application
            - Answer brief questions after each activity
            - Provide final feedback about your experience
            """
        )
        st.write("**Estimated time:** 10 to 15 minutes")

        st.divider()
        st.subheader("Participation and Privacy")
        st.write(
            "Participation is voluntary. You may stop participating at any "
            "time without penalty."
        )
        st.write(
            "No personally identifiable information will be requested. "
            "Responses will be used only for educational purposes as part of "
            "a university usability-testing project."
        )

    agreed = st.checkbox(
        "I have read the information above and voluntarily agree to "
        "participate in this usability study.",
        value=st.session_state.participant["consent"],
        key="consent_checkbox",
    )
    st.session_state.participant["consent"] = agreed

    st.write("")
    left, spacer, right = st.columns([1, 2.5, 1])
    with left:
        st.button("Back", on_click=go_back, use_container_width=True)
    with right:
        st.button(
            "I Agree & Continue",
            on_click=go_next,
            use_container_width=True,
            type="primary",
            disabled=not agreed,
        )


def demographics_page():
    st.title("About You")
    st.write(
        "Please answer a few short questions about your background and the "
        "device you are using today."
    )

    age_options = [
        "Select an option",
        "Under 18",
        "18–24",
        "25–34",
        "35–44",
        "45–54",
        "55 or older",
    ]
    frequency_options = [
        "Select an option",
        "Frequently",
        "Occasionally",
        "Rarely",
        "Never",
    ]
    device_options = [
        "Select an option",
        "Desktop computer",
        "Laptop computer",
        "Tablet",
        "Mobile phone",
    ]
    browser_options = [
        "Select an option",
        "Chrome",
        "Safari",
        "Firefox",
        "Microsoft Edge",
        "Other",
    ]

    with st.container(border=True):
        age_range = st.selectbox(
            "What is your age range?",
            age_options,
            index=(
                age_options.index(st.session_state.participant["age_range"])
                if st.session_state.participant["age_range"] in age_options
                else 0
            ),
        )

        visited_national_park = st.radio(
            "Have you visited a United States National Park before?",
            ["Yes", "No"],
            index=(
                ["Yes", "No"].index(
                    st.session_state.participant["visited_national_park"]
                )
                if st.session_state.participant["visited_national_park"]
                in ["Yes", "No"]
                else None
            ),
        )

        travel_app_frequency = st.selectbox(
            "How often do you use travel or outdoor recreation websites or apps?",
            frequency_options,
            index=(
                frequency_options.index(
                    st.session_state.participant["travel_app_frequency"]
                )
                if st.session_state.participant["travel_app_frequency"]
                in frequency_options
                else 0
            ),
        )

        device_type = st.selectbox(
            "What type of device are you using for this study?",
            device_options,
            index=(
                device_options.index(st.session_state.participant["device_type"])
                if st.session_state.participant["device_type"] in device_options
                else 0
            ),
        )

        browser = st.selectbox(
            "Which web browser are you using?",
            browser_options,
            index=(
                browser_options.index(st.session_state.participant["browser"])
                if st.session_state.participant["browser"] in browser_options
                else 0
            ),
        )

    st.session_state.participant["age_range"] = age_range
    st.session_state.participant["visited_national_park"] = (
        visited_national_park or ""
    )
    st.session_state.participant["travel_app_frequency"] = travel_app_frequency
    st.session_state.participant["device_type"] = device_type
    st.session_state.participant["browser"] = browser

    form_complete = all(
        [
            age_range != "Select an option",
            visited_national_park in ["Yes", "No"],
            travel_app_frequency != "Select an option",
            device_type != "Select an option",
            browser != "Select an option",
        ]
    )

    if not form_complete:
        st.caption("Please answer every question before continuing.")

    st.write("")
    left, spacer, right = st.columns([1, 2.5, 1])
    with left:
        st.button("Back", on_click=go_back, use_container_width=True)
    with right:
        st.button(
            "Continue to Introduction",
            on_click=go_next,
            use_container_width=True,
            type="primary",
            disabled=not form_complete,
        )


def introduction_page():
    st.title("Introducing Find Your Wild")
    st.write(
        "You are about to explore an interactive application designed to "
        "help people discover National Parks across the United States."
    )

    with st.container(border=True):
        st.subheader("During the study, you will")
        st.markdown(
            """
            - Search for National Parks
            - Use filters to narrow the results
            - Review matching park names, photos, and descriptions
            - Compare activities and basic park information
            - Complete three guided activities
            """
        )

        st.divider()
        st.subheader("A few reminders")
        st.markdown(
            """
            - There are no right or wrong answers.
            - If something feels confusing, that is useful feedback.
            - Complete each activity as naturally as possible.
            - We are evaluating the application, not you.
            """
        )
        st.success("When you are ready, continue to Activity 1.")

    show_navigation(next_label="Begin Activity 1")


def find_your_wild_app(task_key: str, show_park_name=True):
    st.subheader("Search & Filters")
    st.write(
        "Use the options below to discover national parks that match your interests."
    )

    selected_states = st.multiselect(
        "Select State(s)",
        options=list(STATE_CODES.keys()),
        placeholder="Select one or more states",
        key=f"{task_key}_states",
    )

    selected_activities = st.multiselect(
        "Activities",
        options=ACTIVITY_OPTIONS,
        placeholder="Choose activities",
        key=f"{task_key}_activities",
    )

    if show_park_name:
        park_name = st.text_input(
            "Search by Park Name",
            placeholder="Enter a park name",
            key=f"{task_key}_park_name",
        )
    else:
        park_name = ""

    max_results = st.slider(
        "Maximum Results",
        min_value=5,
        max_value=25,
        value=10,
        step=5,
        key=f"{task_key}_max_results",
    )

    explore_button = st.button(
        "Explore Parks",
        type="primary",
        use_container_width=True,
        key=f"{task_key}_explore",
    )

    results_key = f"{task_key}_results"
    searched_key = f"{task_key}_searched"

    if explore_button:
        try:
            api_key = st.secrets["NPS_API_KEY"]

            state_codes = [STATE_CODES[state] for state in selected_states]
            params = {"limit": 50}

            if state_codes:
                params["stateCode"] = ",".join(state_codes)
            if park_name.strip():
                params["q"] = park_name.strip()

            parks = fetch_parks(
                api_key,
                tuple(sorted(params.items())),
            )
            parks = filter_and_rank_parks_by_name(parks, park_name)
            parks = filter_parks_by_activities(parks, selected_activities)
            parks = parks[:max_results]

            st.session_state[results_key] = parks
            st.session_state[searched_key] = True

        except KeyError:
            st.error(
                "The National Park Service API key is missing from "
                ".streamlit/secrets.toml."
            )
        except requests.RequestException:
            st.error(
                "The app could not connect to the National Park Service API. "
                "Please try again."
            )

    if st.session_state.get(searched_key, False):
        parks = st.session_state.get(results_key, [])
        if parks:
            st.success(f"Found {len(parks)} matching park site(s).")
            display_park_results(parks)
        else:
            st.warning(
                "No parks matched those selections. Try adjusting the state or "
                "activity filters."
            )
    else:
        st.info("Choose your filters, then select Explore Parks.")


def task_1_page():
    st.title("Activity 1")
    with st.container(border=True):
        st.subheader("Your Goal")
        st.write(
            "Use the Find Your Wild application to locate Yellowstone "
            "National Park."
        )
        st.write(
            "Review the matching result and explore the available park "
            "information before continuing."
        )

    find_your_wild_app(task_key="task1", show_park_name=True)
    show_navigation(next_label="Continue to Reflection")


def task_1_reflection_page():
    reflection_page(
        task_number=1,
        ease_question="How easy was it to locate Yellowstone National Park?",
        next_label="Continue to Activity 2",
    )


def task_2_page():
    st.title("Activity 2")
    with st.container(border=True):
        st.subheader("Your Goal")
        st.write(
            "Use the State and Activities filters to find National Parks in "
            "Florida that offer boating opportunities."
        )
        st.write(
            "Review the matching parks and explore the available information. "
            "Continue when you believe you have completed the activity."
        )

    find_your_wild_app(task_key="task2", show_park_name=False)
    show_navigation(next_label="Continue to Reflection")


def task_2_reflection_page():
    reflection_page(
        task_number=2,
        ease_question=(
            "How easy was it to use the filters to find a Florida park "
            "with boating opportunities?"
        ),
        next_label="Continue to Activity 3",
    )


def task_3_page():
    st.title("Activity 3")
    with st.container(border=True):
        st.subheader("Your Goal")
        st.write(
            "Use the State and Activities filters to find National Parks in "
            "California that offer camping opportunities."
        )
        st.write(
            "Review the matching parks and choose one you would most like to "
            "visit. Continue when you believe you have completed the activity."
        )

    find_your_wild_app(task_key="task3", show_park_name=False)
    show_navigation(next_label="Continue to Reflection")


def task_3_reflection_page():
    reflection_page(
        task_number=3,
        ease_question=(
            "How easy was it to use the filters to find California parks "
            "with camping opportunities?"
        ),
        next_label="Continue to Exit Survey",
    )


def reflection_page(task_number: int, ease_question: str, next_label: str):
    prefix = f"task{task_number}"

    st.title(f"Activity {task_number} Reflection")
    st.write(
        f"Please answer a few questions about your experience completing "
        f"Activity {task_number}."
    )
    st.divider()

    ease_rating = st.slider(
        ease_question,
        min_value=1,
        max_value=5,
        value=st.session_state.participant[f"{prefix}_ease"],
        help="1 = Very Difficult, 5 = Very Easy",
        key=f"{prefix}_ease_widget",
    )

    completion_options = ["Yes", "Partially", "No"]
    completion = st.radio(
        "Were you able to complete the task?",
        completion_options,
        index=(
            completion_options.index(
                st.session_state.participant[f"{prefix}_completion"]
            )
            if st.session_state.participant[f"{prefix}_completion"]
            in completion_options
            else None
        ),
        key=f"{prefix}_completion_widget",
    )

    confusion = st.text_area(
        "What, if anything, was confusing?",
        value=st.session_state.participant[f"{prefix}_confusion"],
        key=f"{prefix}_confusion_widget",
    )

    comments = st.text_area(
        "Additional comments (optional)",
        value=st.session_state.participant[f"{prefix}_comments"],
        key=f"{prefix}_comments_widget",
    )

    st.session_state.participant[f"{prefix}_ease"] = ease_rating
    st.session_state.participant[f"{prefix}_completion"] = completion or ""
    st.session_state.participant[f"{prefix}_confusion"] = confusion
    st.session_state.participant[f"{prefix}_comments"] = comments

    form_complete = completion in completion_options
    if not form_complete:
        st.caption("Please indicate whether you were able to complete the task.")

    st.write("")
    left, spacer, right = st.columns([1, 2.5, 1])
    with left:
        st.button(
            "Back",
            on_click=go_back,
            use_container_width=True,
            key=f"{prefix}_reflection_back",
        )
    with right:
        st.button(
            next_label,
            on_click=go_next,
            use_container_width=True,
            type="primary",
            disabled=not form_complete,
            key=f"{prefix}_reflection_next",
        )


def exit_survey_page():
    st.title("Final Experience Survey")
    st.write(
        "Please share your overall impressions of the Find Your Wild application."
    )
    st.divider()

    overall_satisfaction = st.slider(
        "How satisfied were you with the overall experience?",
        min_value=1,
        max_value=5,
        value=st.session_state.participant["overall_satisfaction"],
        help="1 = Very Dissatisfied, 5 = Very Satisfied",
    )

    most_useful_feature = st.text_area(
        "Which feature did you find most useful?",
        value=st.session_state.participant["most_useful_feature"],
    )

    least_useful_feature = st.text_area(
        "Which feature did you find least useful or most frustrating?",
        value=st.session_state.participant["least_useful_feature"],
    )

    use_again_options = ["Yes", "Maybe", "No"]
    would_use_again = st.radio(
        "Would you use Find Your Wild again?",
        use_again_options,
        index=(
            use_again_options.index(
                st.session_state.participant["would_use_again"]
            )
            if st.session_state.participant["would_use_again"]
            in use_again_options
            else None
        ),
    )

    improvement_suggestion = st.text_area(
        "What is one improvement you would suggest?",
        value=st.session_state.participant["improvement_suggestion"],
    )

    st.session_state.participant["overall_satisfaction"] = overall_satisfaction
    st.session_state.participant["most_useful_feature"] = most_useful_feature
    st.session_state.participant["least_useful_feature"] = least_useful_feature
    st.session_state.participant["would_use_again"] = would_use_again or ""
    st.session_state.participant["improvement_suggestion"] = improvement_suggestion

    form_complete = all(
        [
            most_useful_feature.strip(),
            least_useful_feature.strip(),
            would_use_again in use_again_options,
            improvement_suggestion.strip(),
        ]
    )

    if not form_complete:
        st.caption("Please answer every question before submitting the study.")

    st.write("")
    left, spacer, right = st.columns([1, 2.5, 1])
    with left:
        st.button("Back", on_click=go_back, use_container_width=True)
    with right:
        st.button(
            "Submit Study",
            on_click=submit_study,
            use_container_width=True,
            type="primary",
            disabled=not form_complete,
        )


def thank_you_page():
    st.title("Study Complete")
    with st.container(border=True):
        st.subheader("Thank you for your feedback")
        st.write(
            "Your usability study is complete. Your responses will help "
            "identify ways to improve the Find Your Wild experience."
        )
        st.success(
            "Your responses have been submitted successfully.\n\n"
            "You may now close this browser window."
        )


# ---------------------------------------------------------
# DISPLAY CURRENT PAGE
# ---------------------------------------------------------

current_page = STUDY_STEPS[st.session_state.current_step]
show_progress()

if current_page == "Welcome":
    welcome_page()
elif current_page == "Consent":
    consent_page()
elif current_page == "Demographics":
    demographics_page()
elif current_page == "Introduction":
    introduction_page()
elif current_page == "Task 1":
    task_1_page()
elif current_page == "Task 1 Reflection":
    task_1_reflection_page()
elif current_page == "Task 2":
    task_2_page()
elif current_page == "Task 2 Reflection":
    task_2_reflection_page()
elif current_page == "Task 3":
    task_3_page()
elif current_page == "Task 3 Reflection":
    task_3_reflection_page()
elif current_page == "Exit Survey":
    exit_survey_page()
elif current_page == "Thank You":
    thank_you_page()