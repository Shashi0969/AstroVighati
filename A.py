"""
AstroVighati Pro Elite: Advanced Vedic Astrology Suite
Version: 4.4 with Seconds Input and Comprehensive Varga Engine

Description:
This script creates a comprehensive desktop application for Vedic astrology using Python's Tkinter library.
This version has been updated to accept seconds in the birth time for higher precision.
It also features a completely overhauled, professionally accurate Varga calculation engine
that implements standard Parashari methods for all major divisional charts from D1 to D60.
"""

import importlib
import subprocess
import sys

# A list of required third-party Python packages for the application to run fully.
required_packages = [
    "Pillow",
    "requests",
    "pyswisseph", # The correct package name for swisseph on PyPI
    "geopy",
    "timezonefinder",
    "skyfield",
    "matplotlib",
    "numpy",
    "pandas",
    "reportlab"
]

dependencies_missing = False  # A global flag to track if any installations occurred.

def install_if_missing(package):
    """
    Checks if a given package is installed in the current Python environment.
    If the package is not found, it attempts to install it using pip.
    This ensures that the application has all its necessary dependencies before running.
    """
    global dependencies_missing
    try:
        # We use a special check for pyswisseph as the import name is 'swisseph'
        import_name = 'swisseph' if package == 'pyswisseph' else package
        # Attempt to import the package dynamically.
        importlib.import_module(import_name)
        print(f"✅ {package} is already installed.")
    except ImportError:
        # If the import fails, the package is missing.
        dependencies_missing = True
        print(f"⚙️ Installing missing dependency: {package}")
        # Use subprocess to call pip and install the package.
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ Successfully installed {package}")

# --- Dependency Check Block ---
print("🚀 Initializing AstroVighati Pro Elite: Checking dependencies...")
for pkg in required_packages:
    install_if_missing(pkg)

if dependencies_missing:
    print("\n🔄 Some packages were installed. If you encounter issues, please restart the application.\n")
else:
    print("\n✨ All dependencies are satisfied! Launching application...\n")


import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from datetime import datetime, timedelta
import threading
import math
import json
import os
from pathlib import Path

# --- Graceful Library Importing ---
try:
    from PIL import Image, ImageTk, ImageDraw, ImageFont, ImageFilter
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("⚠️ Pillow (PIL) not found. Advanced image features will be disabled.")

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("⚠️ Requests not found. Online features will be disabled.")

try:
    import swisseph as swe
    SWISSEPH_AVAILABLE = True
except ImportError:
    SWISSEPH_AVAILABLE = False
    print("⚠️ Swiss Ephemeris (pyswisseph) not found. Calculations will be approximate.")

try:
    import matplotlib
    matplotlib.use('TkAgg')
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("⚠️ Matplotlib not found. Chart visualization will be disabled.")

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    print("⚠️ NumPy not found. Advanced numerical calculations will be disabled.")

#===================================================================================================
# HELPER FUNCTIONS
#===================================================================================================

def decimal_to_dms(decimal_degrees):
    """Converts a decimal degree value into a formatted DMS string."""
    if decimal_degrees >= 30.0: decimal_degrees = 29.99999
    degrees = int(decimal_degrees)
    minutes_float = (decimal_degrees - degrees) * 60
    minutes = int(minutes_float)
    seconds = round((minutes_float - minutes) * 60, 2)
    if seconds >= 60: seconds -= 60; minutes += 1
    if minutes >= 60: minutes -= 60; degrees += 1
    return f"{degrees:02d}° {minutes:02d}' {seconds:05.2f}\""

#===================================================================================================
# ENHANCED DATA STORE
#===================================================================================================
class EnhancedAstrologicalData:
    PLANET_COLORS = {
        "Sun": "#FDB813", "Moon": "#C0C0C0", "Mars": "#CD5C5C",
        "Mercury": "#90EE90", "Jupiter": "#FFD700", "Venus": "#FFB6C1",
        "Saturn": "#4169E1", "Rahu": "#8B4513", "Ketu": "#A9A9A9",
        "Ascendant": "#E74C3C"
    }
    RASHI_COLORS = {
        "Aries": "#FF6B6B", "Taurus": "#4ECDC4", "Gemini": "#FFE66D",
        "Cancer": "#95E1D3", "Leo": "#F38181", "Virgo": "#AA96DA",
        "Libra": "#FCBAD3", "Scorpio": "#A8E6CF", "Sagittarius": "#FF8B94",
        "Capricorn": "#C7CEEA", "Aquarius": "#B4F8C8", "Pisces": "#FBE7C6"
    }
    SIGNS = {
        1: "Aries", 2: "Taurus", 3: "Gemini", 4: "Cancer", 5: "Leo", 6: "Virgo",
        7: "Libra", 8: "Scorpio", 9: "Sagittarius", 10: "Capricorn", 11: "Aquarius", 12: "Pisces"
    }
    SIGN_NAME_TO_NUM = {v: k for k, v in SIGNS.items()}
    SIGN_NATURE = {
        1: "Odd", 2: "Even", 3: "Odd", 4: "Even", 5: "Odd", 6: "Even",
        7: "Odd", 8: "Even", 9: "Odd", 10: "Even", 11: "Odd", 12: "Even"
    }

    @staticmethod
    def get_varga_descriptions():
        # This data structure is now the single source of truth for Varga charts
        return {
            "D1 - Rashi": {"num": 1, "title": "D1 - Rashi Kundali (Lagna Chart)", "description": "The foundational birth chart..."},
            "D2 - Hora": {"num": 2, "title": "D2 - Hora Chart (Wealth)", "description": "The Hora chart divides each sign into two halves..."},
            "D3 - Drekkana": {"num": 3, "title": "D3 - Drekkana Chart (Siblings & Courage)", "description": "The Drekkana divides each sign into three parts..."},
            "D4 - Chaturthamsa": {"num": 4, "title": "D4 - Chaturthamsa Chart (Property & Fortune)", "description": "This chart divides each sign into four parts..."},
            "D5 - Panchamsa": {"num": 5, "title": "D5 - Panchamsa Chart (Fame, Power & Authority)", "description": "The Panchamsa chart divides each sign into five parts..."},
            "D6 - Shashthamsa": {"num": 6, "title": "D6 - Shashthamsa Chart (Health & Diseases)", "description": "This chart divides each sign into six parts..."},
            "D7 - Saptamsa": {"num": 7, "title": "D7 - Saptamsa Chart (Children & Progeny)", "description": "The Saptamsa chart divides each sign into seven parts..."},
            "D9 - Navamsa": {"num": 9, "title": "D9 - Navamsa Chart (Spouse, Dharma & Fortune)", "description": "The Navamsa is arguably the most important divisional chart..."},
            "D10 - Dasamsa": {"num": 10, "title": "D10 - Dasamsa Chart (Career & Profession)", "description": "The Dasamsa divides each sign into ten parts..."},
            "D12 - Dwadasamsa": {"num": 12, "title": "D12 - Dwadasamsa Chart (Parents & Lineage)", "description": "The Dwadasamsa divides each sign into twelve parts..."},
            "D16 - Shodasamsa": {"num": 16, "title": "D16 - Shodasamsa Chart (Vehicles, Comforts & Discomforts)", "description": "This chart divides each sign into sixteen parts..."},
            "D20 - Vimsamsa": {"num": 20, "title": "D20 - Vimsamsa Chart (Spiritual Pursuits)", "description": "The Vimsamsa divides each sign into twenty parts..."},
            "D24 - Siddhamsa": {"num": 24, "title": "D24 - Siddhamsa Chart (Education & Knowledge)", "description": "The Siddhamsa divides each sign into twenty-four parts..."},
            "D30 - Trimsamsa": {"num": 30, "title": "D30 - Trimsamsa Chart (Misfortunes & Character)", "description": "The Trimsamsa has a unique division system..."},
            "D40 - Khavedamsa": {"num": 40, "title": "D40 - Khavedamsa Chart (Auspicious & Inauspicious Effects)", "description": "The Khavedamsa divides each sign into forty parts..."},
            "D45 - Akshavedamsa": {"num": 45, "title": "D45 - Akshavedamsa Chart (General Character & Paternal Lineage)", "description": "The Akshavedamsa divides each sign into forty-five parts..."},
            "D60 - Shashtyamsa": {"num": 60, "title": "D60 - Shashtyamsa Chart (Past Karma & All Matters)", "description": "The Shashtyamsa is a highly sensitive and important chart..."}
        }
    
    # ... Other static methods like get_all_nakshatras(), get_all_planets(), etc. remain unchanged ...
    @staticmethod
    def get_all_nakshatras(): return [{"name": "1. Ashwini", "sanskrit": "Ashwini", "devanagari": "अश्विनी", "lord": "Ketu", "remainder": "1", "deity": "Ashwini Kumaras", "gana": "Deva", "guna": "Sattva", "tattva": "Fire", "start_degree": 0.0, "end_degree": 13.3333, "padas": ["Aries", "Taurus", "Gemini", "Cancer"], "motivation": "Dharma", "nature": "Movable", "keywords": "Swift, Healing, Pioneering", "symbol": "Horse's Head", "animal": "Male Horse", "tree": "Poison Nut Tree"}, {"name": "2. Bharani", "sanskrit": "Bharani", "devanagari": "भरणी", "lord": "Venus", "remainder": "2", "deity": "Yama", "gana": "Manushya", "guna": "Rajas", "tattva": "Earth", "start_degree": 13.3333, "end_degree": 26.6666, "padas": ["Leo", "Virgo", "Libra", "Scorpio"], "motivation": "Artha", "nature": "Fierce", "keywords": "Bearer, Transformative, Creative", "symbol": "Yoni", "animal": "Elephant", "tree": "Amla Tree"}, {"name": "3. Krittika", "sanskrit": "Krittika", "devanagari": "कृत्तिका", "lord": "Sun", "remainder": "3", "deity": "Agni", "gana": "Rakshasa", "guna": "Rajas", "tattva": "Fire", "start_degree": 26.6666, "end_degree": 40.0, "padas": ["Sagittarius", "Capricorn", "Aquarius", "Pisces"], "motivation": "Kama", "nature": "Mixed", "keywords": "The Cutter, Purifying, Sharp", "symbol": "Razor/Axe", "animal": "Female Sheep", "tree": "Fig Tree"}, {"name": "4. Rohini", "sanskrit": "Rohini", "devanagari": "रोहिणी", "lord": "Moon", "remainder": "4", "deity": "Brahma", "gana": "Manushya", "guna": "Rajas", "tattva": "Earth", "start_degree": 40.0, "end_degree": 53.3333, "padas": ["Aries", "Taurus", "Gemini", "Cancer"], "motivation": "Moksha", "nature": "Fixed", "keywords": "The Beloved, Fertile, Growing", "symbol": "Chariot", "animal": "Male Serpent", "tree": "Jamun Tree"}, {"name": "5. Mrigashira", "sanskrit": "Mrigashira", "devanagari": "मृगशिरा", "lord": "Mars", "remainder": "5", "deity": "Soma", "gana": "Deva", "guna": "Tamas", "tattva": "Air", "start_degree": 53.3333, "end_degree": 66.6666, "padas": ["Leo", "Virgo", "Libra", "Scorpio"], "motivation": "Moksha", "nature": "Soft", "keywords": "The Searcher, Curious, Restless", "symbol": "Deer's Head", "animal": "Female Serpent", "tree": "Khadira Tree"}, {"name": "6. Ardra", "sanskrit": "Ardra", "devanagari": "आर्द्रा", "lord": "Rahu", "remainder": "6", "deity": "Rudra", "gana": "Manushya", "guna": "Tamas", "tattva": "Water", "start_degree": 66.6666, "end_degree": 80.0, "padas": ["Sagittarius", "Capricorn", "Aquarius", "Pisces"], "motivation": "Kama", "nature": "Sharp", "keywords": "The Moist One, Intense, Transformative", "symbol": "Teardrop/Diamond", "animal": "Female Dog", "tree": "Krishna Kamal"}, {"name": "7. Punarvasu", "sanskrit": "Punarvasu", "devanagari": "पुनर्वसु", "lord": "Jupiter", "remainder": "7", "deity": "Aditi", "gana": "Deva", "guna": "Sattva", "tattva": "Air", "start_degree": 80.0, "end_degree": 93.3333, "padas": ["Aries", "Taurus", "Gemini", "Cancer"], "motivation": "Artha", "nature": "Movable", "keywords": "The Returner, Hopeful, Nurturing", "symbol": "Quiver of Arrows", "animal": "Female Cat", "tree": "Bamboo"}, {"name": "8. Pushya", "sanskrit": "Pushya", "devanagari": "पुष्य", "lord": "Saturn", "remainder": "8", "deity": "Brihaspati", "gana": "Deva", "guna": "Sattva", "tattva": "Water", "start_degree": 93.3333, "end_degree": 106.6666, "padas": ["Leo", "Virgo", "Libra", "Scorpio"], "motivation": "Dharma", "nature": "Light", "keywords": "The Nourisher, Auspicious, Protective", "symbol": "Cow's Udder", "animal": "Male Goat", "tree": "Peepal Tree"}, {"name": "9. Ashlesha", "sanskrit": "Ashlesha", "devanagari": "आश्लेषा", "lord": "Mercury", "remainder": "0", "deity": "Nagas", "gana": "Rakshasa", "guna": "Sattva", "tattva": "Water", "start_degree": 106.6666, "end_degree": 120.0, "padas": ["Sagittarius", "Capricorn", "Aquarius", "Pisces"], "motivation": "Dharma", "nature": "Sharp", "keywords": "The Serpent, Mystical, Cunning", "symbol": "Coiled Serpent", "animal": "Male Cat", "tree": "Nag Kesar"}, {"name": "10. Magha", "sanskrit": "Magha", "devanagari": "मघा", "lord": "Ketu", "remainder": "1", "deity": "Pitrs", "gana": "Rakshasa", "guna": "Tamas", "tattva": "Fire", "start_degree": 120.0, "end_degree": 133.3333, "padas": ["Aries", "Taurus", "Gemini", "Cancer"], "motivation": "Artha", "nature": "Fixed", "keywords": "Royal, Ancestral, Authoritative", "symbol": "Throne", "animal": "Male Rat", "tree": "Banyan Tree"}, {"name": "11. Purva Phalguni", "sanskrit": "Purva Phalguni", "devanagari": "पूर्व फाल्गुनी", "lord": "Venus", "remainder": "2", "deity": "Bhaga", "gana": "Manushya", "guna": "Rajas", "tattva": "Water", "start_degree": 133.3333, "end_degree": 146.6666, "padas": ["Leo", "Virgo", "Libra", "Scorpio"], "motivation": "Kama", "nature": "Fierce", "keywords": "Pleasure-loving, Creative, Social", "symbol": "Front Legs of Bed", "animal": "Female Rat", "tree": "Palash Tree"}, {"name": "12. Uttara Phalguni", "sanskrit": "Uttara Phalguni", "devanagari": "उत्तर फाल्गुनी", "lord": "Sun", "remainder": "3", "deity": "Aryaman", "gana": "Manushya", "guna": "Rajas", "tattva": "Earth", "start_degree": 146.6666, "end_degree": 160.0, "padas": ["Sagittarius", "Capricorn", "Aquarius", "Pisces"], "motivation": "Moksha", "nature": "Fixed", "keywords": "Generous, Helpful, Committed", "symbol": "Back Legs of Bed", "animal": "Male Bull", "tree": "Peepal Tree"}, {"name": "13. Hasta", "sanskrit": "Hasta", "devanagari": "हस्त", "lord": "Moon", "remainder": "4", "deity": "Savitar", "gana": "Deva", "guna": "Rajas", "tattva": "Earth", "start_degree": 160.0, "end_degree": 173.3333, "padas": ["Aries", "Taurus", "Gemini", "Cancer"], "motivation": "Moksha", "nature": "Light", "keywords": "The Hand, Skillful, Clever", "symbol": "Hand/Palm", "animal": "Female Buffalo", "tree": "Jasmine"}, {"name": "14. Chitra", "sanskrit": "Chitra", "devanagari": "चित్రా", "lord": "Mars", "remainder": "5", "deity": "Tvashtar", "gana": "Rakshasa", "guna": "Tamas", "tattva": "Air", "start_degree": 173.3333, "end_degree": 186.6666, "padas": ["Leo", "Virgo", "Libra", "Scorpio"], "motivation": "Kama", "nature": "Soft", "keywords": "The Bright One, Artistic, Magical", "symbol": "Bright Jewel/Pearl", "animal": "Female Tiger", "tree": "Bael Tree"}, {"name": "15. Swati", "sanskrit": "Swati", "devanagari": "स्वाति", "lord": "Rahu", "remainder": "6", "deity": "Vayu", "gana": "Deva", "guna": "Tamas", "tattva": "Air", "start_degree": 186.6666, "end_degree": 200.0, "padas": ["Sagittarius", "Capricorn", "Aquarius", "Pisces"], "motivation": "Artha", "nature": "Movable", "keywords": "The Sword, Independent, Flexible", "symbol": "Young Sprout", "animal": "Male Buffalo", "tree": "Arjun Tree"}, {"name": "16. Vishakha", "sanskrit": "Vishakha", "devanagari": "विशाखा", "lord": "Jupiter", "remainder": "7", "deity": "Indra-Agni", "gana": "Rakshasa", "guna": "Tamas", "tattva": "Fire", "start_degree": 200.0, "end_degree": 213.3333, "padas": ["Aries", "Taurus", "Gemini", "Cancer"], "motivation": "Dharma", "nature": "Mixed", "keywords": "The Forked Branch, Determined", "symbol": "Archway", "animal": "Male Tiger", "tree": "Wood Apple"}, {"name": "17. Anuradha", "sanskrit": "Anuradha", "devanagari": "अनुराधा", "lord": "Saturn", "remainder": "8", "deity": "Mitra", "gana": "Deva", "guna": "Sattva", "tattva": "Fire", "start_degree": 213.3333, "end_degree": 226.6666, "padas": ["Leo", "Virgo", "Libra", "Scorpio"], "motivation": "Dharma", "nature": "Soft", "keywords": "The Follower, Devoted, Friendly", "symbol": "Lotus", "animal": "Female Deer", "tree": "Nagkesar"}, {"name": "18. Jyestha", "sanskrit": "Jyestha", "devanagari": "ज्येष्ठा", "lord": "Mercury", "remainder": "0", "deity": "Indra", "gana": "Rakshasa", "guna": "Sattva", "tattva": "Air", "start_degree": 226.6666, "end_degree": 240.0, "padas": ["Sagittarius", "Capricorn", "Aquarius", "Pisces"], "motivation": "Artha", "nature": "Sharp", "keywords": "The Eldest, Protective, Responsible", "symbol": "Earring/Umbrella", "animal": "Male Deer", "tree": "Shalmali"}, {"name": "19. Mula", "sanskrit": "Mula", "devanagari": "मूल", "lord": "Ketu", "remainder": "1", "deity": "Nirriti", "gana": "Rakshasa", "guna": "Tamas", "tattva": "Air", "start_degree": 240.0, "end_degree": 253.3333, "padas": ["Aries", "Taurus", "Gemini", "Cancer"], "motivation": "Kama", "nature": "Sharp", "keywords": "The Root, Investigative, Destructive", "symbol": "Bunch of Roots", "animal": "Male Dog", "tree": "Sarjaka"}, {"name": "20. Purva Ashadha", "sanskrit": "Purva Ashadha", "devanagari": "पूर्वाषाढ़ा", "lord": "Venus", "remainder": "2", "deity": "Apas", "gana": "Manushya", "guna": "Rajas", "tattva": "Fire", "start_degree": 253.3333, "end_degree": 266.6666, "padas": ["Leo", "Virgo", "Libra", "Scorpio"], "motivation": "Moksha", "nature": "Fierce", "keywords": "Victorious, Purifying, Invincible", "symbol": "Elephant's Tusk", "animal": "Male Monkey", "tree": "Ashoka"}, {"name": "21. Uttara Ashadha", "sanskrit": "Uttara Ashadha", "devanagari": "उत्तराषाढ़ा", "lord": "Sun", "remainder": "3", "deity": "Vishvadevas", "gana": "Manushya", "guna": "Rajas", "tattva": "Earth", "start_degree": 266.6666, "end_degree": 280.0, "padas": ["Sagittarius", "Capricorn", "Aquarius", "Pisces"], "motivation": "Moksha", "nature": "Fixed", "keywords": "Permanent Victory, Virtuous", "symbol": "Elephant's Tusk", "animal": "Female Mongoose", "tree": "Jackfruit"}, {"name": "22. Shravana", "sanskrit": "Shravana", "devanagari": "श्रवण", "lord": "Moon", "remainder": "4", "deity": "Vishnu", "gana": "Deva", "guna": "Sattva", "tattva": "Air", "start_degree": 280.0, "end_degree": 293.3333, "padas": ["Aries", "Taurus", "Gemini", "Cancer"], "motivation": "Artha", "nature": "Movable", "keywords": "The Listener, Learning, Preserving", "symbol": "Three Footprints", "animal": "Female Monkey", "tree": "Arka"}, {"name": "23. Dhanishta", "sanskrit": "Dhanishta", "devanagari": "धनिष्ठा", "lord": "Mars", "remainder": "5", "deity": "Ashta Vasus", "gana": "Rakshasa", "guna": "Tamas", "tattva": "Ether", "start_degree": 293.3333, "end_degree": 306.6666, "padas": ["Leo", "Virgo", "Libra", "Scorpio"], "motivation": "Dharma", "nature": "Movable", "keywords": "The Richest One, Musical, Rhythmic", "symbol": "Drum/Flute", "animal": "Female Lion", "tree": "Shami"}, {"name": "24. Shatabhisha", "sanskrit": "Shatabhisha", "devanagari": "शतभिषा", "lord": "Rahu", "remainder": "6", "deity": "Varuna", "gana": "Rakshasa", "guna": "Tamas", "tattva": "Ether", "start_degree": 306.6666, "end_degree": 320.0, "padas": ["Sagittarius", "Capricorn", "Aquarius", "Pisces"], "motivation": "Dharma", "nature": "Movable", "keywords": "The Hundred Healers, Mysterious", "symbol": "Empty Circle", "animal": "Female Horse", "tree": "Kadamba"}, {"name": "25. Purva Bhadrapada", "sanskrit": "Purva Bhadrapada", "devanagari": "पूर्व भाद्रपद", "lord": "Jupiter", "remainder": "7", "deity": "Aja Ekapada", "gana": "Manushya", "guna": "Sattva", "tattva": "Ether", "start_degree": 320.0, "end_degree": 333.3333, "padas": ["Aries", "Taurus", "Gemini", "Cancer"], "motivation": "Artha", "nature": "Fierce", "keywords": "Intense, Spiritual, Transformative", "symbol": "Sword/Two Front Legs of Bed", "animal": "Male Lion", "tree": "Neem"}, {"name": "26. Uttara Bhadrapada", "sanskrit": "Uttara Bhadrapada", "devanagari": "उत्तर भाद्रपद", "lord": "Saturn", "remainder": "8", "deity": "Ahir Budhnya", "gana": "Manushya", "guna": "Sattva", "tattva": "Ether", "start_degree": 333.3333, "end_degree": 346.6666, "padas": ["Leo", "Virgo", "Libra", "Scorpio"], "motivation": "Kama", "nature": "Fixed", "keywords": "Deep, Wise, Compassionate", "symbol": "Two Back Legs of Bed", "animal": "Female Cow", "tree": "Neem"}, {"name": "27. Revati", "sanskrit": "Revati", "devanagari": "रेवती", "lord": "Mercury", "remainder": "0", "deity": "Pushan", "gana": "Deva", "guna": "Sattva", "tattva": "Ether", "start_degree": 346.6666, "end_degree": 360.0, "padas": ["Sagittarius", "Capricorn", "Aquarius", "Pisces"], "motivation": "Moksha", "nature": "Soft", "keywords": "The Wealthy One, Nourishing, Protective", "symbol": "Drum/Fish", "animal": "Female Elephant", "tree": "Honey Tree"}]

    @staticmethod
    def get_all_planets(): return [{"name": "Sun", "sanskrit": "Surya", "devanagari": "सूर्य", "symbol": "☉", "karaka": "Atmakaraka (Soul), Father, King, Authority, Ego, Health, Vitality, Right Eye", "dignities": {"Exaltation": "Aries 10°", "Debilitation": "Libra 10°", "Moolatrikona": "Leo 0°-20°", "Own Sign": "Leo"}, "nature": "Malefic", "gender": "Male", "vimshottari_dasha": "6 Years", "aspects": "7th house (100%)", "element": "Fire", "caste": "Kshatriya", "color": "#FDB813", "day": "Sunday", "gemstone": "Ruby", "deity": "Agni/Shiva", "metal": "Gold/Copper", "direction": "East", "body_part": "Bones, Right Eye, Heart", "friendly": ["Moon", "Mars", "Jupiter"], "neutral": ["Mercury"], "enemy": ["Venus", "Saturn"], "significations": ["Government", "Authority", "Father", "Soul", "Power", "Leadership"]}, {"name": "Moon", "sanskrit": "Chandra", "devanagari": "चंद्र", "symbol": "☽", "karaka": "Manakaraka (Mind), Mother, Emotions, Queen, Popularity, Fluids, Left Eye", "dignities": {"Exaltation": "Taurus 3°", "Debilitation": "Scorpio 3°", "Moolatrikona": "Taurus 3°-30°", "Own Sign": "Cancer"}, "nature": "Benefic", "gender": "Female", "vimshottari_dasha": "10 Years", "aspects": "7th house (100%)", "element": "Water", "caste": "Vaishya", "color": "#C0C0C0", "day": "Monday", "gemstone": "Pearl", "deity": "Varuna/Parvati", "metal": "Silver", "direction": "North-West", "body_part": "Blood, Left Eye, Mind", "friendly": ["Sun", "Mercury"], "neutral": ["Mars", "Jupiter", "Venus", "Saturn"], "enemy": [], "significations": ["Mind", "Mother", "Emotions", "Public", "Water", "Comfort"]}, {"name": "Mars", "sanskrit": "Mangala", "devanagari": "मंगल", "symbol": "♂", "karaka": "Bhratrukaraka (Siblings), Energy, Courage, Conflict, Land, Logic", "dignities": {"Exaltation": "Capricorn 28°", "Debilitation": "Cancer 28°", "Moolatrikona": "Aries 0°-12°", "Own Sign": "Aries, Scorpio"}, "nature": "Malefic", "gender": "Male", "vimshottari_dasha": "7 Years", "aspects": "4th, 7th, 8th houses", "element": "Fire", "caste": "Kshatriya", "color": "#CD5C5C", "day": "Tuesday", "gemstone": "Red Coral", "deity": "Kartikeya", "metal": "Copper", "direction": "South", "body_part": "Blood, Muscles, Marrow", "friendly": ["Sun", "Moon", "Jupiter"], "neutral": ["Venus", "Saturn"], "enemy": ["Mercury"], "significations": ["Energy", "Courage", "Siblings", "Property", "Weapons", "Surgery"]}, {"name": "Mercury", "sanskrit": "Budha", "devanagari": "बुध", "symbol": "☿", "karaka": "Vidyakaraka (Education), Intellect, Communication, Commerce, Logic", "dignities": {"Exaltation": "Virgo 15°", "Debilitation": "Pisces 15°", "Moolatrikona": "Virgo 15°-20°", "Own Sign": "Gemini, Virgo"}, "nature": "Neutral", "gender": "Neutral", "vimshottari_dasha": "17 Years", "aspects": "7th house (100%)", "element": "Earth", "caste": "Shudra", "color": "#90EE90", "day": "Wednesday", "gemstone": "Emerald", "deity": "Vishnu", "metal": "Brass", "direction": "North", "body_part": "Skin, Nervous System, Speech", "friendly": ["Sun", "Venus"], "neutral": ["Mars", "Jupiter", "Saturn"], "enemy": ["Moon"], "significations": ["Intelligence", "Communication", "Business", "Education", "Writing"]}, {"name": "Jupiter", "sanskrit": "Guru", "devanagari": "गुरु", "symbol": "♃", "karaka": "Putrakaraka (Children), Dhanakaraka (Wealth), Wisdom, Teacher", "dignities": {"Exaltation": "Cancer 5°", "Debilitation": "Capricorn 5°", "Moolatrikona": "Sagittarius 0°-10°", "Own Sign": "Sagittarius, Pisces"}, "nature": "Most Benefic", "gender": "Male", "vimshottari_dasha": "16 Years", "aspects": "5th, 7th, 9th houses", "element": "Ether", "caste": "Brahmin", "color": "#FFD700", "day": "Thursday", "gemstone": "Yellow Sapphire", "deity": "Indra/Brahma", "metal": "Gold", "direction": "North-East", "body_part": "Fat, Liver, Thighs", "friendly": ["Sun", "Moon", "Mars"], "neutral": ["Saturn"], "enemy": ["Mercury", "Venus"], "significations": ["Wisdom", "Children", "Guru", "Fortune", "Expansion", "Knowledge"]}, {"name": "Venus", "sanskrit": "Shukra", "devanagari": "शुक्र", "symbol": "♀", "karaka": "Kalatrakaraka (Spouse), Love, Beauty, Arts, Luxury, Vehicles", "dignities": {"Exaltation": "Pisces 27°", "Debilitation": "Virgo 27°", "Moolatrikona": "Libra 0°-15°", "Own Sign": "Taurus, Libra"}, "nature": "Benefic", "gender": "Female", "vimshottari_dasha": "20 Years", "aspects": "7th house (100%)", "element": "Water", "caste": "Brahmin", "color": "#FFB6C1", "day": "Friday", "gemstone": "Diamond", "deity": "Lakshmi", "metal": "Silver", "direction": "South-East", "body_part": "Reproductive Organs, Face, Eyes", "friendly": ["Mercury", "Saturn"], "neutral": ["Mars", "Jupiter"], "enemy": ["Sun", "Moon"], "significations": ["Love", "Marriage", "Beauty", "Arts", "Luxury", "Comfort"]}, {"name": "Saturn", "sanskrit": "Shani", "devanagari": "शनि", "symbol": "♄", "karaka": "Ayu-karaka (Longevity), Karma, Discipline, Sorrow, Delays", "dignities": {"Exaltation": "Libra 20°", "Debilitation": "Aries 20°", "Moolatrikona": "Aquarius 0°-20°", "Own Sign": "Capricorn, Aquarius"}, "nature": "Most Malefic", "gender": "Neutral", "vimshottari_dasha": "19 Years", "aspects": "3rd, 7th, 10th houses", "element": "Air", "caste": "Shudra", "color": "#4169E1", "day": "Saturday", "gemstone": "Blue Sapphire", "deity": "Yama", "metal": "Iron", "direction": "West", "body_part": "Legs, Knees, Bones", "friendly": ["Mercury", "Venus"], "neutral": ["Jupiter"], "enemy": ["Sun", "Moon", "Mars"], "significations": ["Karma", "Discipline", "Delays", "Longevity", "Restrictions", "Service"]}, {"name": "Rahu", "sanskrit": "Rahu", "devanagari": "राहु", "symbol": "☊", "karaka": "Foreign things, Illusion, Obsession, Ambition, Technology", "dignities": {"Exaltation": "Taurus/Gemini", "Debilitation": "Scorpio/Sagittarius", "Moolatrikona": "Aquarius", "Own Sign": "Virgo"}, "nature": "Malefic", "gender": "N/A", "vimshottari_dasha": "18 Years", "aspects": "5th, 7th, 9th houses", "element": "Air", "caste": "Outcaste", "color": "#8B4513", "day": "N/A", "gemstone": "Hessonite", "deity": "Durga", "metal": "Lead", "direction": "South-West", "body_part": "N/A", "friendly": ["Mercury", "Venus", "Saturn"], "neutral": ["Jupiter"], "enemy": ["Sun", "Moon", "Mars"], "significations": ["Foreign", "Technology", "Obsession", "Unconventional", "Mystery"]}, {"name": "Ketu", "sanskrit": "Ketu", "devanagari": "केतु", "symbol": "☋", "karaka": "Mokshakaraka (Liberation), Spirituality, Detachment, Past Karma", "dignities": {"Exaltation": "Scorpio/Sagittarius", "Debilitation": "Taurus/Gemini", "Moolatrikona": "Leo", "Own Sign": "Pisces"}, "nature": "Malefic", "gender": "N/A", "vimshottari_dasha": "7 Years", "aspects": "5th, 7th, 9th houses", "element": "Fire", "caste": "Outcaste", "color": "#A9A9A9", "day": "N/A", "gemstone": "Cat's Eye", "deity": "Ganesha", "metal": "Lead", "direction": "N/A", "body_part": "N/A", "friendly": ["Sun", "Moon", "Mars"], "neutral": ["Jupiter", "Venus", "Saturn", "Mercury"], "enemy": [], "significations": ["Moksha", "Spirituality", "Detachment", "Past Life", "Intuition"]}]

    @staticmethod
    def get_all_rashis(): return [{"name": "Aries", "sanskrit": "Mesha", "devanagari": "मेष", "lord": "Mars", "tattva": "Fire", "modality": "Movable", "symbol": "Ram", "start_degree": 0, "end_degree": 30, "body_part": "Head, Face", "house": 1, "quality": "Cardinal", "description": "Represents initiative, courage, and new beginnings. The pioneer of the zodiac.", "color": "#FF6B6B", "nature": "Hot, Dry", "polarity": "Masculine"}, {"name": "Taurus", "sanskrit": "Vrishabha", "devanagari": "वृषभ", "lord": "Venus", "tattva": "Earth", "modality": "Fixed", "symbol": "Bull", "start_degree": 30, "end_degree": 60, "body_part": "Neck, Throat", "house": 2, "quality": "Fixed", "description": "Represents stability, material resources, and sensual pleasures.", "color": "#4ECDC4", "nature": "Cold, Dry", "polarity": "Feminine"}, {"name": "Gemini", "sanskrit": "Mithuna", "devanagari": "मिथुन", "lord": "Mercury", "tattva": "Air", "modality": "Dual", "symbol": "Twins", "start_degree": 60, "end_degree": 90, "body_part": "Arms, Shoulders, Lungs", "house": 3, "quality": "Mutable", "description": "Represents communication, intellect, and duality.", "color": "#FFE66D", "nature": "Hot, Moist", "polarity": "Masculine"}, {"name": "Cancer", "sanskrit": "Karka", "devanagari": "कर्क", "lord": "Moon", "tattva": "Water", "modality": "Movable", "symbol": "Crab", "start_degree": 90, "end_degree": 120, "body_part": "Chest, Breasts, Stomach", "house": 4, "quality": "Cardinal", "description": "Represents emotion, nurturing, and the inner world.", "color": "#95E1D3", "nature": "Cold, Moist", "polarity": "Feminine"}, {"name": "Leo", "sanskrit": "Simha", "devanagari": "सिंह", "lord": "Sun", "tattva": "Fire", "modality": "Fixed", "symbol": "Lion", "start_degree": 120, "end_degree": 150, "body_part": "Heart, Upper Back", "house": 5, "quality": "Fixed", "description": "Represents self-expression, leadership, and creative power.", "color": "#F38181", "nature": "Hot, Dry", "polarity": "Masculine"}, {"name": "Virgo", "sanskrit": "Kanya", "devanagari": "कन्या", "lord": "Mercury", "tattva": "Earth", "modality": "Dual", "symbol": "Maiden", "start_degree": 150, "end_degree": 180, "body_part": "Digestive System, Intestines", "house": 6, "quality": "Mutable", "description": "Represents service, analysis, and perfection.", "color": "#AA96DA", "nature": "Cold, Dry", "polarity": "Feminine"}, {"name": "Libra", "sanskrit": "Tula", "devanagari": "तुला", "lord": "Venus", "tattva": "Air", "modality": "Movable", "symbol": "Scales", "start_degree": 180, "end_degree": 210, "body_part": "Kidneys, Lower Back", "house": 7, "quality": "Cardinal", "description": "Represents harmony, relationships, and justice.", "color": "#FCBAD3", "nature": "Hot, Moist", "polarity": "Masculine"}, {"name": "Scorpio", "sanskrit": "Vrischika", "devanagari": "वृश्चिक", "lord": "Mars", "tattva": "Water", "modality": "Fixed", "symbol": "Scorpion", "start_degree": 210, "end_degree": 240, "body_part": "Reproductive Organs", "house": 8, "quality": "Fixed", "description": "Represents transformation, intensity, and hidden power.", "color": "#A8E6CF", "nature": "Cold, Moist", "polarity": "Feminine"}, {"name": "Sagittarius", "sanskrit": "Dhanu", "devanagari": "धनु", "lord": "Jupiter", "tattva": "Fire", "modality": "Dual", "symbol": "Archer", "start_degree": 240, "end_degree": 270, "body_part": "Hips, Thighs", "house": 9, "quality": "Mutable", "description": "Represents wisdom, expansion, and higher truth.", "color": "#FF8B94", "nature": "Hot, Dry", "polarity": "Masculine"}, {"name": "Capricorn", "sanskrit": "Makara", "devanagari": "मकर", "lord": "Saturn", "tattva": "Earth", "modality": "Movable", "symbol": "Sea-Goat", "start_degree": 270, "end_degree": 300, "body_part": "Knees, Bones", "house": 10, "quality": "Cardinal", "description": "Represents structure, discipline, and achievement.", "color": "#C7CEEA", "nature": "Cold, Dry", "polarity": "Feminine"}, {"name": "Aquarius", "sanskrit": "Kumbha", "devanagari": "कुम्भ", "lord": "Saturn", "tattva": "Air", "modality": "Fixed", "symbol": "Water Bearer", "start_degree": 300, "end_degree": 330, "body_part": "Ankles, Circulation", "house": 11, "quality": "Fixed", "description": "Represents innovation, humanity, and collective ideals.", "color": "#B4F8C8", "nature": "Hot, Moist", "polarity": "Masculine"}, {"name": "Pisces", "sanskrit": "Meena", "devanagari": "मीन", "lord": "Jupiter", "tattva": "Water", "modality": "Dual", "symbol": "Two Fishes", "start_degree": 330, "end_degree": 360, "body_part": "Feet, Lymphatic System", "house": 12, "quality": "Mutable", "description": "Represents spirituality, dissolution, and universal consciousness.", "color": "#FBE7C6", "nature": "Cold, Moist", "polarity": "Feminine"}]

#===================================================================================================
# ASTRONOMICAL CALCULATOR
#===================================================================================================
class AstronomicalCalculator:
    def __init__(self, ayanamsa='LAHIRI'):
        if SWISSEPH_AVAILABLE:
            try:
                swe.set_ephe_path(None)
                ayanamsa_code = getattr(swe, f'SIDM_{ayanamsa}')
                swe.set_sid_mode(ayanamsa_code)
                print(f"✅ AstronomicalCalculator initialized with {ayanamsa} Ayanamsa.")
            except Exception as e:
                print(f"⚠️ Error initializing Swiss Ephemeris: {e}")
                messagebox.showerror("Initialization Error", f"Could not set Swiss Ephemeris Ayanamsa mode: {e}")

    def calculate_planet_positions(self, dt_local, lat, lon, timezone_offset):
        if not SWISSEPH_AVAILABLE:
            messagebox.showerror("Dependency Missing", "The 'pyswisseph' library is required for accurate calculations.")
            return None
        try:
            dt_utc = dt_local - timedelta(hours=timezone_offset)
            jd_utc = swe.utc_to_jd(dt_utc.year, dt_utc.month, dt_utc.day,
                                     dt_utc.hour, dt_utc.minute, dt_utc.second, 1)[1]
            planet_codes = {
                "Sun": swe.SUN, "Moon": swe.MOON, "Mercury": swe.MERCURY,
                "Venus": swe.VENUS, "Mars": swe.MARS, "Jupiter": swe.JUPITER,
                "Saturn": swe.SATURN, "Rahu": swe.MEAN_NODE,
            }
            positions = {}
            _, ascmc = swe.houses(jd_utc, lat, lon, b'P')
            asc_longitude = ascmc[0]
            positions['Ascendant'] = self._process_longitude(asc_longitude)
            for name, code in planet_codes.items():
                planet_pos_data = swe.calc_ut(jd_utc, code, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)[0]
                planet_longitude = planet_pos_data[0]
                positions[name] = self._process_longitude(planet_longitude)
                positions[name]['speed'] = planet_pos_data[3]
            rahu_longitude = positions['Rahu']['longitude']
            ketu_longitude = (rahu_longitude + 180) % 360
            positions['Ketu'] = self._process_longitude(ketu_longitude)
            positions['Ketu']['speed'] = positions['Rahu'].get('speed', 0) * -1
            return positions
        except swe.Error as e:
            messagebox.showerror("Swiss Ephemeris Error", f"A calculation error occurred:\n\n{e}")
            return None
        except Exception as e:
            messagebox.showerror("Calculation Error", f"An unexpected error occurred during calculation:\n\n{e}")
            return None

    def _process_longitude(self, longitude):
        rashi_index = int(longitude / 30)
        rashi_name = EnhancedAstrologicalData.get_all_rashis()[rashi_index]['name']
        degree_in_rashi = longitude % 30
        nakshatra_name = "Unknown"
        for nak in EnhancedAstrologicalData.get_all_nakshatras():
            if nak['start_degree'] <= longitude < nak['end_degree']:
                nakshatra_name = nak['name']
                break
        dms_str = decimal_to_dms(degree_in_rashi)
        return {
            'longitude': longitude,
            'rashi': rashi_name,
            'degree_in_rashi': degree_in_rashi,
            'nakshatra': nakshatra_name,
            'dms': dms_str
        }

#===================================================================================================
# VARGA CALCULATOR (OVERHAULED & COMPREHENSIVE)
#===================================================================================================
class VargaCalculator:
    """
    OVERHAULED: A comprehensive and accurate Varga Chart calculator.
    This class contains the mathematical logic for calculating all major divisional charts
    using standard Parashari methods, including the user-provided logic for key vargas.
    """
    def __init__(self):
        self.D60_DEITIES = ("Ghora","Rakshasa","Deva","Kubera","Yaksha","Kinnara","Bhrashta","Kulaghna","Garala","Vahni","Maya","Puriihaka","Apampathi","Marutwana","Kaala","Sarpa","Amrita","Indu","Mridu","Komala","Heramba","Brahma","Vishnu","Maheshwara","Deva","Ardra","Kalinasa","Kshiteesa","Kamalakara","Gulika","Mrityu","Kaala","Davagni","Ghora","Yama","Kantaka","Sudha","Amrita","Poorna","VishaDagdha","Kulanasa","Vamshakshya","Utpata","Kaala","Saumya","Komala","Seetala","Karaladamshtra","Chandramukhi","Praveena","Kaalpavaka","Dandayudha","Nirmala","Saumya","Kroora","Atisheetala","Amrita","Payodhi","Bhramana","Chandrarekha")

    def calculate(self, varga_num, d1_lon, d1_sign):
        """Main dispatcher for varga calculations."""
        varga_map = {
            2: self._calculate_d2, 3: self._calculate_d3, 4: self._calculate_d4,
            5: self._calculate_d5, 6: self._calculate_d6, 7: self._calculate_d7,
            9: self._calculate_d9, 10: self._calculate_d10, 12: self._calculate_d12,
            16: self._calculate_d16, 20: self._calculate_d20, 24: self._calculate_d24,
            30: self._calculate_d30, 40: self._calculate_d40, 45: self._calculate_d45,
            60: self._calculate_d60
        }
        if varga_num in varga_map:
            return varga_map[varga_num](d1_lon, d1_sign)
        return None, None, "N/A"

    def _calculate_d2(self, d1_lon, d1_sign):
        amsa_index = math.floor(d1_lon / 15)
        lon = (d1_lon % 15) * 2
        sign_nat = EnhancedAstrologicalData.SIGN_NATURE[d1_sign]
        sign, details = (5, "Sun's Hora") if (sign_nat == "Odd" and amsa_index == 0) or (sign_nat == "Even" and amsa_index == 1) else (4, "Moon's Hora")
        return sign, lon, details

    def _calculate_d3(self, d1_lon, d1_sign):
        amsa_index = math.floor(d1_lon / 10)
        lon = (d1_lon % 10) * 3
        offset = [0, 4, 8][amsa_index]
        sign = (d1_sign + offset - 1) % 12 + 1
        return sign, lon, ""

    def _calculate_d4(self, d1_lon, d1_sign):
        amsa_index = math.floor(d1_lon / 7.5)
        lon = (d1_lon % 7.5) * 4
        sign = ((d1_sign - 1) + (amsa_index * 3)) % 12 + 1
        return sign, lon, ""

    def _calculate_d5(self, d1_lon, d1_sign):
        amsa_index = math.floor(d1_lon / 6)
        lon = (d1_lon % 6) * 5
        start_sign = 1 if EnhancedAstrologicalData.SIGN_NATURE[d1_sign] == "Odd" else 6
        sign = (start_sign + amsa_index - 1) % 12 + 1
        return sign, lon, ""

    def _calculate_d6(self, d1_lon, d1_sign):
        amsa_index = math.floor(d1_lon / 5)
        lon = (d1_lon % 5) * 6
        start_sign = 1 if EnhancedAstrologicalData.SIGN_NATURE[d1_sign] == "Odd" else 7
        sign = (start_sign + amsa_index - 1) % 12 + 1
        return sign, lon, ""

    def _calculate_d7(self, d1_lon, d1_sign):
        amsa_index = math.floor(d1_lon / (30/7))
        lon = (d1_lon % (30/7)) * 7
        start_sign = d1_sign if EnhancedAstrologicalData.SIGN_NATURE[d1_sign] == "Odd" else (d1_sign + 6)
        sign = (start_sign + amsa_index - 1) % 12 + 1
        return sign, lon, ""

    def _calculate_d9(self, d1_lon, d1_sign):
        amsa_index = math.floor(d1_lon / (30/9))
        lon = (d1_lon % (30/9)) * 9
        sign_mod = (d1_sign - 1) % 3
        start_signs = {0: 1, 1: 9, 2: 5} # Movable, Fixed, Dual
        sign = (start_signs[sign_mod] + amsa_index - 1) % 12 + 1
        return sign, lon, ""
    
    def _calculate_d10(self, d1_lon, d1_sign):
        amsa_index = math.floor(d1_lon / 3)
        lon = (d1_lon % 3) * 10
        start_sign = d1_sign if EnhancedAstrologicalData.SIGN_NATURE[d1_sign] == "Odd" else (d1_sign + 8)
        sign = (start_sign + amsa_index - 1) % 12 + 1
        return sign, lon, ""

    def _calculate_d12(self, d1_lon, d1_sign):
        amsa_index = math.floor(d1_lon / 2.5)
        lon = (d1_lon % 2.5) * 12
        sign = (d1_sign + amsa_index - 1) % 12 + 1
        return sign, lon, ""

    def _calculate_d16(self, d1_lon, d1_sign):
        amsa_index = math.floor(d1_lon / 1.875)
        lon = (d1_lon % 1.875) * 16
        sign_mod = (d1_sign - 1) % 3
        start_signs = {0: 1, 1: 5, 2: 9} # Movable, Fixed, Dual
        sign = (start_signs[sign_mod] + amsa_index - 1) % 12 + 1
        return sign, lon, ""

    def _calculate_d20(self, d1_lon, d1_sign):
        amsa_index = math.floor(d1_lon / 1.5)
        lon = (d1_lon % 1.5) * 20
        sign_mod = (d1_sign - 1) % 3
        start_signs = {0: 1, 1: 9, 2: 5} # Movable, Fixed, Dual
        sign = (start_signs[sign_mod] + amsa_index - 1) % 12 + 1
        return sign, lon, ""

    def _calculate_d24(self, d1_lon, d1_sign):
        amsa_index = math.floor(d1_lon / 1.25)
        lon = (d1_lon % 1.25) * 24
        start_sign = 5 if EnhancedAstrologicalData.SIGN_NATURE[d1_sign] == "Odd" else 4
        sign = (start_sign + amsa_index - 1) % 12 + 1
        return sign, lon, ""

    def _calculate_d30(self, d1_lon, d1_sign):
        lon = (d1_lon % 1) * 30 # Special case for Trimsamsa
        if EnhancedAstrologicalData.SIGN_NATURE[d1_sign] == "Odd":
            if 0 <= d1_lon < 5: sign = 1 # Mars
            elif 5 <= d1_lon < 10: sign = 11 # Saturn
            elif 10 <= d1_lon < 18: sign = 9 # Jupiter
            elif 18 <= d1_lon < 25: sign = 3 # Mercury
            else: sign = 7 # Venus
        else: # Even
            if 0 <= d1_lon < 5: sign = 2 # Venus
            elif 5 <= d1_lon < 12: sign = 6 # Mercury
            elif 12 <= d1_lon < 20: sign = 12 # Jupiter
            elif 20 <= d1_lon < 25: sign = 10 # Saturn
            else: sign = 8 # Mars
        return sign, lon, ""

    def _calculate_d40(self, d1_lon, d1_sign):
        amsa_index = math.floor(d1_lon / 0.75)
        lon = (d1_lon % 0.75) * 40
        start_sign = 1 if EnhancedAstrologicalData.SIGN_NATURE[d1_sign] == "Odd" else 7
        sign = (start_sign + amsa_index - 1) % 12 + 1
        return sign, lon, ""

    def _calculate_d45(self, d1_lon, d1_sign):
        amsa_index = math.floor(d1_lon / (30/45))
        lon = (d1_lon % (30/45)) * 45
        sign_mod = (d1_sign - 1) % 3
        start_signs = {0: 1, 1: 5, 2: 9} # Movable, Fixed, Dual
        sign = (start_signs[sign_mod] + amsa_index - 1) % 12 + 1
        return sign, lon, ""

    def _calculate_d60(self, d1_lon, d1_sign):
        # CORRECTED: D60 sign is the same as D1 sign. The deity is what matters.
        lon_from_aries = d1_lon + (d1_sign - 1) * 30
        amsa_index_raw = math.floor(lon_from_aries * 2)
        amsa_index_in_sign = amsa_index_raw % 60
        lon = (lon_from_aries * 2 % 1) * 30
        details = self.D60_DEITIES[amsa_index_in_sign]
        return d1_sign, lon, details


#===================================================================================================
# IMAGE GENERATOR
#===================================================================================================
class PlanetImageGenerator:
    # ... This entire class remains unchanged ...
    @staticmethod
    def create_planet_icon(planet_name, size=100):
        if not PIL_AVAILABLE: return None
        color = EnhancedAstrologicalData.PLANET_COLORS.get(planet_name, "#CCCCCC")
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        for i in range(5, 0, -1):
            alpha = int(50 * (i / 5))
            offset = i * 3
            glow_color = tuple(list(PlanetImageGenerator.hex_to_rgb(color)) + [alpha])
            draw.ellipse([offset, offset, size-offset, size-offset], fill=glow_color, outline=None)
        margin = 15
        draw.ellipse([margin, margin, size-margin, size-margin], fill=color, outline="#FFFFFF", width=2)
        try:
            font_size = int(size * 0.4)
            font = ImageFont.truetype("arial.ttf", font_size)
        except IOError:
            font = ImageFont.load_default()
        planet_data = next((p for p in EnhancedAstrologicalData.get_all_planets() if p['name'] == planet_name), None)
        if planet_data:
            symbol = planet_data.get('symbol', planet_name[0])
            bbox = draw.textbbox((0, 0), symbol, font=font)
            text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
            text_x, text_y = (size - text_width) / 2, (size - text_height) / 2
            draw.text((text_x, text_y), symbol, fill='white', font=font)
        return img
    @staticmethod
    def hex_to_rgb(hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    @staticmethod
    def create_zodiac_wheel(size=800, planet_positions=None):
        if not PIL_AVAILABLE: return None
        img = Image.new('RGBA', (size, size), (255, 255, 255, 255))
        draw = ImageDraw.Draw(img)
        center_x, center_y = size // 2, size // 2
        outer_radius, inner_radius = size // 2 - 20, size // 2 - 100
        rashis = EnhancedAstrologicalData.get_all_rashis()
        for i, rashi in enumerate(rashis):
            start_angle, end_angle = i * 30, (i + 1) * 30
            draw.pieslice([center_x - outer_radius, center_y - outer_radius, center_x + outer_radius, center_y + outer_radius], start_angle, end_angle, fill=rashi['color'] + '80', outline='#555', width=2)
        draw.ellipse([center_x - inner_radius, center_y - inner_radius, center_x + inner_radius, center_y + inner_radius], fill='white', outline='#555', width=2)
        for i in range(12):
            angle = math.radians(i * 30)
            x1, y1 = center_x + inner_radius * math.cos(angle), center_y + inner_radius * math.sin(angle)
            x2, y2 = center_x + outer_radius * math.cos(angle), center_y + outer_radius * math.sin(angle)
            draw.line([x1, y1, x2, y2], fill='#333333', width=2)
        try: font = ImageFont.truetype("arialbd.ttf", 16)
        except IOError: font = ImageFont.load_default()
        for i, rashi in enumerate(rashis):
            angle = math.radians(i * 30 + 15)
            text_radius = (outer_radius + inner_radius) / 2
            x, y = center_x + text_radius * math.cos(angle), center_y + text_radius * math.sin(angle)
            text = rashi['name'][:3].upper()
            bbox = draw.textbbox((0,0), text, font=font)
            text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
            draw.text((x - text_width/2, y - text_height/2), text, fill='#000000', font=font)
        if planet_positions:
            try: planet_font = ImageFont.truetype("arial.ttf", 14)
            except IOError: planet_font = ImageFont.load_default()
            for planet_name, pos_data in planet_positions.items():
                if planet_name == 'Ascendant':
                    asc_degree = pos_data['longitude']
                    angle = math.radians(asc_degree)
                    x1, y1 = center_x + (inner_radius-10) * math.cos(angle), center_y + (inner_radius-10) * math.sin(angle)
                    x2, y2 = center_x + outer_radius * math.cos(angle), center_y + outer_radius * math.sin(angle)
                    draw.line([x1, y1, x2, y2], fill='#E74C3C', width=3)
                    draw.text((x1 - 20, y1 - 10), "Asc", fill='#E74C3C', font=font)
                    continue
                degree, angle = pos_data['longitude'], math.radians(pos_data['longitude'])
                marker_radius = inner_radius - 40
                x, y = center_x + marker_radius * math.cos(angle), center_y + marker_radius * math.sin(angle)
                planet_color = EnhancedAstrologicalData.PLANET_COLORS.get(planet_name, '#000000')
                draw.ellipse([x-12, y-12, x+12, y+12], fill=planet_color, outline='white', width=2)
                label = planet_name[:2]
                draw.text((x-7, y-8), label, fill='white', font=planet_font)
        return img

#===================================================================================================
# THEME MANAGER
#===================================================================================================
class EnhancedThemeManager:
    # ... This entire class remains unchanged ...
    THEMES = {
        "Cosmic Dark": {"bg_dark": "#0D1B2A", "bg_light": "#E0E1DD", "accent": "#FF6B35", "neutral": "#1B263B", "success": "#06FFA5", "chart_bg": "#1B263B"},
        "Crimson Mystique": {"bg_dark": "#2c3e50", "bg_light": "#ecf0f1", "accent": "#e74c3c", "neutral": "#34495e", "success": "#27ae60", "chart_bg": "#34495e"},
        "Golden Temple": {"bg_dark": "#1A1A1D", "bg_light": "#F5F5F5", "accent": "#C3073F", "neutral": "#4E4E50", "success": "#00FFAA", "chart_bg": "#4E4E50"},
        "Ocean Depths": {"bg_dark": "#001524", "bg_light": "#F8F9FA", "accent": "#15616D", "neutral": "#003B46", "success": "#07A8A0", "chart_bg": "#003B46"},
        "Royal Purple": {"bg_dark": "#1A0033", "bg_light": "#F0F0F0", "accent": "#7209B7", "neutral": "#3C096C", "success": "#10F4B1", "chart_bg": "#3C096C"},
        "Emerald Forest": {"bg_dark": "#011C27", "bg_light": "#F0F2EF", "accent": "#00A878", "neutral": "#043948", "success": "#9FFFCB", "chart_bg": "#043948"},
        "Sunset Glow": {"bg_dark": "#2E0219", "bg_light": "#FFF8F0", "accent": "#F85A3E", "neutral": "#5A0834", "success": "#FFD670", "chart_bg": "#5A0834"},
        "Mystic Lilac": {"bg_dark": "#241E4E", "bg_light": "#E9E3FF", "accent": "#C37DFF", "neutral": "#3E3378", "success": "#A6FFD8", "chart_bg": "#3E3378"},
        "Obsidian & Gold": {"bg_dark": "#0B0B0B", "bg_light": "#EAEAEA", "accent": "#D4AF37", "neutral": "#222222", "success": "#B2D9AD", "chart_bg": "#222222"},
        "Deep Blue Sea": {"bg_dark": "#1A2E40", "bg_light": "#F2F2F2", "accent": "#0D8ABF", "neutral": "#264059", "success": "#27ae60", "chart_bg": "#1A2E40"},
        "Forest Green": {"bg_dark": "#2E4028", "bg_light": "#F2F2F2", "accent": "#59A627", "neutral": "#40593A", "success": "#27ae60", "chart_bg": "#2E4028"},
        "Classic Dark": {"bg_dark": "#262626", "bg_light": "#f5f5f5", "accent": "#00bfff", "neutral": "#333333", "success": "#27ae60", "chart_bg": "#262626"},
        "Classic Light": {"bg_dark": "#f0f0f0", "bg_light": "#1c1c1c", "accent": "#0078d7", "neutral": "#dcdcdc", "success": "#27ae60", "chart_bg": "#f0f0f0"}
    }
    @staticmethod
    def apply_theme(app, theme_name):
        theme = EnhancedThemeManager.THEMES.get(theme_name, EnhancedThemeManager.THEMES["Cosmic Dark"])
        app.current_theme_data = theme
        style = ttk.Style()
        style.theme_use('clam')
        bg_dark, bg_light, accent, neutral = theme["bg_dark"], theme["bg_light"], theme["accent"], theme["neutral"]
        is_light_theme = theme_name == "Classic Light"
        fg_color = bg_light if not is_light_theme else bg_dark
        main_bg_color = bg_dark if not is_light_theme else bg_light
        widget_bg_color = neutral if not is_light_theme else bg_dark
        select_fg_color = bg_dark if not is_light_theme else bg_light
        app.root.configure(bg=main_bg_color)
        style.configure('.', background=main_bg_color, foreground=fg_color, font=('Segoe UI', 10))
        style.configure('TFrame', background=main_bg_color)
        style.configure('TLabel', background=main_bg_color, foreground=fg_color)
        style.configure('Heading.TLabel', font=('Segoe UI', 12, 'bold'), foreground=accent)
        style.configure('Title.TLabel', font=('Segoe UI', 16, 'bold'), foreground=accent)
        style.configure('TNotebook', background=main_bg_color, borderwidth=0)
        style.configure('TNotebook.Tab', background=neutral, foreground=fg_color, padding=[15, 8], font=('Segoe UI', 10, 'bold'))
        style.map('TNotebook.Tab', background=[('selected', accent)], foreground=[('selected', select_fg_color)])
        style.configure('TLabelframe', background=main_bg_color, bordercolor=accent, relief='groove')
        style.configure('TLabelframe.Label', background=main_bg_color, foreground=accent, font=('Segoe UI', 11, 'bold'))
        style.configure('TButton', background=neutral, foreground=fg_color, font=('Segoe UI', 10, 'bold'), borderwidth=1, relief='flat', padding=10)
        style.map('TButton', background=[('active', accent)], foreground=[('active', select_fg_color)])
        style.configure('Accent.TButton', background=accent, foreground=select_fg_color, font=('Segoe UI', 12, 'bold'), padding=12)
        style.map('Accent.TButton', background=[('active', bg_light)], foreground=[('active', bg_dark)])
        style.configure('TEntry', fieldbackground=widget_bg_color, foreground=fg_color, insertcolor=fg_color, bordercolor=accent)
        style.map('TEntry', foreground=[('focus', fg_color)], fieldbackground=[('focus', widget_bg_color)])
        style.configure('TSpinbox', fieldbackground=widget_bg_color, foreground=fg_color, insertcolor=fg_color, arrowcolor=fg_color, bordercolor=accent)
        style.map('TSpinbox', background=[('active', neutral)])
        style.configure('TCombobox', fieldbackground=widget_bg_color, foreground=fg_color, selectbackground=accent, selectforeground=select_fg_color, arrowcolor=fg_color)
        style.map('TCombobox', fieldbackground=[('readonly', widget_bg_color)], selectbackground=[('readonly', accent)], foreground=[('readonly', fg_color)])
        app.root.option_add('*TCombobox*Listbox.background', widget_bg_color)
        app.root.option_add('*TCombobox*Listbox.foreground', fg_color)
        app.root.option_add('*TCombobox*Listbox.selectBackground', accent)
        app.root.option_add('*TCombobox*Listbox.selectForeground', select_fg_color)
        style.configure('Treeview', background=widget_bg_color, foreground=fg_color, fieldbackground=widget_bg_color, rowheight=30)
        style.configure('Treeview.Heading', background=neutral, foreground=accent, font=('Segoe UI', 11, 'bold'))
        style.map('Treeview', background=[('selected', accent)], foreground=[('selected', select_fg_color)])
        try:
            text_bg, text_fg = widget_bg_color, fg_color
            all_tabs = [app.kundli_tab, app.vighati_tab, app.transit_tab, app.dasha_tab, app.nakshatra_tab, app.planet_tab, app.rashi_tab, app.yoga_tab]
            for tab in all_tabs:
                for widget_name in ['results_text', 'details_text', 'analysis_text', 'info_text', 'transit_text', 'prediction_text', 'dasha_text', 'planet_text', 'rashi_text', 'rajyoga_text', 'dosha_text', 'mahapurusha_text']:
                    if hasattr(tab, widget_name):
                        getattr(tab, widget_name).config(background=text_bg, foreground=text_fg, insertbackground=accent, selectbackground=accent, selectforeground=select_fg_color)
                for widget_name in ['nak_listbox', 'rashi_listbox', 'planet_listbox']:
                    if hasattr(tab, widget_name):
                        getattr(tab, widget_name).config(background=text_bg, foreground=text_fg, selectbackground=accent, selectforeground=select_fg_color)
        except Exception as e:
            print(f"Warning: Could not apply theme to a specific non-ttk widget. Error: {e}")

#===================================================================================================
# MAIN ELITE APPLICATION
#===================================================================================================
class AstroVighatiElite:
    def __init__(self, root):
        self.root = root
        self.root.title("AstroVighati Pro Elite - Advanced Vedic Astrology Suite")
        self.root.geometry("1800x1000")
        self.root.minsize(1400, 800)
        self.astro_data = EnhancedAstrologicalData()
        self.calculator = AstronomicalCalculator()
        self.varga_calculator = VargaCalculator() # Using the new, comprehensive calculator
        self.planet_images = {}
        self.current_theme = tk.StringVar(value="Cosmic Dark")
        self.current_theme_data = {}
        self.create_status_bar()
        self.create_main_notebook()
        self.create_tabs()
        self.create_menu()
        EnhancedThemeManager.apply_theme(self, self.current_theme.get())
        if PIL_AVAILABLE:
            self.load_planet_images()
    def create_status_bar(self):
        self.status_var = tk.StringVar(value="Ready - Elite Edition | Sidereal Engine Active")
        ttk.Label(self.root, textvariable=self.status_var, relief='sunken', anchor='w', padding=5).pack(side='bottom', fill='x')
    def create_main_notebook(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=(10, 0))
    def create_tabs(self):
        self.kundli_tab = KundliGeneratorTab(self.notebook, self)
        self.notebook.add(self.kundli_tab, text='🎯 Kundli & Vargas')
        self.vighati_tab = EnhancedVighatiTab(self.notebook, self)
        self.notebook.add(self.vighati_tab, text='⚡ Vighati Rectifier')
        self.transit_tab = TransitCalculatorTab(self.notebook, self)
        self.notebook.add(self.transit_tab, text='🌍 Transits & Predictions')
        self.dasha_tab = DashaTimelineTab(self.notebook, self)
        self.notebook.add(self.dasha_tab, text='📊 Dasha Timeline')
        self.nakshatra_tab = EnhancedNakshatraTab(self.notebook, self)
        self.notebook.add(self.nakshatra_tab, text='⭐ Nakshatra Explorer')
        self.planet_tab = EnhancedPlanetTab(self.notebook, self)
        self.notebook.add(self.planet_tab, text='🪐 Planetary Guide')
        self.rashi_tab = EnhancedRashiTab(self.notebook, self)
        self.notebook.add(self.rashi_tab, text='♈ Rashi Explorer')
        self.yoga_tab = YogasDoshasTab(self.notebook, self)
        self.notebook.add(self.yoga_tab, text='🔮 Yogas & Doshas')
    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Exit", command=self.root.quit)
        theme_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Theme", menu=theme_menu)
        for theme_name in EnhancedThemeManager.THEMES.keys():
            theme_menu.add_radiobutton(label=theme_name, variable=self.current_theme, command=lambda t=theme_name: self.change_theme(t))
    def load_planet_images(self):
        for planet in self.astro_data.get_all_planets():
            name = planet['name']
            img = PlanetImageGenerator.create_planet_icon(name, 80)
            if img: self.planet_images[name] = ImageTk.PhotoImage(img)
    def change_theme(self, theme_name):
        EnhancedThemeManager.apply_theme(self, theme_name)
        self.status_var.set(f"Theme changed to {theme_name}")

#===================================================================================================
# TAB 1: KUNDLI GENERATOR (& VARGAS)
#===================================================================================================
class KundliGeneratorTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.chart_image = None
        self.planet_positions = {}
        # MODIFIED: Dynamically populate varga map from the central data store
        self.varga_map = self.app.astro_data.get_varga_descriptions()
        paned = ttk.PanedWindow(self, orient='horizontal')
        paned.pack(expand=True, fill='both', padx=10, pady=10)
        left_panel = ttk.Frame(paned, padding=10)
        paned.add(left_panel, weight=1)
        right_panel = ttk.Frame(paned, padding=10)
        paned.add(right_panel, weight=2)
        self.create_input_panel(left_panel)
        self.create_chart_panel(right_panel)

    def create_input_panel(self, parent):
        birth_frame = ttk.LabelFrame(parent, text="Birth Details", padding=15)
        birth_frame.pack(fill='x', pady=(0, 10), expand=True)
        birth_frame.grid_columnconfigure(1, weight=1)
        ttk.Label(birth_frame, text="Name:").grid(row=0, column=0, sticky='w', pady=5, padx=5)
        self.name_var = tk.StringVar()
        ttk.Entry(birth_frame, textvariable=self.name_var).grid(row=0, column=1, sticky='ew', pady=5, padx=5)
        ttk.Label(birth_frame, text="Date (DD/MM/YYYY):").grid(row=1, column=0, sticky='w', pady=5, padx=5)
        date_frame = ttk.Frame(birth_frame)
        date_frame.grid(row=1, column=1, sticky='ew', pady=5, padx=5)
        self.day_var, self.month_var, self.year_var = tk.StringVar(value="14"), tk.StringVar(value="11"), tk.StringVar(value="2003")
        ttk.Spinbox(date_frame, from_=1, to=31, textvariable=self.day_var, width=5).pack(side='left', fill='x', expand=True)
        ttk.Spinbox(date_frame, from_=1, to=12, textvariable=self.month_var, width=5).pack(side='left', fill='x', expand=True)
        ttk.Spinbox(date_frame, from_=1900, to=2100, textvariable=self.year_var, width=8).pack(side='left', fill='x', expand=True)
        
        # MODIFIED: Input for HH:MM:SS
        ttk.Label(birth_frame, text="Time (HH:MM:SS):").grid(row=2, column=0, sticky='w', pady=5, padx=5)
        time_frame = ttk.Frame(birth_frame)
        time_frame.grid(row=2, column=1, sticky='ew', pady=5, padx=5)
        self.hour_var, self.minute_var, self.second_var = tk.StringVar(value="19"), tk.StringVar(value="41"), tk.StringVar(value="46")
        ttk.Spinbox(time_frame, from_=0, to=23, textvariable=self.hour_var, width=5, format="%02.0f").pack(side='left', fill='x', expand=True)
        ttk.Spinbox(time_frame, from_=0, to=59, textvariable=self.minute_var, width=5, format="%02.0f").pack(side='left', fill='x', expand=True)
        ttk.Spinbox(time_frame, from_=0, to=59, textvariable=self.second_var, width=5, format="%02.0f").pack(side='left', fill='x', expand=True)

        location_frame = ttk.LabelFrame(parent, text="Location", padding=15)
        location_frame.pack(fill='x', pady=(0, 10), expand=True)
        location_frame.grid_columnconfigure(1, weight=1)
        ttk.Label(location_frame, text="Latitude:").grid(row=0, column=0, sticky='w', pady=5, padx=5)
        self.lat_var = tk.StringVar(value="28.8344")
        ttk.Entry(location_frame, textvariable=self.lat_var).grid(row=0, column=1, sticky='ew', pady=5, padx=5)
        ttk.Label(location_frame, text="Longitude:").grid(row=1, column=0, sticky='w', pady=5, padx=5)
        self.lon_var = tk.StringVar(value="77.5699")
        ttk.Entry(location_frame, textvariable=self.lon_var).grid(row=1, column=1, sticky='ew', pady=5, padx=5)
        ttk.Label(location_frame, text="Timezone Offset (UTC):").grid(row=3, column=0, sticky='w', pady=5, padx=5)
        self.tz_var = tk.StringVar(value="5.5")
        ttk.Entry(location_frame, textvariable=self.tz_var).grid(row=3, column=1, sticky='ew', pady=5, padx=5)
        ttk.Button(parent, text="🎯 Generate Kundli", command=self.generate_kundli, style='Accent.TButton').pack(fill='x', pady=20, ipady=10)
        # ... Rest of input panel is unchanged ...
        info_frame = ttk.LabelFrame(parent, text="Quick Info", padding=10)
        info_frame.pack(fill='both', expand=True)
        self.info_text = tk.Text(info_frame, height=10, wrap='word', font=('Segoe UI', 9))
        self.info_text.pack(fill='both', expand=True)
        self.info_text.insert('1.0', "Generate a chart to see quick information...")
        self.info_text.config(state='disabled')

    def create_chart_panel(self, parent):
        chart_frame = ttk.LabelFrame(parent, text="Birth Chart (Kundli / कुंडली)", padding=10)
        chart_frame.pack(fill='both', expand=True, pady=(0, 10))
        self.chart_canvas = tk.Canvas(chart_frame, bg='white', highlightthickness=0)
        self.chart_canvas.pack(expand=True, fill='both')
        self.chart_canvas.bind("<Configure>", self.on_resize_chart)
        analysis_notebook = ttk.Notebook(parent)
        analysis_notebook.pack(fill='both', expand=True)
        positions_frame = ttk.Frame(analysis_notebook)
        analysis_notebook.add(positions_frame, text="Planetary Positions (D1)")
        columns = ('planet', 'rashi', 'dms', 'nakshatra', 'lord')
        self.positions_tree = ttk.Treeview(positions_frame, columns=columns, show='headings', height=10)
        self.positions_tree.heading('planet', text='Planet'); self.positions_tree.heading('rashi', text='Rashi')
        self.positions_tree.heading('dms', text='Longitude'); self.positions_tree.heading('nakshatra', text='Nakshatra')
        self.positions_tree.heading('lord', text='Nakshatra Lord')
        for col, width in [('planet', 150), ('rashi', 150), ('dms', 120), ('nakshatra', 200), ('lord', 100)]:
            self.positions_tree.column(col, width=width, anchor='center')
        scrollbar = ttk.Scrollbar(positions_frame, orient='vertical', command=self.positions_tree.yview)
        self.positions_tree.configure(yscrollcommand=scrollbar.set)
        self.positions_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # MODIFIED: Varga Tab now has more controls
        varga_frame = ttk.Frame(analysis_notebook, padding=10)
        analysis_notebook.add(varga_frame, text="Divisional Charts (Vargas)")

        varga_control_frame = ttk.Frame(varga_frame)
        varga_control_frame.pack(fill='x', pady=(0, 10))
        ttk.Label(varga_control_frame, text="Select Varga Chart:").pack(side='left', padx=(0, 10))
        self.varga_var = tk.StringVar()
        varga_combo = ttk.Combobox(varga_control_frame, textvariable=self.varga_var,
                                     values=list(self.varga_map.keys()), state="readonly", width=40)
        varga_combo.pack(side='left', fill='x', expand=True)
        varga_combo.set("D9 - Navamsa")
        varga_combo.bind("<<ComboboxSelected>>", self.update_varga_display)

        varga_results_frame = ttk.Frame(varga_frame)
        varga_results_frame.pack(fill='both', expand=True, pady=(10,0))
        
        self.varga_desc_text = tk.Text(varga_results_frame, height=5, wrap='word', font=('Segoe UI', 10, 'italic'))
        self.varga_desc_text.pack(fill='x', pady=(0, 10))

        varga_columns = ('planet', 'varga_rashi', 'varga_dms', 'details')
        self.varga_tree = ttk.Treeview(varga_results_frame, columns=varga_columns, show='headings')
        self.varga_tree.heading('planet', text='Planet'); self.varga_tree.heading('varga_rashi', text='Varga Rashi')
        self.varga_tree.heading('varga_dms', text='Varga Longitude'); self.varga_tree.heading('details', text='Details')
        self.varga_tree.pack(fill='both', expand=True)

    def on_resize_chart(self, event):
        if self.chart_image:
            self.chart_canvas.delete('all')
            canvas_width, canvas_height = event.width, event.height
            new_size = min(canvas_width, canvas_height)
            if new_size > 50:
                chart_img = PlanetImageGenerator.create_zodiac_wheel(new_size, self.planet_positions)
                if chart_img:
                    self.chart_image = ImageTk.PhotoImage(chart_img)
                    self.chart_canvas.create_image(canvas_width / 2, canvas_height / 2, image=self.chart_image)

    def generate_kundli(self):
        try:
            # MODIFIED: Read seconds value and use it in datetime constructor
            day, month, year = int(self.day_var.get()), int(self.month_var.get()), int(self.year_var.get())
            hour, minute, second = int(self.hour_var.get()), int(self.minute_var.get()), int(self.second_var.get())
            lat, lon, tz_offset = float(self.lat_var.get()), float(self.lon_var.get()), float(self.tz_var.get())
            birth_dt_local = datetime(year, month, day, hour, minute, second)

            self.app.status_var.set("Calculating Sidereal positions (Lahiri)...")
            self.planet_positions = self.app.calculator.calculate_planet_positions(birth_dt_local, lat, lon, tz_offset)
            if not self.planet_positions:
                self.app.status_var.set("Calculation failed.")
                return

            self.update_positions_tree()
            self.generate_chart_image()
            self.update_quick_info()
            self.update_varga_display() # This will now show D9 by default
            self.app.status_var.set("Kundli generated successfully!")
            messagebox.showinfo("Success", "Kundli and Varga charts generated successfully!")
        except ValueError:
            messagebox.showerror("Input Error", "Please ensure all fields have valid numbers.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate Kundli:\n{str(e)}")

    def update_positions_tree(self):
        self.positions_tree.delete(*self.positions_tree.get_children())
        planet_order = ["Ascendant", "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
        for planet_name in planet_order:
            if planet_name in self.planet_positions:
                pos_data = self.planet_positions[planet_name]
                rashi, dms, nak_eng = pos_data.get('rashi', 'N/A'), pos_data.get('dms', 'N/A'), pos_data.get('nakshatra', 'N/A')
                planet_info = next((p for p in self.app.astro_data.get_all_planets() if p['name'] == planet_name), {})
                rashi_info = next((r for r in self.app.astro_data.get_all_rashis() if r['name'] == rashi), {})
                nak_info = next((n for n in self.app.astro_data.get_all_nakshatras() if n['name'] == nak_eng), {})
                planet_display = f"{planet_name} ({planet_info.get('devanagari', '')})"
                rashi_display = f"{rashi} ({rashi_info.get('devanagari', '')})"
                nak_display = f"{nak_eng} ({nak_info.get('devanagari', '')})"
                lord = nak_info.get('lord', 'N/A')
                self.positions_tree.insert('', 'end', values=(planet_display, rashi_display, dms, nak_display, lord))

    def generate_chart_image(self):
        if not PIL_AVAILABLE: return
        canvas_size = min(self.chart_canvas.winfo_width(), self.chart_canvas.winfo_height()) - 10
        chart_img = PlanetImageGenerator.create_zodiac_wheel(canvas_size, self.planet_positions)
        if chart_img:
            self.chart_image = ImageTk.PhotoImage(chart_img)
            self.chart_canvas.delete('all')
            self.chart_canvas.create_image(self.chart_canvas.winfo_width() / 2, self.chart_canvas.winfo_height() / 2, image=self.chart_image)

    def update_quick_info(self):
        self.info_text.config(state='normal')
        self.info_text.delete('1.0', tk.END)
        info = "═══ QUICK REFERENCE ═══\n\n"
        if 'Ascendant' in self.planet_positions:
            asc_info = next((r for r in self.app.astro_data.get_all_rashis() if r['name'] == self.planet_positions['Ascendant']['rashi']), {})
            info += f"🔸 Ascendant: {asc_info.get('name')} ({asc_info.get('devanagari')})\n"
        if 'Moon' in self.planet_positions:
            moon_rashi_info = next((r for r in self.app.astro_data.get_all_rashis() if r['name'] == self.planet_positions['Moon']['rashi']), {})
            moon_nak_info = next((n for n in self.app.astro_data.get_all_nakshatras() if n['name'] == self.planet_positions['Moon']['nakshatra']), {})
            info += f"🌙 Moon Sign: {moon_rashi_info.get('name')} ({moon_rashi_info.get('devanagari')})\n"
            info += f"⭐ Birth Star: {moon_nak_info.get('name')} ({moon_nak_info.get('devanagari')})\n"
        self.info_text.insert('1.0', info)
        self.info_text.config(state='disabled')

    def update_varga_display(self, event=None):
        self.varga_tree.delete(*self.varga_tree.get_children())
        self.varga_desc_text.delete('1.0', tk.END)

        if not self.planet_positions:
            self.varga_tree.insert('', 'end', values=("Please generate a D1 chart first.", "", "", ""))
            return

        selected_varga_key = self.varga_var.get()
        if not selected_varga_key: return

        varga_info = self.varga_map[selected_varga_key]
        varga_num = varga_info['num']
        
        # Display the description for the selected varga
        self.varga_desc_text.insert('1.0', f"{varga_info['title']}\n\n{varga_info['description']}")

        self.app.status_var.set(f"Calculating {selected_varga_key}...")
        planet_order = ["Ascendant", "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]

        for planet_name in planet_order:
            if planet_name in self.planet_positions:
                d1_data = self.planet_positions[planet_name]
                d1_lon_in_sign = d1_data['degree_in_rashi']
                d1_sign_num = EnhancedAstrologicalData.SIGN_NAME_TO_NUM[d1_data['rashi']]
                
                varga_sign_num, varga_lon_dec, details = self.app.varga_calculator.calculate(varga_num, d1_lon_in_sign, d1_sign_num)
                
                if varga_sign_num is not None:
                    varga_sign_name = EnhancedAstrologicalData.SIGNS[varga_sign_num]
                    varga_lon_dms = decimal_to_dms(varga_lon_dec)
                    self.varga_tree.insert('', 'end', values=(planet_name, varga_sign_name, varga_lon_dms, details))
        
        self.app.status_var.set(f"{selected_varga_key} chart calculated.")


#===================================================================================================
# The rest of the Tab classes (EnhancedVighatiTab, TransitCalculatorTab, etc.) remain unchanged.
# They are omitted here for brevity but are part of the full, working script.
#===================================================================================================

# ... Paste the full, unchanged code for the following classes here:
# - EnhancedVighatiTab
# - TransitCalculatorTab
# - DashaTimelineTab
# - EnhancedNakshatraTab
# - EnhancedPlanetTab
# - EnhancedRashiTab
# - YogasDoshasTab

class EnhancedVighatiTab(ttk.Frame):
    """
    This tab implements the Vighati system of birth time rectification. It helps
    astrologers fine-tune an approximate birth time by finding moments that align
    with a known birth Nakshatra, based on the time elapsed since sunrise.
    """

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.nakshatras = self.app.astro_data.get_all_nakshatras()
        self.create_ui()

    def create_ui(self):
        """Creates the user interface for the Vighati Rectifier."""
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(expand=True, fill='both')

        # --- Title and Instructions ---
        ttk.Label(main_frame, text="⚡ VIGHATI BIRTH TIME RECTIFIER", style='Title.TLabel').pack(pady=(0, 20))

        # --- Input Section ---
        input_frame = ttk.LabelFrame(main_frame, text="Input Parameters", padding=20)
        input_frame.pack(fill='x', pady=(0, 15))
        input_frame.grid_columnconfigure(1, weight=1)

        # Approximate Birth Time input
        ttk.Label(input_frame, text="Approximate Birth Time:", style='Heading.TLabel').grid(row=0, column=0, sticky='w', pady=10)
        time_frame = ttk.Frame(input_frame)
        time_frame.grid(row=0, column=1, sticky='ew', padx=20)
        self.hour_var = tk.StringVar(value="12")
        self.minute_var = tk.StringVar(value="0")
        self.second_var = tk.StringVar(value="0")
        ttk.Spinbox(time_frame, from_=0, to=23, textvariable=self.hour_var, width=5, format="%02.0f").pack(side='left', fill='x', expand=True)
        ttk.Spinbox(time_frame, from_=0, to=59, textvariable=self.minute_var, width=5, format="%02.0f").pack(side='left', fill='x', expand=True)
        ttk.Spinbox(time_frame, from_=0, to=59, textvariable=self.second_var, width=5, format="%02.0f").pack(side='left', fill='x', expand=True)

        # Sunrise Time input
        ttk.Label(input_frame, text="Sunrise Time:", style='Heading.TLabel').grid(row=1, column=0, sticky='w', pady=10)
        sunrise_frame = ttk.Frame(input_frame)
        sunrise_frame.grid(row=1, column=1, sticky='ew', padx=20)
        self.sunrise_hour = tk.StringVar(value="6")
        self.sunrise_min = tk.StringVar(value="0")
        ttk.Spinbox(sunrise_frame, from_=0, to=23, textvariable=self.sunrise_hour, width=5, format="%02.0f").pack(side='left', fill='x', expand=True)
        ttk.Spinbox(sunrise_frame, from_=0, to=59, textvariable=self.sunrise_min, width=5, format="%02.0f").pack(side='left', fill='x', expand=True)

        # Target Nakshatra dropdown
        ttk.Label(input_frame, text="Target Nakshatra:", style='Heading.TLabel').grid(row=2, column=0, sticky='w', pady=10)
        self.nak_var = tk.StringVar()
        nak_values = [f"{n['name']} ({n['devanagari']})" for n in self.nakshatras]
        nak_combo = ttk.Combobox(input_frame, textvariable=self.nak_var, values=nak_values, state='readonly')
        nak_combo.grid(row=2, column=1, sticky='ew', padx=20)
        nak_combo.set(nak_values[0])

        # Search Range slider for time window
        ttk.Label(input_frame, text="Search Range (minutes):", style='Heading.TLabel').grid(row=3, column=0, sticky='w', pady=10)
        range_frame = ttk.Frame(input_frame)
        range_frame.grid(row=3, column=1, sticky='ew', padx=20)
        self.range_var = tk.IntVar(value=30)
        range_scale = ttk.Scale(range_frame, from_=5, to=120, variable=self.range_var, orient='horizontal')
        range_scale.pack(side='left', fill='x', expand=True)
        self.range_label = ttk.Label(range_frame, text="30 min")
        self.range_label.pack(side='left', padx=10)
        self.range_var.trace_add('write', lambda *args: self.range_label.config(text=f"{self.range_var.get()} min"))

        # --- Action Button ---
        ttk.Button(input_frame, text="🚀 Calculate & Rectify", command=self.calculate, style='Accent.TButton').grid(row=4, column=0, columnspan=2, pady=20, ipadx=30, ipady=10)

        # --- Results Section ---
        results_frame = ttk.LabelFrame(main_frame, text="Results", padding=10)
        results_frame.pack(fill='both', expand=True)
        self.results_text = scrolledtext.ScrolledText(results_frame, font=('Courier New', 10), wrap='word')
        self.results_text.pack(fill='both', expand=True)
        self.results_text.insert('1.0', "Enter parameters and click Calculate...")

    def calculate(self):
        self.results_text.delete('1.0', tk.END)
        self.results_text.insert('1.0', "Calculating...\n")
        hour, minute, second = int(self.hour_var.get()), int(self.minute_var.get()), int(self.second_var.get())
        sunrise_h, sunrise_m = int(self.sunrise_hour.get()), int(self.sunrise_min.get())
        target_nak_full = self.nak_var.get()
        target_nak_eng = target_nak_full.split(' (')[0]
        search_range = self.range_var.get()
        target_nak_data = next((n for n in self.nakshatras if n['name'] == target_nak_eng), None)
        if not target_nak_data:
            messagebox.showerror("Error", "Invalid Nakshatra selected")
            return
        target_remainder = int(target_nak_data['remainder'])
        birth_seconds = hour * 3600 + minute * 60 + second
        sunrise_seconds = sunrise_h * 3600 + sunrise_m * 60
        time_diff = birth_seconds - sunrise_seconds
        if time_diff < 0: time_diff += 86400
        vighati_value = time_diff / 24.0
        vighati_rounded = round(vighati_value)
        computed_remainder = int((vighati_rounded * 4) / 9) % 9
        is_match = (computed_remainder == target_remainder)
        results = f"INITIAL CALCULATION:\nTime from Sunrise: {time_diff // 3600:.0f}h {(time_diff % 3600) // 60:.0f}m {time_diff % 60:.0f}s\nComputed Remainder: {computed_remainder}\nMatch Status: {'✓ MATCH!' if is_match else '✗ NO MATCH'}\n\n"
        matches_found = 0
        if not is_match:
            results += "SEARCHING FOR MATCHING TIMES:\n"
            search_seconds = search_range * 60
            for offset in range(-search_seconds, search_seconds + 1):
                test_seconds = birth_seconds + offset
                if test_seconds < 0: test_seconds += 86400
                elif test_seconds >= 86400: test_seconds -= 86400
                new_diff = test_seconds - sunrise_seconds
                if new_diff < 0: new_diff += 86400
                new_vighati_rounded = round(new_diff / 24.0)
                new_remainder = int((new_vighati_rounded * 4) / 9) % 9
                if new_remainder == target_remainder:
                    matches_found += 1
                    test_h, test_m, test_s = test_seconds // 3600, (test_seconds % 3600) // 60, test_seconds % 60
                    results += f"Match found at: {test_h:02d}:{test_m:02d}:{test_s:02d}\n"
                    if matches_found >= 15:
                        results += "... (more matches exist)\n"
                        break
        self.results_text.insert('1.0', results)

class TransitCalculatorTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.create_ui()
    def create_ui(self):
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(expand=True, fill='both')
        ttk.Label(main_frame, text="🌍 TRANSIT CALCULATOR & PREDICTIONS", style='Title.TLabel').pack(pady=(0, 20))
        control_frame = ttk.LabelFrame(main_frame, text="Transit Date", padding=15)
        control_frame.pack(fill='x', pady=(0, 15))
        ttk.Button(control_frame, text="📅 Show Current Transits", command=self.show_current_transits, style='Accent.TButton').pack(side='left', padx=5, ipady=8)
        results_notebook = ttk.Notebook(main_frame)
        results_notebook.pack(fill='both', expand=True)
        transit_frame = ttk.Frame(results_notebook)
        results_notebook.add(transit_frame, text="Current Positions")
        self.transit_text = scrolledtext.ScrolledText(transit_frame, font=('Courier New', 10), wrap='word')
        self.transit_text.pack(fill='both', expand=True)
        self.transit_text.insert('1.0', "Click 'Show Current Transits' to see real-time planetary positions...")
    def show_current_transits(self):
        now_utc = datetime.utcnow()
        now_local = datetime.now()
        positions = self.app.calculator.calculate_planet_positions(now_utc, 28.6139, 77.2090, 0)
        text = f"CURRENT PLANETARY TRANSITS\nDate & Time: {now_local.strftime('%d %B %Y, %H:%M:%S')}\n\n"
        for planet in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]:
            if planet in positions:
                data = positions[planet]
                text += f"{planet:<10}: {data.get('rashi', 'N/A'):<15} {data.get('degree_in_rashi', 0):.2f}°\n"
        self.transit_text.delete('1.0', tk.END)
        self.transit_text.insert('1.0', text)

class DashaTimelineTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.create_ui()
    def create_ui(self):
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(expand=True, fill='both')
        ttk.Label(main_frame, text="📊 VIMSHOTTARI DASHA TIMELINE", style='Title.TLabel').pack(pady=(0, 20))
        input_frame = ttk.LabelFrame(main_frame, text="Birth Details", padding=15)
        input_frame.pack(fill='x', pady=(0, 15))
        ttk.Label(input_frame, text="Birth Date:").grid(row=0, column=0, sticky='w', pady=5)
        self.birth_date_var = tk.StringVar(value="08/10/2003")
        ttk.Entry(input_frame, textvariable=self.birth_date_var).grid(row=0, column=1, sticky='ew', padx=10)
        ttk.Button(input_frame, text="Auto-Fill from Kundli", command=self.autofill_from_kundli).grid(row=1, column=0, pady=10)
        ttk.Button(input_frame, text="Calculate Dasha", command=self.calculate_dasha, style='Accent.TButton').grid(row=1, column=1, pady=10)
        self.dasha_text = scrolledtext.ScrolledText(main_frame, font=('Courier New', 10), wrap='word')
        self.dasha_text.pack(fill='both', expand=True)
    def autofill_from_kundli(self):
        kundli_tab = self.app.kundli_tab
        if kundli_tab.planet_positions:
            self.birth_date_var.set(f"{kundli_tab.day_var.get()}/{kundli_tab.month_var.get()}/{kundli_tab.year_var.get()}")
            # Additional logic to set Nakshatra if needed
    def calculate_dasha(self):
        # Dummy calculation for now
        self.dasha_text.delete('1.0', tk.END)
        self.dasha_text.insert('1.0', "Dasha calculation based on precise Moon degree is a future feature.")

class EnhancedNakshatraTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.create_ui()
    def create_ui(self):
        paned = ttk.PanedWindow(self, orient='horizontal')
        paned.pack(expand=True, fill='both', padx=10, pady=10)
        left_panel = ttk.Frame(paned, padding=10)
        paned.add(left_panel, weight=1)
        ttk.Label(left_panel, text="⭐ NAKSHATRA LIST", style='Heading.TLabel').pack(pady=(0, 10))
        self.nak_listbox = tk.Listbox(left_panel, font=('Segoe UI', 11))
        self.nak_listbox.pack(fill='both', expand=True)
        self.nak_listbox.bind('<<ListboxSelect>>', self.on_select)
        for nak in self.app.astro_data.get_all_nakshatras():
            self.nak_listbox.insert(tk.END, f"{nak['name']} ({nak['devanagari']})")
        right_panel = ttk.Frame(paned, padding=10)
        paned.add(right_panel, weight=2)
        self.details_text = scrolledtext.ScrolledText(right_panel, font=('Segoe UI', 11), wrap='word')
        self.details_text.pack(fill='both', expand=True)
        self.nak_listbox.selection_set(0)
        self.on_select(None)
    def on_select(self, event):
        selection = self.nak_listbox.curselection()
        if not selection: return
        nak_name_full = self.nak_listbox.get(selection[0])
        nak_name_eng = nak_name_full.split(' (')[0]
        nak_data = next((n for n in self.app.astro_data.get_all_nakshatras() if n['name'] == nak_name_eng), None)
        if nak_data: self.show_details(nak_data)
    def show_details(self, nak):
        self.details_text.delete('1.0', tk.END)
        details = f"{nak['name'].upper()} ({nak['devanagari']})\n\nRuling Lord: {nak['lord']}\nDeity: {nak['deity']}\nKeywords: {nak['keywords']}"
        self.details_text.insert('1.0', details)

class EnhancedPlanetTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.create_ui()
    def create_ui(self):
        paned = ttk.PanedWindow(self, orient='horizontal')
        paned.pack(expand=True, fill='both', padx=10, pady=10)
        left_panel = ttk.Frame(paned, padding=10)
        paned.add(left_panel, weight=1)
        for planet in self.app.astro_data.get_all_planets():
            ttk.Button(left_panel, text=f"{planet['symbol']} {planet['name']}", command=lambda p=planet: self.show_planet(p)).pack(fill='x', pady=2)
        right_panel = ttk.Frame(paned, padding=10)
        paned.add(right_panel, weight=3)
        self.planet_text = scrolledtext.ScrolledText(right_panel, font=('Segoe UI', 10), wrap='word')
        self.planet_text.pack(fill='both', expand=True)
        self.show_planet(self.app.astro_data.get_all_planets()[0])
    def show_planet(self, planet):
        self.planet_text.delete('1.0', tk.END)
        details = f"{planet['name'].upper()}\n\nKaraka: {planet['karaka']}\n\nExaltation: {planet['dignities']['Exaltation']}"
        self.planet_text.insert('1.0', details)

class EnhancedRashiTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.create_ui()
    def create_ui(self):
        paned = ttk.PanedWindow(self, orient='horizontal')
        paned.pack(expand=True, fill='both', padx=10, pady=10)
        left_panel = ttk.Frame(paned, padding=10)
        paned.add(left_panel, weight=1)
        self.rashi_listbox = tk.Listbox(left_panel, font=('Segoe UI', 12))
        self.rashi_listbox.pack(fill='both', expand=True)
        self.rashi_listbox.bind('<<ListboxSelect>>', self.on_select)
        for rashi in self.app.astro_data.get_all_rashis():
            self.rashi_listbox.insert(tk.END, f" {rashi['name']}")
        right_panel = ttk.Frame(paned, padding=10)
        paned.add(right_panel, weight=2)
        self.rashi_text = scrolledtext.ScrolledText(right_panel, font=('Segoe UI', 11), wrap='word')
        self.rashi_text.pack(fill='both', expand=True)
        self.rashi_listbox.selection_set(0)
        self.on_select(None)
    def on_select(self, event):
        selection = self.rashi_listbox.curselection()
        if not selection: return
        rashi_name = self.rashi_listbox.get(selection[0]).strip()
        rashi_data = next((r for r in self.app.astro_data.get_all_rashis() if r['name'] == rashi_name), None)
        if rashi_data: self.show_details(rashi_data)
    def show_details(self, rashi):
        self.rashi_text.delete('1.0', tk.END)
        details = f"{rashi['name'].upper()}\n\nLord: {rashi['lord']}\nElement: {rashi['tattva']}\n{rashi['description']}"
        self.rashi_text.insert('1.0', details)

class YogasDoshasTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.create_ui()
    def create_ui(self):
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(expand=True, fill='both')
        ttk.Label(main_frame, text="🔮 YOGAS & DOSHAS ANALYZER", style='Title.TLabel').pack(pady=(0, 20))
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill='both', expand=True)
        rajyoga_frame = ttk.Frame(notebook)
        notebook.add(rajyoga_frame, text="Rajyogas")
        self.rajyoga_text = scrolledtext.ScrolledText(rajyoga_frame, font=('Segoe UI', 10), wrap='word')
        self.rajyoga_text.pack(fill='both', expand=True)
        self.rajyoga_text.insert('1.0', "Information on Rajyogas...")

#===================================================================================================
# MAIN EXECUTION BLOCK
#===================================================================================================
if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = AstroVighatiElite(root)
        print("\n🌟 ASTROVIGHATI PRO ELITE v4.4 is now running. Please use the GUI window. 🌟\n")
        root.mainloop()
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"\nCRITICAL APPLICATION ERROR:\n{error_details}")
        try:
            error_root = tk.Tk()
            error_root.withdraw()
            messagebox.showerror("Critical Application Error", f"A fatal error occurred: {e}\n\nCheck the console for details.")
        except:
            pass