import streamlit as st

# Get access token from Streamlit secrets
ACCESS_TOKEN = "EAANTaHFrvbgBPdKhprtPRmB5Or1KfZCgBZCPUzOZASNj31ZA79ZCmYy917oYHCpZCDZBV3ovebGwnZCB83ZADrOYGwv9CVcxi7SVgC2mo4XqZADwMBcbbYWROLskEfq5K3cQEcJ0UYt5FZBYmzfxQW3vUyvLhUbeppYNZB1ZAWV9FrVsAucDJBPCYGMuZBoThKJfZC2jZBcs"
WELLNESS_PALACE_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJsb2NhdGlvbl9pZCI6IjFvUjlxWGRBSXZ5R3lEMUxBcDhPIiwidmVyc2lvbiI6MSwiaWF0IjoxNzUyNDA3MzAyNjg4LCJzdWIiOiJNZ3p6NVFreHdqdE9CNDNLVmI3NyJ9.w-8PLgiGd_MLz6swGEkrEwjsRYzuKkxmqf5ZzoNZ1n8"

FARES_ESTHETIC_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJsb2NhdGlvbl9pZCI6IkpnMktmM29KTDVpWUtrdWJtVWFzIiwidmVyc2lvbiI6MSwiaWF0IjoxNzUyNDA5NDk4NjY3LCJzdWIiOiJNZ3p6NVFreHdqdE9CNDNLVmI3NyJ9.f0ODGDmFfDVrpXvQKeBb8yzxAMMslhr_A5hvNQh3ckA"

KINE_CINQ_SENS_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJsb2NhdGlvbl9pZCI6IldxRXBsSDBEV3VTckxCakdPR09rIiwidmVyc2lvbiI6MSwiaWF0IjoxNzUyNDA5NjA3NjcxLCJzdWIiOiJNZ3p6NVFreHdqdE9CNDNLVmI3NyJ9.55yqlq37Q3QurKw19rY7JPNS2mXjKFdBl7AS8U8OGQo"

DADIJ_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJsb2NhdGlvbl9pZCI6ImNpT0tBTU1xTTdtbHgwQmNjVERmIiwiY29tcGFueV9pZCI6IjhXUHpsd3JIbVBhaThzWUczNEN4IiwidmVyc2lvbiI6MSwiaWF0IjoxNzAzMjQ4NDMwMjY1LCJzdWIiOiJ1c2VyX2lkIn0.gerwvj7XJK1r-oJndse-FVRZ9XHqSrqBmysN7pBUIns"

CENTRE_PLENITUDE_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJsb2NhdGlvbl9pZCI6Ilc3eUprUXRLSFljaVR0dGJkVUxyIiwidmVyc2lvbiI6MSwiaWF0IjoxNzUyNDEwNDI3MjQwLCJzdWIiOiJNZ3p6NVFreHdqdE9CNDNLVmI3NyJ9.GdsAyphpcQKJ1DbX_q0BQlihsqfh27S-LvjFEg0Jcx8"

CENTRE_KINAISANCE_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJsb2NhdGlvbl9pZCI6IkVkd2NKSW40Z1k4NjlSSTRJM05FIiwidmVyc2lvbiI6MSwiaWF0IjoxNzUyNDEwNjc5NTU0LCJzdWIiOiJNZ3p6NVFreHdqdE9CNDNLVmI3NyJ9.mwhDc6nl_-H7lTzZstpvbF4JthHG4YOdq0IJqzHeqxI"

LE_NEUF_MAROC_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJsb2NhdGlvbl9pZCI6ImE1RVpkT0daeXVRYjhvTmpvamxrIiwidmVyc2lvbiI6MSwiaWF0IjoxNzUyNDEwODQxNzM2LCJzdWIiOiJNZ3p6NVFreHdqdE9CNDNLVmI3NyJ9.0RNyhHfrOn0YUQtyhhtXXBTzS_10BOvs35SVXefOIKw"

MAISON_ECLAT_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJsb2NhdGlvbl9pZCI6IkxqRzRXWnd3bTVkUUN4aUE2VnBmIiwidmVyc2lvbiI6MSwiaWF0IjoxNzUyNDExMDE5Mjg3LCJzdWIiOiJNZ3p6NVFreHdqdE9CNDNLVmI3NyJ9.4KTY65bLVE2GEB62_0aaqjUy5v9t4UwFgSj9jK4KJeY"

CENTRE_BE_SALAM_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJsb2NhdGlvbl9pZCI6IlVMM1cyYWI1ZmFrbVhIZUo5YUZkIiwidmVyc2lvbiI6MSwiaWF0IjoxNzUyNDExMDkwNDgwLCJzdWIiOiJNZ3p6NVFreHdqdE9CNDNLVmI3NyJ9.8UquqveQsjEl_6x9fU1Hzs2TnrJ7ED89SrC6nfibNo4"

KRASOTKA_BEAUTY_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJsb2NhdGlvbl9pZCI6ImJXR1dzNGVQZDFNYThUVDFIMzNxIiwidmVyc2lvbiI6MSwiaWF0IjoxNzUyNDExMTY4MzQyLCJzdWIiOiJNZ3p6NVFreHdqdE9CNDNLVmI3NyJ9.crZZZWnuB96PJRte2gTHgeXMiXzXX-nVqlNPaMNr0H0"

MAYAE_BEAUTY_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJsb2NhdGlvbl9pZCI6Ik1laG9JSEhiQTd0UEFyeDhKOUpNIiwidmVyc2lvbiI6MSwiaWF0IjoxNzUyNDExMjEyOTU2LCJzdWIiOiJNZ3p6NVFreHdqdE9CNDNLVmI3NyJ9.713nUpr4rd0j6KhQJaEECaBiPVidDV-k1ieSlKI-C_c"

SVEALTHY_API_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJsb2NhdGlvbl9pZCI6Imloam5DYVBpWG50SjFPWndZMEI0IiwidmVyc2lvbiI6MSwiaWF0IjoxNzUzMTE2NjE3MDUyLCJzdWIiOiJNZ3p6NVFreHdqdE9CNDNLVmI3NyJ9.yMHqWMStaI-vYMXHYQUrx1yFSIWjutVxiHjVsdYczY4"

HERMOSA_API_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJsb2NhdGlvbl9pZCI6IkNVMG95bHp4czBvd1NSWTU1MjdmIiwidmVyc2lvbiI6MSwiaWF0IjoxNzUzMzY5MDcxNzkwLCJzdWIiOiJNZ3p6NVFreHdqdE9CNDNLVmI3NyJ9.lg4459hPZV305r5j3d-fA-WoUYzOAZ6YdaUHBS2wTf8"

BLOOM_API_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJsb2NhdGlvbl9pZCI6IlJ6MmlUSjdpNllES0RnUkU1dnhrIiwidmVyc2lvbiI6MSwiaWF0IjoxNzE2MTEwOTcyMDg4LCJzdWIiOiJ1dnpBdFQ1T2p4NHdpQXZMNVpiNCJ9.Nt1hM47it3JIwLzMRNUpzO4tP34yOhRGzj6mN0n-E9Q"
# Centers configuration - API keys from Streamlit secrets
CENTERS = [
    {
        "apiKey":  WELLNESS_PALACE_API_KEY ,
        "locationId": "1oR9qXdAIvyGyD1LAp8O",
        "city": "Casablanca",
        "centerName": "Wellness Palace",
        "pipelineName": "Nouveau Pipeline",
        "calendarId": "ApPxaeBYILG6C4bkSpc0",
        "businessId": "act_25684814804439146"
    },
    {
        "apiKey":  FARES_ESTHETIC_API_KEY ,
        "locationId": "Jg2Kf3oJL5iYKkubmUas",
        "city": "Marrakesh",
        "centerName": "Fares Esthetic Center",
        "pipelineName": "Nouveau Pipeline",
        "calendarId": "GwNJooiGfAn9GjMqphyG",
        "businessId": "act_1656373184910599"
    },
    {
        "apiKey":  KINE_CINQ_SENS_API_KEY ,
        "locationId": "WqEplH0DWuSrLBjGOGOk",
        "city": "Rabat",
        "centerName": "Kiné Cinq Sens",
        "pipelineName": "Nouveau Pipeline",
        "calendarId": "w1fw3eqQzkCtt2JN5JJb",
        "businessId": "act_326370360527674"
    },
    {
        "apiKey":  DADIJ_API_KEY ,
        "locationId": "ciOKAMMqM7mlx0BccTDf",
        "city": "Rabat",
        "centerName": "Dadij",
        "pipelineName": "DADIJ LEADS PIPELINE",
        "calendarId": "h97fBm4J0I85pYKzLT6e",
        "businessId": "act_3499790706966281"
    },
    {
        "apiKey":  CENTRE_PLENITUDE_API_KEY ,
        "locationId": "W7yJkQtKHYciTttbdULr",
        "city": "Marrakesh",
        "centerName": "Centre Plénitude",
        "pipelineName": "Plénitude Pipeline",
        "calendarId": "PSKUglRKRcozvRj9TTjF",
        "businessId": "act_776928644645438"
    },
    {
        "apiKey":  CENTRE_KINAISANCE_API_KEY ,
        "locationId": "EdwcJIn4gY869RI4I3NE",
        "city": "Casablanca",
        "centerName": "Centre Kinaisance",
        "pipelineName": "Nouveau Pipeline",
        "calendarId": "4E0AYMcG27owc6ylnRTf",
        "calendarId2": "DHDDTAdMxijNedp0Q8Sk",
        "businessId": "act_701050159071271"
    },
    {
        "apiKey":  LE_NEUF_MAROC_API_KEY ,
        "locationId": "a5EZdOGZyuQb8oNjojlk",
        "city": "Casablanca",
        "centerName": "Le Neuf Maroc",
        "pipelineName": "Nouveau Pipeline",
        "calendarId": "dnMc4WakoOzAwYQtT4um",
        "businessId": "act_2508632876144425"
    },
    {
        "apiKey":  CENTRE_BE_SALAM_API_KEY ,
        "locationId": "UL3W2ab5fakmXHeJ9aFd",
        "city": "Casablanca",
        "centerName": "Centre Be Salam",
        "pipelineName": "Nouveau Pipeline",
        "calendarId": "5M1g3Rpl0aAQHbPGf2B5",
        "businessId": "act_3974524579468467"
    },
    {
        "apiKey":  KRASOTKA_BEAUTY_API_KEY ,
        "locationId": "bWGWs4ePd1Ma8TT1H33q",
        "city": "Casablanca",
        "centerName": "Krasotka Beauty Center",
        "pipelineName": "Nouveau Pipeline",
        "calendarId": "C82RZoQRjVrjOdBnRvBW",
        "businessId": "act_2166625163851201"
    },
    {
        "apiKey":  SVEALTHY_API_KEY ,
        "locationId": "ihjnCaPiXntJ1OZwY0B4",
        "city": "Casablanca",
        "centerName": "Svealthy",
        "pipelineName": "Nouveau Pipeline",
        "calendarId": "Fw0K4ezXHzSeOYACb7iq",
        "businessId": "act_513437851427640"
    },
    {
        "apiKey": BLOOM_API_KEY,
        "locationId": "Rz2iTJ7i6YDKDgRE5vxk",
        "city": "Casablanca",
        "centerName": "Bloom Clinic",
        "pipelineName": "Lp Calendar Pipeline",
        "calendarId": "iW0Nuq4XNVu7AOCsDKLF",
        "businessId": "act_1180242759663330"
    }

]

# Benchmark definitions with classic colors
BENCHMARKS = {
    'confirmation': {'excellent': 60, 'good': 40, 'colors': ['#28a745', '#ffc107', '#dc3545']},  # Green, Yellow, Red
    'show_up': {'excellent': 50, 'good': 35, 'colors': ['#28a745', '#ffc107', '#dc3545']},
    'conversion': {'excellent': 50, 'good': 30, 'colors': ['#28a745', '#ffc107', '#dc3545']},
    'cancellation': {'excellent': 30, 'good': 40, 'colors': ['#28a745', '#ffc107', '#dc3545'], 'reverse': True},
    'no_answer': {'excellent': 30, 'good': 40, 'colors': ['#28a745', '#ffc107', '#dc3545'], 'reverse': True}
}

# Color constants
COLORS = {
    'GREEN': '#28a745',
    'YELLOW': '#ffc107', 
    'RED': '#dc3545',
    'NEUTRAL': '#6c757d',
    'PRIMARY': '#007bff',
    'SECONDARY': '#6c757d'
}

# CSS Styling
CUSTOM_CSS = """
<style>
    .main {
        background-color: #f8f9fa;
    }
    .stApp {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    .metric-green { border-left-color: #28a745; }
    .metric-yellow { border-left-color: #ffc107; }
    .metric-red { border-left-color: #dc3545; }
    .metric-neutral { border-left-color: #6c757d; }

    .benchmark-legend {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        border: 1px solid #dee2e6;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }

    .benchmark-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 15px;
        margin-top: 15px;
    }

    .benchmark-item {
        background: #f8f9fa;
        padding: 12px;
        border-radius: 8px;
        border-left: 3px solid #007bff;
    }

    /* Table styling for colored cells */
    .colored-table {
        border-collapse: collapse;
        width: 100%;
    }

    .colored-table th, .colored-table td {
        padding: 8px 12px;
        text-align: left;
        border: 1px solid #dee2e6;
    }

    .colored-table th {
        background-color: #f8f9fa;
        font-weight: bold;
    }

    .cell-green {
        background-color: #d4edda !important;
        color: #155724 !important;
        font-weight: bold;
    }

    .cell-yellow {
        background-color: #fff3cd !important;
        color: #856404 !important;
        font-weight: bold;
    }

    .cell-red {
        background-color: #f8d7da !important;
        color: #721c24 !important;
        font-weight: bold;
    }

    .cell-neutral {
        background-color: #f8f9fa !important;
        color: #495057 !important;
    }
</style>
"""
# ...existing config...
AUTH_USER = "admin"
AUTH_PASS = "admin"
# ...existing config...