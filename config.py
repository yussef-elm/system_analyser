import streamlit as st

# Get access token from Streamlit secrets
ACCESS_TOKEN = st.secrets["META_ACCESS_TOKEN"]

# Centers configuration - API keys from Streamlit secrets
CENTERS = [
       {
        "apiKey": st.secrets["BLOOM_API_KEY"],
        "locationId": "Rz2iTJ7i6YDKDgRE5vxk",
        "city": "Casablanca",
        "centerName": "Bloom Clinic",
        "pipelineName": "Lp Calendar Pipeline",
        "calendarId": "iW0Nuq4XNVu7AOCsDKLF",
        "businessId": "act_1180242759663330"
    },
    {
        "apiKey": st.secrets["WELLNESS_PALACE_API_KEY"],
        "locationId": "1oR9qXdAIvyGyD1LAp8O",
        "city": "Casablanca",
        "centerName": "Wellness Palace",
        "pipelineName": "Nouveau Pipeline",
        "calendarId": "ApPxaeBYILG6C4bkSpc0",
        "businessId": "act_25684814804439146"
    },
    {
        "apiKey": st.secrets["FARES_ESTHETIC_API_KEY"],
        "locationId": "Jg2Kf3oJL5iYKkubmUas",
        "city": "Marrakesh",
        "centerName": "Fares Esthetic Center",
        "pipelineName": "Nouveau Pipeline",
        "calendarId": "GwNJooiGfAn9GjMqphyG",
        "businessId": "act_1656373184910599"
    },
    {
        "apiKey": st.secrets["KINE_CINQ_SENS_API_KEY"],
        "locationId": "WqEplH0DWuSrLBjGOGOk",
        "city": "Rabat",
        "centerName": "Kiné Cinq Sens",
        "pipelineName": "Nouveau Pipeline",
        "calendarId": "w1fw3eqQzkCtt2JN5JJb",
        "businessId": "act_326370360527674"
    },
    {
        "apiKey": st.secrets["DADIJ_API_KEY"],
        "locationId": "ciOKAMMqM7mlx0BccTDf",
        "city": "Rabat",
        "centerName": "Dadij",
        "pipelineName": "DADIJ LEADS PIPELINE",
        "calendarId": "h97fBm4J0I85pYKzLT6e",
        "businessId": "act_3499790706966281"
    },
    {
        "apiKey": st.secrets["CENTRE_PLENITUDE_API_KEY"],
        "locationId": "W7yJkQtKHYciTttbdULr",
        "city": "Marrakesh",
        "centerName": "Centre Plénitude",
        "pipelineName": "Plénitude Pipeline",
        "calendarId": "PSKUglRKRcozvRj9TTjF",
        "businessId": "act_776928644645438"
    },
    {
        "apiKey": st.secrets["CENTRE_KINAISANCE_API_KEY"],
        "locationId": "EdwcJIn4gY869RI4I3NE",
        "city": "Casablanca",
        "centerName": "Centre Kinaisance",
        "pipelineName": "Nouveau Pipeline",
        "calendarId": "4E0AYMcG27owc6ylnRTf",
        "calendarId2": "DHDDTAdMxijNedp0Q8Sk",
        "businessId": "act_701050159071271"
    },
    {
        "apiKey": st.secrets["LE_NEUF_MAROC_API_KEY"],
        "locationId": "a5EZdOGZyuQb8oNjojlk",
        "city": "Casablanca",
        "centerName": "Le Neuf Maroc",
        "pipelineName": "Nouveau Pipeline",
        "calendarId": "dnMc4WakoOzAwYQtT4um",
        "businessId": "act_2508632876144425"
    },
    {
        "apiKey": st.secrets["CENTRE_BE_SALAM_API_KEY"],
        "locationId": "UL3W2ab5fakmXHeJ9aFd",
        "city": "Casablanca",
        "centerName": "Centre Be Salam",
        "pipelineName": "Nouveau Pipeline",
        "calendarId": "5M1g3Rpl0aAQHbPGf2B5",
        "businessId": "act_3974524579468467"
    },
    {
        "apiKey": st.secrets["KRASOTKA_BEAUTY_API_KEY"],
        "locationId": "bWGWs4ePd1Ma8TT1H33q",
        "city": "Casablanca",
        "centerName": "Krasotka Beauty Center",
        "pipelineName": "Nouveau Pipeline",
        "calendarId": "C82RZoQRjVrjOdBnRvBW",
        "businessId": "act_2166625163851201"
    },
    {
        "apiKey": st.secrets["MAYAE_BEAUTY_API_KEY"],
        "locationId": "MehoIHHbA7tPArx8J9JM",
        "city": "Marrakesh",
        "centerName": "Mayae Beauty Center",
        "pipelineName": "Nouveau Pipeline",
        "calendarId": "HZSSHX1WeZ2juD1vQk0b",
        "businessId": "act_1803648590586295"
    },
    {
        "apiKey": st.secrets["SVEALTHY_API_KEY"],
        "locationId": "ihjnCaPiXntJ1OZwY0B4",
        "city": "Casablanca",
        "centerName": "Svealthy",
        "pipelineName": "Nouveau Pipeline",
        "calendarId": "Fw0K4ezXHzSeOYACb7iq",
        "businessId": "act_513437851427640"
    },
    {
        "apiKey": st.secrets["ELIXIR_API_KEY"],
        "locationId": "aQtkSVL55sGJ5X87tWEv",
        "city": "Agadir",
        "centerName": "Elixir",
        "pipelineName": "ELIXIR PIPELINE",
        "calendarId": "sk4EYCbwf0WxP7xF9DsT",
        "businessId": "act_1026380249209164"
    }
]
