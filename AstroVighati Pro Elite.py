# GUI Version - 5.0

""" AstroVighati Pro Elite: Advanced Vedic Astrology Suite
Version: 5.0 with Integrated Knowledge Base and Advanced Varga Analysis

Description:
This script creates a comprehensive desktop application for Vedic astrology using Python's Tkinter library.
The application is designed with a modular, tab-based interface, where each tab provides a specific
astrological tool. This version incorporates Devanagari script for key astrological terms and utilizes
a professionally accurate, Sidereal (Lahiri Ayanamsa) calculation engine for both the Natal (D1)
and all major Divisional (Varga) charts.

The analytical core has been significantly upgraded with an integrated knowledge base derived from
classical texts like P.V.R. Narasimha Rao's "Vedic Astrology: An Integrated Approach", providing
dynamic interpretations for planetary placements, conjunctions, and special states in both the
main Rashi chart and selected Divisional charts.

Core Architecture:
- Main Application Class (`AstroVighatiElite`): Initializes the main window, manages themes, menus, and all the UI tabs.
- Tab Classes (e.g., `KundliGeneratorTab`): Each tab is a self-contained class responsible for its UI and functionality.
- Data Class (`EnhancedAstrologicalData`): Acts as a centralized, static database for astrological information.
- Calculation Engine (`AstronomicalCalculator` & `VargaCalculator`): High-accuracy engine using `pyswisseph` with Lahiri Ayanamsa for all D-chart calculations.
- Interpretation Engine (`InterpretationEngine`): The new analytical core. Contains a rich, context-aware
  knowledge base derived from provided texts to generate dynamic interpretations for various astrological configurations.
- Theming Engine (`EnhancedThemeManager`): Manages the visual styling of the application."""

import importlib
import subprocess
import sys

# A list of required third-party Python packages for the application to run fully.
required_packages = [
    "PIL",
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
    Checks if a given package is installed. If not, it attempts to install it using pip.
    """
    global dependencies_missing
    try:
        # Use a special check for pyswisseph as the import name is 'swisseph'
        import_name = 'swisseph' if package == 'pyswisseph' else package
        importlib.import_module(import_name)
        print(f"✅ {package} is already installed.")
    except ImportError:
        dependencies_missing = True
        print(f"⚙️ Installing missing dependency: {package}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ Successfully installed {package}")

# --- Dependency Check Block ---
print("🚀 Initializing AstroVighati Pro Elite v5.0: Checking dependencies...")
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
    from PIL import Image, ImageTk, ImageDraw, ImageFont
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
    if not isinstance(decimal_degrees, (int, float)): return "N/A"
    is_negative = decimal_degrees < 0
    decimal_degrees = abs(decimal_degrees)
    degrees = int(decimal_degrees)
    minutes_float = (decimal_degrees - degrees) * 60
    minutes = int(minutes_float)
    seconds = int((minutes_float - minutes) * 60)
    sign = "-" if is_negative else ""
    return f"{sign}{degrees:02d}° {minutes:02d}' {seconds:02d}\""

#===================================================================================================
# DATA & INTERPRETATION STORES
#===================================================================================================
class EnhancedAstrologicalData:
    """
    A static class acting as a central repository for all core astrological data,
    including detailed information about planets, nakshatras, rashis, and Varga charts.
    """
    PLANET_COLORS = {
        "Sun": "#FDB813", "Moon": "#C0C0C0", "Mars": "#CD5C5C",
        "Mercury": "#90EE90", "Jupiter": "#FFD700", "Venus": "#FFB6C1",
        "Saturn": "#4169E1", "Rahu": "#8B4513", "Ketu": "#A9A9A9",
        "Ascendant": "#E74C3C"
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
        """
        Returns a dictionary of detailed descriptions for each major Varga chart,
        synthesized from "Vedic Astrology: An Integrated Approach", Chapter 6.
        """
        return {
            "D1 - Rashi": {
                "title": "D1 - Rashi Kundali (Lagna Chart)",
                "description": "The Rashi chart is the foundational birth chart, representing existence at the physical level. It is the 'tree' from which all other 'fruits' (Vargas) grow, showing the totality of your life's potential. All planetary positions, aspects, and yogas in this chart manifest on the physical, tangible plane. The Ascendant (Lagna) is the key, representing your personality, health, and life's path."
            },
            "D2 - Hora": {
                "title": "D2 - Hora Chart (Wealth)",
                "description": "The Hora chart divides each sign into two halves (Horas). This chart is paramount for assessing wealth, financial prosperity, and resources. It reveals your capacity to accumulate and sustain wealth. Planets in the Sun's Hora indicate wealth earned through self-effort and power. Planets in the Moon's Hora suggest wealth accumulated through family or the public."
            },
            "D3 - Drekkana": {
                "title": "D3 - Drekkana Chart (Siblings & Courage)",
                "description": "The Drekkana divides each sign into three parts. It provides deep insights into one's siblings (co-borns), courage, initiative, and personal drive. The 3rd house and its lord in D3 are crucial for younger siblings, while the 11th house relates to elder siblings. Mars, as the natural karaka for siblings and courage, is very important here."
            },
            "D4 - Chaturthamsa": {
                "title": "D4 - Chaturthamsa Chart (Property & Fortune)",
                "description": "This chart (also Turyamsa) divides each sign into four parts. It is analyzed for matters of property, land, homes, vehicles, and one's overall fortune ('Bhagya') related to fixed assets and domestic happiness. The 4th house, its lord, the Moon (home), and Venus (vehicles) are key."
            },
            "D5 - Panchamsa": {
                "title": "D5 - Panchamsa Chart (Fame, Power & Authority)",
                "description": "Divides each sign into five parts. This chart reveals one's creative abilities, past life merits (purva punya), fame, power, authority, and followers. It is a key chart for politicians, artists, and leaders. The strength of the Sun, Jupiter, and the D5 Lagna lord are crucial."
            },
            "D6 - Shashthamsa": {
                "title": "D6 - Shashthamsa Chart (Health & Diseases)",
                "description": "Divides each sign into six parts. It is a critical chart for a microscopic analysis of health, diseases, debts, and conflicts. The 6th house, its lord, and malefics like Saturn and Mars reveal the nature and timing of health struggles. The D6 Lagna represents overall vitality."
            },
            "D7 - Saptamsa": {
                "title": "D7 - Saptamsa Chart (Children & Progeny)",
                "description": "The Saptamsa divides each sign into seven parts. It is the primary chart for all matters related to children, grandchildren, and one's creative legacy. It shows the potential for having children, their well-being, and the relationship with them. Jupiter is the most important planet, and the 5th house (first child), 7th (second), and 9th (third) are analyzed."
            },
            "D9 - Navamsa": {
                "title": "D9 - Navamsa Chart (Spouse, Dharma & Fortune)",
                "description": "Arguably the most important Varga, the Navamsa (nine divisions) is the 'fruit' of the D1 'tree'. Its primary indication is marriage, the spouse, and marital life. Beyond that, it represents one's dharma (righteous path), inner self, skills, and overall fortune, especially in the second half of life. A planet's position here reveals its true inner strength. A planet in the same sign in D1 and D9 is 'Vargottama' and becomes exceptionally powerful."
            },
            "D10 - Dasamsa": {
                "title": "D10 - Dasamsa Chart (Career & Profession)",
                "description": "The Dasamsa (ten divisions) is the microscopic view of the 10th house, representing one's career, profession, status, and achievements in society. The 10th house, its lord, and karakas like the Sun (authority), Mercury (commerce), and Saturn (service) are key. The D10 Lagna shows the environment of one's work."
            },
            "D12 - Dwadasamsa": {
                "title": "D12 - Dwadasamsa Chart (Parents & Lineage)",
                "description": "This chart (twelve divisions) is used to analyze one's parents, grandparents, and ancestral lineage. It shows the karma inherited from one's lineage. The 4th house and Moon relate to the mother, while the 9th house and Sun relate to the father. Afflictions can indicate ancestral curses or inherited health issues."
            },
            "D16 - Shodasamsa": {
                "title": "D16 - Shodasamsa Chart (Vehicles, Comforts & Discomforts)",
                "description": "Also known as Kalamsa, this chart (sixteen divisions) is analyzed for vehicles, luxuries, and general comforts and discomforts. It is a chart of material pleasures. Venus is the natural karaka, and the 4th house in D16 is key. Malefics like Mars or Saturn can indicate accidents or breakdowns."
            },
            "D20 - Vimsamsa": {
                "title": "D20 - Vimsamsa Chart (Spiritual Pursuits)",
                "description": "This chart (twenty divisions) assesses one's spiritual inclinations, religious devotion, worship, and progress on the spiritual path. Jupiter (wisdom) and Ketu (moksha/liberation) are most important. The 9th house in D20 indicates one's spiritual practices and guru."
            },
            "D24 - Siddhamsa": {
                "title": "D24 - Siddhamsa Chart (Education & Knowledge)",
                "description": "The Siddhamsa (twenty-four divisions) is for a detailed analysis of formal education, learning capacity (Vidya), and academic achievements. Mercury (intellect) and Jupiter (knowledge) are key. The 4th house shows formal schooling and the 5th shows intelligence and scholarships."
            },
            "D30 - Trimsamsa": {
                "title": "D30 - Trimsamsa Chart (Misfortunes & Character)",
                "description": "This chart has a unique irregular division system. It is primarily used to analyze evils, misfortunes, punishments, and character weaknesses. It reveals the source of karmic difficulties. Malefics like Saturn and Mars ruling or influencing the D30 Lagna can indicate significant life struggles."
            },
            "D40 - Khavedamsa": {
                "title": "D40 - Khavedamsa Chart (Auspicious/Inauspicious - Maternal)",
                "description": "This chart (forty divisions) is used to determine the specific auspicious and inauspicious karmic effects inherited from the maternal lineage. The Moon's condition is significant. A predominance of benefics in Kendras/Trikonas suggests fortune from the mother's side."
            },
            "D45 - Akshavedamsa": {
                "title": "D45 - Akshavedamsa Chart (Character & Paternal Lineage)",
                "description": "This chart (forty-five divisions) assesses the karmic inheritance from the paternal lineage and its influence on one's general character and moral compass. The Sun's condition is significant. The strength of the D45 Lagna lord indicates the moral fiber of the individual."
            },
            "D60 - Shashtyamsa": {
                "title": "D60 - Shashtyamsa Chart (Past Karma & All Matters)",
                "description": "A highly sensitive and important chart (sixty divisions) that requires a very precise birth time. Sage Parashara gives this chart great weight, stating it reveals the fine print of karma from past lives and is used as a final confirmatory tool for all matters. A good D1 chart can be altered by a bad D60, and vice versa. If the Lagna and planets fall in benefic Shashtyamsas, life will be fortunate."
            }
        }

    # ... (get_all_planets, get_all_nakshatras, get_all_rashis methods remain unchanged) ...
    @staticmethod
    def get_all_planets():
        """Returns a list of dictionaries, each containing detailed information about a Planet (Graha)."""
        return [
            {
                "name": "Sun", "sanskrit": "Surya", "devanagari": "सूर्य", "symbol": "☉",
                "karaka": "Atmakaraka (Soul), Father, King, Authority, Ego, Health, Vitality, Right Eye",
                "dignities": {
                    "Exaltation": "Aries 10°", "Debilitation": "Libra 10°",
                    "Moolatrikona": "Leo 0°-20°", "Own Sign": "Leo"
                },
                "nature": "Malefic", "gender": "Male", "vimshottari_dasha": "6 Years",
                "aspects": "7th house (100%)", "element": "Fire", "caste": "Kshatriya",
                "color": "#FDB813", "day": "Sunday", "gemstone": "Ruby",
                "deity": "Agni/Shiva", "metal": "Gold/Copper", "direction": "East",
                "body_part": "Bones, Right Eye, Heart", "friendly": ["Moon", "Mars", "Jupiter"],
                "neutral": ["Mercury"], "enemy": ["Venus", "Saturn"],
                "significations": ["Government", "Authority", "Father", "Soul", "Power", "Leadership"]
            },
            {
                "name": "Moon", "sanskrit": "Chandra", "devanagari": "चंद्र", "symbol": "☽",
                "karaka": "Manakaraka (Mind), Mother, Emotions, Queen, Popularity, Fluids, Left Eye",
                "dignities": {
                    "Exaltation": "Taurus 3°", "Debilitation": "Scorpio 3°",
                    "Moolatrikona": "Taurus 3°-30°", "Own Sign": "Cancer"
                },
                "nature": "Benefic", "gender": "Female", "vimshottari_dasha": "10 Years",
                "aspects": "7th house (100%)", "element": "Water", "caste": "Vaishya",
                "color": "#C0C0C0", "day": "Monday", "gemstone": "Pearl",
                "deity": "Varuna/Parvati", "metal": "Silver", "direction": "North-West",
                "body_part": "Blood, Left Eye, Mind", "friendly": ["Sun", "Mercury"],
                "neutral": ["Mars", "Jupiter", "Venus", "Saturn"], "enemy": [],
                "significations": ["Mind", "Mother", "Emotions", "Public", "Water", "Comfort"]
            },
            {
                "name": "Mars", "sanskrit": "Mangala", "devanagari": "मंगल", "symbol": "♂",
                "karaka": "Bhratrukaraka (Siblings), Energy, Courage, Conflict, Land, Logic",
                "dignities": {
                    "Exaltation": "Capricorn 28°", "Debilitation": "Cancer 28°",
                    "Moolatrikona": "Aries 0°-12°", "Own Sign": "Aries, Scorpio"
                },
                "nature": "Malefic", "gender": "Male", "vimshottari_dasha": "7 Years",
                "aspects": "4th, 7th, 8th houses", "element": "Fire", "caste": "Kshatriya",
                "color": "#CD5C5C", "day": "Tuesday", "gemstone": "Red Coral",
                "deity": "Kartikeya", "metal": "Copper", "direction": "South",
                "body_part": "Blood, Muscles, Marrow", "friendly": ["Sun", "Moon", "Jupiter"],
                "neutral": ["Venus", "Saturn"], "enemy": ["Mercury"],
                "significations": ["Energy", "Courage", "Siblings", "Property", "Weapons", "Surgery"]
            },
            {
                "name": "Mercury", "sanskrit": "Budha", "devanagari": "बुध", "symbol": "☿",
                "karaka": "Vidyakaraka (Education), Intellect, Communication, Commerce, Logic",
                "dignities": {
                    "Exaltation": "Virgo 15°", "Debilitation": "Pisces 15°",
                    "Moolatrikona": "Virgo 15°-20°", "Own Sign": "Gemini, Virgo"
                },
                "nature": "Neutral", "gender": "Neutral", "vimshottari_dasha": "17 Years",
                "aspects": "7th house (100%)", "element": "Earth", "caste": "Shudra",
                "color": "#90EE90", "day": "Wednesday", "gemstone": "Emerald",
                "deity": "Vishnu", "metal": "Brass", "direction": "North",
                "body_part": "Skin, Nervous System, Speech", "friendly": ["Sun", "Venus"],
                "neutral": ["Mars", "Jupiter", "Saturn"], "enemy": ["Moon"],
                "significations": ["Intelligence", "Communication", "Business", "Education", "Writing"]
            },
            {
                "name": "Jupiter", "sanskrit": "Guru", "devanagari": "गुरु", "symbol": "♃",
                "karaka": "Putrakaraka (Children), Dhanakaraka (Wealth), Wisdom, Teacher",
                "dignities": {
                    "Exaltation": "Cancer 5°", "Debilitation": "Capricorn 5°",
                    "Moolatrikona": "Sagittarius 0°-10°", "Own Sign": "Sagittarius, Pisces"
                },
                "nature": "Most Benefic", "gender": "Male", "vimshottari_dasha": "16 Years",
                "aspects": "5th, 7th, 9th houses", "element": "Ether", "caste": "Brahmin",
                "color": "#FFD700", "day": "Thursday", "gemstone": "Yellow Sapphire",
                "deity": "Indra/Brahma", "metal": "Gold", "direction": "North-East",
                "body_part": "Fat, Liver, Thighs", "friendly": ["Sun", "Moon", "Mars"],
                "neutral": ["Saturn"], "enemy": ["Mercury", "Venus"],
                "significations": ["Wisdom", "Children", "Guru", "Fortune", "Expansion", "Knowledge"]
            },
            {
                "name": "Venus", "sanskrit": "Shukra", "devanagari": "शुक्र", "symbol": "♀",
                "karaka": "Kalatrakaraka (Spouse), Love, Beauty, Arts, Luxury, Vehicles",
                "dignities": {
                    "Exaltation": "Pisces 27°", "Debilitation": "Virgo 27°",
                    "Moolatrikona": "Libra 0°-15°", "Own Sign": "Taurus, Libra"
                },
                "nature": "Benefic", "gender": "Female", "vimshottari_dasha": "20 Years",
                "aspects": "7th house (100%)", "element": "Water", "caste": "Brahmin",
                "color": "#FFB6C1", "day": "Friday", "gemstone": "Diamond",
                "deity": "Lakshmi", "metal": "Silver", "direction": "South-East",
                "body_part": "Reproductive Organs, Face, Eyes", "friendly": ["Mercury", "Saturn"],
                "neutral": ["Mars", "Jupiter"], "enemy": ["Sun", "Moon"],
                "significations": ["Love", "Marriage", "Beauty", "Arts", "Luxury", "Comfort"]
            },
            {
                "name": "Saturn", "sanskrit": "Shani", "devanagari": "शनि", "symbol": "♄",
                "karaka": "Ayu-karaka (Longevity), Karma, Discipline, Sorrow, Delays",
                "dignities": {
                    "Exaltation": "Libra 20°", "Debilitation": "Aries 20°",
                    "Moolatrikona": "Aquarius 0°-20°", "Own Sign": "Capricorn, Aquarius"
                },
                "nature": "Most Malefic", "gender": "Neutral", "vimshottari_dasha": "19 Years",
                "aspects": "3rd, 7th, 10th houses", "element": "Air", "caste": "Shudra",
                "color": "#4169E1", "day": "Saturday", "gemstone": "Blue Sapphire",
                "deity": "Yama", "metal": "Iron", "direction": "West",
                "body_part": "Legs, Knees, Bones", "friendly": ["Mercury", "Venus"],
                "neutral": ["Jupiter"], "enemy": ["Sun", "Moon", "Mars"],
                "significations": ["Karma", "Discipline", "Delays", "Longevity", "Restrictions", "Service"]
            },
            {
                "name": "Rahu", "sanskrit": "Rahu", "devanagari": "राहु", "symbol": "☊",
                "karaka": "Foreign things, Illusion, Obsession, Ambition, Technology",
                "dignities": {
                    "Exaltation": "Taurus/Gemini", "Debilitation": "Scorpio/Sagittarius",
                    "Moolatrikona": "Aquarius", "Own Sign": "Virgo"
                },
                "nature": "Malefic", "gender": "N/A", "vimshottari_dasha": "18 Years",
                "aspects": "5th, 7th, 9th houses", "element": "Air", "caste": "Outcaste",
                "color": "#8B4513", "day": "N/A", "gemstone": "Hessonite",
                "deity": "Durga", "metal": "Lead", "direction": "South-West",
                "body_part": "N/A", "friendly": ["Mercury", "Venus", "Saturn"],
                "neutral": ["Jupiter"], "enemy": ["Sun", "Moon", "Mars"],
                "significations": ["Foreign", "Technology", "Obsession", "Unconventional", "Mystery"]
            },
            {
                "name": "Ketu", "sanskrit": "Ketu", "devanagari": "केतु", "symbol": "☋",
                "karaka": "Mokshakaraka (Liberation), Spirituality, Detachment, Past Karma",
                "dignities": {
                    "Exaltation": "Scorpio/Sagittarius", "Debilitation": "Taurus/Gemini",
                    "Moolatrikona": "Leo", "Own Sign": "Pisces"
                },
                "nature": "Malefic", "gender": "N/A", "vimshottari_dasha": "7 Years",
                "aspects": "5th, 7th, 9th houses", "element": "Fire", "caste": "Outcaste",
                "color": "#A9A9A9", "day": "N/A", "gemstone": "Cat's Eye",
                "deity": "Ganesha", "metal": "Lead", "direction": "N/A",
                "body_part": "N/A", "friendly": ["Sun", "Moon", "Mars"],
                "neutral": ["Jupiter", "Venus", "Saturn", "Mercury"], "enemy": [],
                "significations": ["Moksha", "Spirituality", "Detachment", "Past Life", "Intuition"]
            }
        ]

    @staticmethod
    def get_all_nakshatras():
        """Returns a list of dictionaries, each containing detailed information about a Nakshatra."""
        return [
            {"name": "1. Ashwini", "sanskrit": "Ashwini", "devanagari": "अश्विनी", "lord": "Ketu", "remainder": "1", "deity": "Ashwini Kumaras", "start_degree": 0.0, "end_degree": 13.3333, "padas": ["Aries", "Taurus", "Gemini", "Cancer"]},
            {"name": "2. Bharani", "sanskrit": "Bharani", "devanagari": "भरणी", "lord": "Venus", "remainder": "2", "deity": "Yama", "start_degree": 13.3333, "end_degree": 26.6666, "padas": ["Leo", "Virgo", "Libra", "Scorpio"]},
            {"name": "3. Krittika", "sanskrit": "Krittika", "devanagari": "कृत्तिका", "lord": "Sun", "remainder": "3", "deity": "Agni", "start_degree": 26.6666, "end_degree": 40.0, "padas": ["Sagittarius", "Capricorn", "Aquarius", "Pisces"]},
            {"name": "4. Rohini", "sanskrit": "Rohini", "devanagari": "रोहिणी", "lord": "Moon", "remainder": "4", "deity": "Brahma", "start_degree": 40.0, "end_degree": 53.3333, "padas": ["Aries", "Taurus", "Gemini", "Cancer"]},
            {"name": "5. Mrigashira", "sanskrit": "Mrigashira", "devanagari": "मृगशिरा", "lord": "Mars", "remainder": "5", "deity": "Soma", "start_degree": 53.3333, "end_degree": 66.6666, "padas": ["Leo", "Virgo", "Libra", "Scorpio"]},
            {"name": "6. Ardra", "sanskrit": "Ardra", "devanagari": "आर्द्रा", "lord": "Rahu", "remainder": "6", "deity": "Rudra", "start_degree": 66.6666, "end_degree": 80.0, "padas": ["Sagittarius", "Capricorn", "Aquarius", "Pisces"]},
            {"name": "7. Punarvasu", "sanskrit": "Punarvasu", "devanagari": "पुनर्वसु", "lord": "Jupiter", "remainder": "7", "deity": "Aditi", "start_degree": 80.0, "end_degree": 93.3333, "padas": ["Aries", "Taurus", "Gemini", "Cancer"]},
            {"name": "8. Pushya", "sanskrit": "Pushya", "devanagari": "पुष्य", "lord": "Saturn", "remainder": "8", "deity": "Brihaspati", "start_degree": 93.3333, "end_degree": 106.6666, "padas": ["Leo", "Virgo", "Libra", "Scorpio"]},
            {"name": "9. Ashlesha", "sanskrit": "Ashlesha", "devanagari": "आश्लेषा", "lord": "Mercury", "remainder": "0", "deity": "Nagas", "start_degree": 106.6666, "end_degree": 120.0, "padas": ["Sagittarius", "Capricorn", "Aquarius", "Pisces"]},
            {"name": "10. Magha", "sanskrit": "Magha", "devanagari": "मघा", "lord": "Ketu", "remainder": "1", "deity": "Pitrs", "start_degree": 120.0, "end_degree": 133.3333, "padas": ["Aries", "Taurus", "Gemini", "Cancer"]},
            {"name": "11. Purva Phalguni", "sanskrit": "Purva Phalguni", "devanagari": "पूर्व फाल्गुनी", "lord": "Venus", "remainder": "2", "deity": "Bhaga", "start_degree": 133.3333, "end_degree": 146.6666, "padas": ["Leo", "Virgo", "Libra", "Scorpio"]},
            {"name": "12. Uttara Phalguni", "sanskrit": "Uttara Phalguni", "devanagari": "उत्तर फाल्गुनी", "lord": "Sun", "remainder": "3", "deity": "Aryaman", "start_degree": 146.6666, "end_degree": 160.0, "padas": ["Sagittarius", "Capricorn", "Aquarius", "Pisces"]},
            {"name": "13. Hasta", "sanskrit": "Hasta", "devanagari": "हस्त", "lord": "Moon", "remainder": "4", "deity": "Savitar", "start_degree": 160.0, "end_degree": 173.3333, "padas": ["Aries", "Taurus", "Gemini", "Cancer"]},
            {"name": "14. Chitra", "sanskrit": "Chitra", "devanagari": "चित్రా", "lord": "Mars", "remainder": "5", "deity": "Tvashtar", "start_degree": 173.3333, "end_degree": 186.6666, "padas": ["Leo", "Virgo", "Libra", "Scorpio"]},
            {"name": "15. Swati", "sanskrit": "Swati", "devanagari": "स्वाति", "lord": "Rahu", "remainder": "6", "deity": "Vayu", "start_degree": 186.6666, "end_degree": 200.0, "padas": ["Sagittarius", "Capricorn", "Aquarius", "Pisces"]},
            {"name": "16. Vishakha", "sanskrit": "Vishakha", "devanagari": "विशाखा", "lord": "Jupiter", "remainder": "7", "deity": "Indra-Agni", "start_degree": 200.0, "end_degree": 213.3333, "padas": ["Aries", "Taurus", "Gemini", "Cancer"]},
            {"name": "17. Anuradha", "sanskrit": "Anuradha", "devanagari": "अनुराधा", "lord": "Saturn", "remainder": "8", "deity": "Mitra", "start_degree": 213.3333, "end_degree": 226.6666, "padas": ["Leo", "Virgo", "Libra", "Scorpio"]},
            {"name": "18. Jyestha", "sanskrit": "Jyestha", "devanagari": "ज्येष्ठा", "lord": "Mercury", "remainder": "0", "deity": "Indra", "start_degree": 226.6666, "end_degree": 240.0, "padas": ["Sagittarius", "Capricorn", "Aquarius", "Pisces"]},
            {"name": "19. Mula", "sanskrit": "Mula", "devanagari": "मूल", "lord": "Ketu", "remainder": "1", "deity": "Nirriti", "start_degree": 240.0, "end_degree": 253.3333, "padas": ["Aries", "Taurus", "Gemini", "Cancer"]},
            {"name": "20. Purva Ashadha", "sanskrit": "Purva Ashadha", "devanagari": "पूर्वाषाढ़ा", "lord": "Venus", "remainder": "2", "deity": "Apas", "start_degree": 253.3333, "end_degree": 266.6666, "padas": ["Leo", "Virgo", "Libra", "Scorpio"]},
            {"name": "21. Uttara Ashadha", "sanskrit": "Uttara Ashadha", "devanagari": "उत्तराषाढ़ा", "lord": "Sun", "remainder": "3", "deity": "Vishvadevas", "start_degree": 266.6666, "end_degree": 280.0, "padas": ["Sagittarius", "Capricorn", "Aquarius", "Pisces"]},
            {"name": "22. Shravana", "sanskrit": "Shravana", "devanagari": "श्रवण", "lord": "Moon", "remainder": "4", "deity": "Vishnu", "start_degree": 280.0, "end_degree": 293.3333, "padas": ["Aries", "Taurus", "Gemini", "Cancer"]},
            {"name": "23. Dhanishta", "sanskrit": "Dhanishta", "devanagari": "धनिष्ठा", "lord": "Mars", "remainder": "5", "deity": "Ashta Vasus", "start_degree": 293.3333, "end_degree": 306.6666, "padas": ["Leo", "Virgo", "Libra", "Scorpio"]},
            {"name": "24. Shatabhisha", "sanskrit": "Shatabhisha", "devanagari": "शतभिषा", "lord": "Rahu", "remainder": "6", "deity": "Varuna", "start_degree": 306.6666, "end_degree": 320.0, "padas": ["Sagittarius", "Capricorn", "Aquarius", "Pisces"]},
            {"name": "25. Purva Bhadrapada", "sanskrit": "Purva Bhadrapada", "devanagari": "पूर्व भाद्रपद", "lord": "Jupiter", "remainder": "7", "deity": "Aja Ekapada", "start_degree": 320.0, "end_degree": 333.3333, "padas": ["Aries", "Taurus", "Gemini", "Cancer"]},
            {"name": "26. Uttara Bhadrapada", "sanskrit": "Uttara Bhadrapada", "devanagari": "उत्तर भाद्रपद", "lord": "Saturn", "remainder": "8", "deity": "Ahir Budhnya", "start_degree": 333.3333, "end_degree": 346.6666, "padas": ["Leo", "Virgo", "Libra", "Scorpio"]},
            {"name": "27. Revati", "sanskrit": "Revati", "devanagari": "रेवती", "lord": "Mercury", "remainder": "0", "deity": "Pushan", "start_degree": 346.6666, "end_degree": 360.0, "padas": ["Sagittarius", "Capricorn", "Aquarius", "Pisces"]},
        ]

    @staticmethod
    def get_all_rashis():
        """Returns a list of dictionaries, each containing detailed information about a Rashi (Zodiac Sign)."""
        return [
            {"name": "Aries", "sanskrit": "Mesha", "devanagari": "मेष", "lord": "Mars", "tattva": "Fire", "modality": "Movable", "description": "Represents initiative, courage, and new beginnings."},
            {"name": "Taurus", "sanskrit": "Vrishabha", "devanagari": "वृषभ", "lord": "Venus", "tattva": "Earth", "modality": "Fixed", "description": "Represents stability, material resources, and sensual pleasures."},
            {"name": "Gemini", "sanskrit": "Mithuna", "devanagari": "मिथुन", "lord": "Mercury", "tattva": "Air", "modality": "Dual", "description": "Represents communication, intellect, and duality."},
            {"name": "Cancer", "sanskrit": "Karka", "devanagari": "कर्क", "lord": "Moon", "tattva": "Water", "modality": "Movable", "description": "Represents emotion, nurturing, and the inner world."},
            {"name": "Leo", "sanskrit": "Simha", "devanagari": "सिंह", "lord": "Sun", "tattva": "Fire", "modality": "Fixed", "description": "Represents self-expression, leadership, and creative power."},
            {"name": "Virgo", "sanskrit": "Kanya", "devanagari": "कन्या", "lord": "Mercury", "tattva": "Earth", "modality": "Dual", "description": "Represents service, analysis, and perfection."},
            {"name": "Libra", "sanskrit": "Tula", "devanagari": "तुला", "lord": "Venus", "tattva": "Air", "modality": "Movable", "description": "Represents harmony, relationships, and justice."},
            {"name": "Scorpio", "sanskrit": "Vrischika", "devanagari": "वृश्चिक", "lord": "Mars", "tattva": "Water", "modality": "Fixed", "description": "Represents transformation, intensity, and hidden power."},
            {"name": "Sagittarius", "sanskrit": "Dhanu", "devanagari": "धनु", "lord": "Jupiter", "tattva": "Fire", "modality": "Dual", "description": "Represents wisdom, expansion, and higher truth."},
            {"name": "Capricorn", "sanskrit": "Makara", "devanagari": "मकर", "lord": "Saturn", "tattva": "Earth", "modality": "Movable", "description": "Represents structure, discipline, and achievement."},
            {"name": "Aquarius", "sanskrit": "Kumbha", "devanagari": "कुम्भ", "lord": "Saturn", "tattva": "Air", "modality": "Fixed", "description": "Represents innovation, humanity, and collective ideals."},
            {"name": "Pisces", "sanskrit": "Meena", "devanagari": "मीन", "lord": "Jupiter", "tattva": "Water", "modality": "Dual", "description": "Represents spirituality, dissolution, and universal consciousness."}
        ]

class InterpretationEngine:
    """
    The new analytical core of the application. This class contains a rich database of
    interpretive text derived from "Vedic Astrology: An Integrated Approach" and other
    classical principles. It generates context-aware analysis for planets in signs,
    houses, and divisional charts.
    """

    def __init__(self, app_instance):
        self.app = app_instance

    def get_planet_in_house_analysis(self, planet_name, house_num, varga_num=1):
        """
        Provides a contextual interpretation for a planet in a specific house,
        tailored to the Varga chart being analyzed.
        """
        varga_info = EnhancedAstrologicalData.get_varga_descriptions().get(f"D{varga_num}", {})
        varga_context = varga_info.get("title", "the chart")

        # General house significations from Chapter 7
        house_significations = {
            1: "self, physical body, appearance, overall personality",
            2: "wealth, family, speech, assets",
            3: "courage, younger siblings, communication, short journeys",
            4: "mother, home, properties, happiness, education",
            5: "children, intelligence, creativity, past-life merits (purva punya)",
            6: "enemies, health issues, service, daily work, obstacles",
            7: "spouse, partnerships, business, relationships",
            8: "longevity, hidden matters, inheritance, sudden events, transformation",
            9: "father, guru, fortune, higher knowledge, dharma",
            10: "career, public status, actions in society (karma), achievements",
            11: "gains, income, elder siblings, fulfillment of desires",
            12: "losses, expenses, spirituality, liberation (moksha), foreign lands"
        }
        
        # Mapping Varga to its primary domain
        varga_domain = {
            1: "life in general", 2: "matters of wealth", 3: "siblings and courage", 4: "property and comfort",
            5: "fame and authority", 6: "health and conflicts", 7: "children and creativity", 9: "dharma and marriage",
            10: "career and actions", 12: "parents and lineage", 16: "vehicles and pleasures", 20: "spiritual pursuits",
            24: "education and learning", 30: "misfortunes and character", 60: "past karma"
        }

        domain_text = varga_domain.get(varga_num, "this area of life")
        house_text = house_significations.get(house_num, "an unknown area")

        # Basic planet nature from Chapter 3
        planet_nature = {
            "Sun": "authority, soul, and leadership", "Moon": "emotions, mind, and nurturing",
            "Mars": "energy, action, and conflict", "Mercury": "intellect, communication, and analysis",
            "Jupiter": "wisdom, expansion, and fortune", "Venus": "love, harmony, and luxury",
            "Saturn": "discipline, structure, and karma", "Rahu": "obsession, ambition, and foreign influences",
            "Ketu": "detachment, spirituality, and intuition"
        }
        planet_text = planet_nature.get(planet_name, "its inherent energy")

        return f"In {varga_context}, the placement of **{planet_name}** in the **{house_num}st/nd/rd/th house** influences '{house_text}' within the domain of **{domain_text}**. This indicates that the native's {planet_text} will strongly manifest in these specific matters."

    def get_planet_in_sign_analysis(self, planet_name, sign_name):
        """Provides interpretation for a planet in a specific sign."""
        planet_data = next((p for p in EnhancedAstrologicalData.get_all_planets() if p['name'] == planet_name), {})
        sign_data = next((r for r in EnhancedAstrologicalData.get_all_rashis() if r['name'] == sign_name), {})

        if not planet_data or not sign_data:
            return "Analysis not available."

        planet_element = planet_data.get("element")
        sign_element = sign_data.get("tattva")
        modality = sign_data.get("modality")
        
        harmony = "harmoniously" if planet_element == sign_element else "with some tension, requiring adaptation"

        return f"**{planet_name}** in **{sign_name}**: The {planet_element} nature of {planet_name} interacts with the {sign_element}, {modality} nature of {sign_name}. This placement suggests that the planet's energies will express themselves {harmony}. The native will approach {planet_data.get('significations')[0].lower()} and {planet_data.get('significations')[1].lower()} with the qualities of {sign_data.get('description').lower().replace('represents', '').strip()}"

    def get_special_state_analysis(self, planet_name, speed, sun_longitude, planet_longitude):
        """Checks for and interprets combustion and retrograde states."""
        analysis = []
        # Retrograde Check
        if speed < 0:
            analysis.append(f"**{planet_name} is Retrograde (Vakri)**: This indicates that the planet's energies are turned inward. It may cause delays, introspection, or an unconventional approach to the planet's significations. It often brings karmic matters to the forefront for resolution.")
        
        # Combustion Check (for planets other than Sun)
        if planet_name not in ["Sun", "Rahu", "Ketu"]:
            # A common range for combustion is within 8-15 degrees depending on the planet
            combustion_orb = 8.5 
            if planet_name == "Venus": combustion_orb = 8.0
            if planet_name == "Mercury" and speed > 0: combustion_orb = 14.0
            if planet_name == "Mercury" and speed < 0: combustion_orb = 12.0
            
            separation = abs(planet_longitude - sun_longitude)
            if separation > 180: separation = 360 - separation
            
            if separation <= combustion_orb:
                analysis.append(f"**{planet_name} is Combust (Asta)**: Being very close to the Sun, its significations are 'burnt' or overpowered by the Sun's ego and authority. This can weaken the planet's ability to give independent results, making its expression dependent on the Sun's agenda.")
        
        return "\n".join(analysis) if analysis else ""

    def get_conjunction_analysis(self, planets_in_house):
        """Provides interpretation for planetary conjunctions (more than one planet in a house)."""
        if len(planets_in_house) < 2:
            return ""
        
        planet_names = sorted([p['name'] for p in planets_in_house])
        combo_key = tuple(planet_names)
        
        # A simple knowledge base for common conjunctions
        conjunction_kb = {
            ('Mercury', 'Sun'): "This forms **Budha-Aditya Yoga**, a combination for sharp intellect, communication skills, and success in academic or commercial fields. The person is often learned and respected.",
            ('Mars', 'Saturn'): "A challenging conjunction of two powerful malefics. It can give immense discipline and drive for technical fields but may also bring frustration, accidents, or conflict. It requires careful channeling of energy.",
            ('Jupiter', 'Venus'): "A conjunction of the two Gurus (teachers). It can give great knowledge, wealth, and refinement. However, as they are natural enemies, it can sometimes lead to conflicts in ideology or relationships.",
            ('Moon', 'Saturn'): "This forms **Punarphoo Dosha** or **Vish Yoga** (Poison Yoga). It can cause moodiness, depression, delays, and obstacles. It is a karmic combination that teaches patience and detachment through emotional hardship."
            # More combinations can be added here
        }

        analysis = [f"**Conjunction in this house:** The presence of {', '.join(planet_names)} together creates a powerful fusion of energies."]
        
        # Check for specific known combinations
        for i in range(len(planet_names)):
            for j in range(i + 1, len(planet_names)):
                pair = (planet_names[i], planet_names[j])
                if pair in conjunction_kb:
                    analysis.append(conjunction_kb[pair])
        
        return "\n".join(analysis)

#===================================================================================================
# ASTRONOMICAL & VARGA CALCULATORS
#===================================================================================================
# ... (AstronomicalCalculator and VargaCalculator classes remain unchanged, as they are correct) ...
class AstronomicalCalculator:
    """
    Handles all core astronomical calculations using Swiss Ephemeris with Lahiri Ayanamsa
    to provide precise Sidereal positions for Vedic astrological analysis.
    """
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
            jd_utc = swe.utc_to_jd(dt_utc.year, dt_utc.month, dt_utc.day, dt_utc.hour, dt_utc.minute, dt_utc.second, 1)[1]

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
            # Corrected logic to handle the 360->0 degree transition
            start_deg = nak['start_degree']
            end_deg = nak['end_degree']
            # Handle Revati which crosses the 360/0 boundary
            if start_deg > end_deg:
                if longitude >= start_deg or longitude < end_deg:
                    nakshatra_name = nak['name']
                    break
            else:
                if start_deg <= longitude < end_deg:
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

class VargaCalculator:
    """
    Accurate Varga Chart calculator based on principles from "Vedic Astrology: An Integrated Approach".
    """
    def __init__(self):
        self.D60_DEITIES = ("Ghora","Rakshasa","Deva","Kubera","Yaksha","Kinnara","Bhrashta","Kulaghna","Garala","Vahni","Maya","Puriihaka","Apampathi","Marutwana","Kaala","Sarpa","Amrita","Indu","Mridu","Komala","Heramba","Brahma","Vishnu","Maheshwara","Deva","Ardra","Kalinasa","Kshiteesa","Kamalakara","Gulika","Mrityu","Kaala","Davagni","Ghora","Yama","Kantaka","Sudha","Amrita","Poorna","VishaDagdha","Kulanasa","Vamshakshya","Utpata","Kaala","Saumya","Komala","Seetala","Karaladamshtra","Chandramukhi","Praveena","Kaalpavaka","Dandayudha","Nirmala","Saumya","Kroora","Atisheetala","Amrita","Payodhi","Bhramana","Chandrarekha")

    def calculate_varga_position(self, varga_num, d1_longitude_in_sign, d1_sign_num):
        """Main dispatcher for Varga calculations."""
        lon_in_sign = d1_longitude_in_sign
        sign = d1_sign_num

        if varga_num == 1:
            return sign, lon_in_sign, ""
        elif varga_num == 2: # D2 Hora
            division_size = 15
            amsa = math.floor(lon_in_sign / division_size)
            new_lon = (lon_in_sign % division_size) * 2
            if (EnhancedAstrologicalData.SIGN_NATURE[sign] == 'Odd' and amsa == 0) or \
               (EnhancedAstrologicalData.SIGN_NATURE[sign] == 'Even' and amsa == 1):
                return 5, new_lon, "Sun's Hora" # Leo
            else:
                return 4, new_lon, "Moon's Hora" # Cancer
        elif varga_num == 3: # D3 Drekkana
            division_size = 10
            amsa = math.floor(lon_in_sign / division_size)
            new_lon = (lon_in_sign % division_size) * 3
            offset = [0, 4, 8][amsa]
            new_sign = (sign + offset - 1) % 12 + 1
            return new_sign, new_lon, ""
        elif varga_num == 4: # D4 Chaturthamsa
            division_size = 7.5
            amsa = math.floor(lon_in_sign / division_size)
            new_lon = (lon_in_sign % division_size) * 4
            offset = [0, 3, 6, 9][amsa]
            new_sign = (sign + offset - 1) % 12 + 1
            return new_sign, new_lon, ""
        elif varga_num == 7: # D7 Saptamsa
            division_size = 30 / 7
            amsa = math.floor(lon_in_sign / division_size)
            new_lon = (lon_in_sign % division_size) * 7
            if EnhancedAstrologicalData.SIGN_NATURE[sign] == 'Odd':
                new_sign = (sign + amsa - 1) % 12 + 1
            else:
                new_sign = (sign + 6 + amsa - 1) % 12 + 1
            return new_sign, new_lon, ""
        elif varga_num == 9: # D9 Navamsa
            division_size = 30 / 9
            amsa = math.floor(lon_in_sign / division_size)
            new_lon = (lon_in_sign % division_size) * 9
            rashi_type = (sign - 1) % 4  # 0:Fiery, 1:Earthy, 2:Airy, 3:Watery
            start_sign = [1, 10, 7, 4][rashi_type]
            new_sign = (start_sign + amsa - 1) % 12 + 1
            return new_sign, new_lon, ""
        elif varga_num == 10: # D10 Dasamsa
            division_size = 3
            amsa = math.floor(lon_in_sign / division_size)
            new_lon = (lon_in_sign % division_size) * 10
            if EnhancedAstrologicalData.SIGN_NATURE[sign] == 'Odd':
                new_sign = (sign + amsa - 1) % 12 + 1
            else:
                new_sign = (sign + 8 + amsa - 1) % 12 + 1
            return new_sign, new_lon, ""
        elif varga_num == 12: # D12 Dwadasamsa
            division_size = 2.5
            amsa = math.floor(lon_in_sign / division_size)
            new_lon = (lon_in_sign % division_size) * 12
            new_sign = (sign + amsa - 1) % 12 + 1
            return new_sign, new_lon, ""
        elif varga_num == 16: # D16 Shodasamsa
            division_size = 30 / 16
            amsa = math.floor(lon_in_sign / division_size)
            new_lon = (lon_in_sign % division_size) * 16
            modality_type = (sign - 1) % 3 # 0:Movable, 1:Fixed, 2:Dual
            start_sign = [1, 5, 9][modality_type]
            new_sign = (start_sign + amsa - 1) % 12 + 1
            return new_sign, new_lon, ""
        elif varga_num == 20: # D20 Vimsamsa
            division_size = 1.5
            amsa = math.floor(lon_in_sign / division_size)
            new_lon = (lon_in_sign % division_size) * 20
            modality_type = (sign - 1) % 3
            start_sign = [1, 9, 5][modality_type]
            new_sign = (start_sign + amsa - 1) % 12 + 1
            return new_sign, new_lon, ""
        elif varga_num == 24: # D24 Siddhamsa
            division_size = 1.25
            amsa = math.floor(lon_in_sign / division_size)
            new_lon = (lon_in_sign % division_size) * 24
            start_sign = 5 if EnhancedAstrologicalData.SIGN_NATURE[sign] == 'Odd' else 4
            new_sign = (start_sign + amsa - 1) % 12 + 1
            return new_sign, new_lon, ""
        elif varga_num == 30: # D30 Trimsamsa
            if EnhancedAstrologicalData.SIGN_NATURE[sign] == 'Odd':
                if 0 <= lon_in_sign < 5: new_sign = 1  # Mars
                elif 5 <= lon_in_sign < 10: new_sign = 11 # Saturn
                elif 10 <= lon_in_sign < 18: new_sign = 9 # Jupiter
                elif 18 <= lon_in_sign < 25: new_sign = 3 # Mercury
                else: new_sign = 7 # Venus
            else: # Even
                if 0 <= lon_in_sign < 5: new_sign = 2 # Venus
                elif 5 <= lon_in_sign < 12: new_sign = 6 # Mercury
                elif 12 <= lon_in_sign < 20: new_sign = 12 # Jupiter
                elif 20 <= lon_in_sign < 25: new_sign = 10 # Saturn
                else: new_sign = 8 # Mars
            # Longitude in Trimsamsa is symbolic and not usually calculated.
            return new_sign, 0, ""
        elif varga_num == 60: # D60 Shashtyamsa
            amsa_index = math.floor(d1_longitude_in_sign * 2)
            if amsa_index >= 60: amsa_index = 59
            new_lon = (d1_longitude_in_sign * 2 % 1) * 30
            # Corrected logic: The sign progresses from the D1 sign itself.
            new_sign = ((sign -1 + amsa_index) % 12) + 1
            details = self.D60_DEITIES[amsa_index]
            return new_sign, new_lon, details
        else: # Fallback for other Vargas
            division_size = 30 / varga_num
            amsa = math.floor(lon_in_sign / division_size)
            new_lon = (lon_in_sign % division_size) * varga_num
            new_sign = (sign + amsa - 1) % 12 + 1
            return new_sign, new_lon, ""


#===================================================================================================
# THEME MANAGER
#===================================================================================================
# ... (EnhancedThemeManager class remains unchanged, as it is correct) ...
class EnhancedThemeManager:
    """
    Manages the visual styling of the entire application. It contains a collection of
    pre-defined themes and a powerful `apply_theme` method that configures the style
    of all Tkinter and ttk widgets to match the selected theme. This ensures a
    consistent and professional look and feel.
    """

    THEMES = {
        "Cosmic Dark": {
            "bg_dark": "#0D1B2A", "bg_light": "#E0E1DD", "accent": "#FF6B35",
            "neutral": "#1B263B", "success": "#06FFA5", "chart_bg": "#1B263B"
        },
        "Crimson Mystique": {
            "bg_dark": "#2c3e50", "bg_light": "#ecf0f1", "accent": "#e74c3c",
            "neutral": "#34495e", "success": "#27ae60", "chart_bg": "#34495e"
        },
        "Golden Temple": {
            "bg_dark": "#1A1A1D", "bg_light": "#F5F5F5", "accent": "#C3073F",
            "neutral": "#4E4E50", "success": "#00FFAA", "chart_bg": "#4E4E50"
        },
        "Ocean Depths": {
            "bg_dark": "#001524", "bg_light": "#F8F9FA", "accent": "#15616D",
            "neutral": "#003B46", "success": "#07A8A0", "chart_bg": "#003B46"
        },
        "Royal Purple": {
            "bg_dark": "#1A0033", "bg_light": "#F0F0F0", "accent": "#7209B7",
            "neutral": "#3C096C", "success": "#10F4B1", "chart_bg": "#3C096C"
        },
        "Emerald Forest": {
            "bg_dark": "#011C27", "bg_light": "#F0F2EF", "accent": "#00A878",
            "neutral": "#043948", "success": "#9FFFCB", "chart_bg": "#043948"
        },
        "Sunset Glow": {
            "bg_dark": "#2E0219", "bg_light": "#FFF8F0", "accent": "#F85A3E",
            "neutral": "#5A0834", "success": "#FFD670", "chart_bg": "#5A0834"
        },
        "Mystic Lilac": {
            "bg_dark": "#241E4E", "bg_light": "#E9E3FF", "accent": "#C37DFF",
            "neutral": "#3E3378", "success": "#A6FFD8", "chart_bg": "#3E3378"
        },
        "Obsidian & Gold": {
            "bg_dark": "#0B0B0B", "bg_light": "#EAEAEA", "accent": "#D4AF37",
            "neutral": "#222222", "success": "#B2D9AD", "chart_bg": "#222222"
        },
        "Deep Blue Sea": {
            "bg_dark": "#1A2E40", "bg_light": "#F2F2F2", "accent": "#0D8ABF",
            "neutral": "#264059", "success": "#27ae60", "chart_bg": "#1A2E40"
        },
        "Forest Green": {
            "bg_dark": "#2E4028", "bg_light": "#F2F2F2", "accent": "#59A627",
            "neutral": "#40593A", "success": "#27ae60", "chart_bg": "#2E4028"
        },
        "Classic Dark": {
            "bg_dark": "#262626", "bg_light": "#f5f5f5", "accent": "#00bfff",
            "neutral": "#333333", "success": "#27ae60", "chart_bg": "#262626"
        },
        "Classic Light": {
            "bg_dark": "#f0f0f0", "bg_light": "#1c1c1c", "accent": "#0078d7",
            "neutral": "#dcdcdc", "success": "#27ae60", "chart_bg": "#f0f0f0"
        }
    }

    @staticmethod
    def apply_theme(app, theme_name):
        """
        Applies a full visual theme to the application.
        """
        theme = EnhancedThemeManager.THEMES.get(theme_name, EnhancedThemeManager.THEMES["Cosmic Dark"])
        app.current_theme_data = theme

        style = ttk.Style()
        style.theme_use('clam')

        bg_dark = theme["bg_dark"]
        bg_light = theme["bg_light"]
        accent = theme["accent"]
        neutral = theme["neutral"]

        is_light_theme = theme_name == "Classic Light"
        fg_color = bg_light if not is_light_theme else bg_dark
        main_bg_color = bg_dark if not is_light_theme else bg_light
        widget_bg_color = neutral if not is_light_theme else "#FFFFFF"
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
        style.configure('Vertical.TScrollbar', background=neutral, troughcolor=main_bg_color, arrowcolor=fg_color)
        style.map('Vertical.TScrollbar', background=[('active', accent)])

        try:
            text_bg = widget_bg_color
            text_fg = fg_color
            all_tabs = [
                app.kundli_tab, app.vighati_tab, app.transit_tab,
                app.dasha_tab, app.nakshatra_tab, app.planet_tab,
                app.rashi_tab, app.yoga_tab
            ]
            for tab in all_tabs:
                for widget_name in ['results_text', 'details_text', 'analysis_text', 'info_text', 'transit_text', 'prediction_text', 'dasha_text', 'planet_text', 'rashi_text', 'rajyoga_text', 'dosha_text', 'mahapurusha_text', 'varga_desc_text']:
                    if hasattr(tab, widget_name):
                        widget = getattr(tab, widget_name)
                        widget.config(background=text_bg, foreground=text_fg, insertbackground=accent, selectbackground=accent, selectforeground=select_fg_color)
                for widget_name in ['nak_listbox', 'rashi_listbox', 'planet_listbox']:
                    if hasattr(tab, widget_name):
                        widget = getattr(tab, widget_name)
                        widget.config(background=text_bg, foreground=text_fg, selectbackground=accent, selectforeground=select_fg_color)
        except Exception as e:
            print(f"Warning: Could not apply theme to a specific non-ttk widget. Error: {e}")

#===================================================================================================
# MAIN ELITE APPLICATION
#===================================================================================================
class AstroVighatiElite:
    """
    The main application class. It orchestrates the entire GUI, including the main window,
    menu bar, status bar, and the notebook containing all the feature tabs.
    """

    def __init__(self, root):
        self.root = root
        self.root.title("AstroVighati Pro Elite v5.0 - Advanced Vedic Astrology Suite")
        self.root.geometry("1800x1000")
        self.root.minsize(1400, 800)

        # Instantiate core components
        self.astro_data = EnhancedAstrologicalData()
        self.calculator = AstronomicalCalculator()
        self.varga_calculator = VargaCalculator()
        self.interpreter = InterpretationEngine(self) # New Interpretation Engine

        # Theme Management
        self.current_theme = tk.StringVar(value="Cosmic Dark")
        self.current_theme_data = {}

        # UI Initialization
        self.create_status_bar()
        self.create_main_notebook()
        self.create_tabs()
        self.create_menu()

        EnhancedThemeManager.apply_theme(self, self.current_theme.get())

    # ... (All other methods in AstroVighatiElite class remain unchanged from the previous correct response) ...
    def create_status_bar(self):
        """Creates the status bar at the bottom of the window."""
        self.status_var = tk.StringVar(value="Ready - Elite Edition v5.0 | Sidereal Engine Active")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief='sunken', anchor='w', padding=5)
        status_bar.pack(side='bottom', fill='x')

    def create_main_notebook(self):
        """Creates the main ttk.Notebook widget that will hold all the tabs."""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=(10, 0))

    def create_tabs(self):
        """
        Instantiates and adds all the functional tabs to the main notebook.
        """
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
        """Creates the main application menu bar (File, Theme, Tools, Help)."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File Menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Chart", command=self.new_chart)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Theme Menu
        theme_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Theme", menu=theme_menu)
        for theme_name in EnhancedThemeManager.THEMES.keys():
            theme_menu.add_radiobutton(
                label=theme_name,
                variable=self.current_theme,
                command=lambda t=theme_name: self.change_theme(t)
            )

        # Help Menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="User Guide", command=self.show_help)
        help_menu.add_separator()
        help_menu.add_command(label="About", command=self.show_about)

    def change_theme(self, theme_name):
        """Callback function to change the application's theme."""
        EnhancedThemeManager.apply_theme(self, theme_name)
        self.status_var.set(f"Theme changed to {theme_name}")

    def new_chart(self):
        """Clears the chart and switches to the Kundli tab."""
        self.notebook.select(self.kundli_tab)
        # Here you could add code to clear the input fields in kundli_tab
        messagebox.showinfo("New Chart", "Ready for new birth details.")

    def show_help(self):
        """Displays a user guide in a message box."""
        help_text = """
        AstroVighati Pro Elite v5.0 - User Guide

        KUNDLI & VARGAS:
        - Enter birth details (date, time, location, and timezone offset from UTC).
        - Click 'Generate Kundli' to calculate accurate Sidereal planetary positions.
        - The D1 positions will be displayed.
        - Use the 'Divisional Chart Controls' to select a Varga (e.g., D9) to see its specific calculations.
        - The 'Detailed Analysis' tab will dynamically update to provide interpretations for the selected chart (D1 or Varga).
        - The 'Varga Meanings' tab provides detailed descriptions for each divisional chart.

        OTHER TABS:
        These tabs function as before, providing tools for transits, Dasha periods,
        and exploring detailed astrological data.
        """
        messagebox.showinfo("User Guide", help_text)

    def show_about(self):
        """Displays the 'About' dialog with application information."""
        about_text = """
        AstroVighati Pro Elite v5.0

        Advanced Vedic Astrology Suite
        with Integrated Knowledge Base & Sidereal Engine (Lahiri Ayanamsa)

        Features:
        • Real-time D1 & Varga calculations via Swiss Ephemeris
        • Dynamic, context-aware analysis for D1 and Varga charts
        • Knowledge base derived from "Vedic Astrology: An Integrated Approach"
        • Vighati birth time rectification tool

        © 2024 - Elite Edition
        """
        messagebox.showinfo("About", about_text)


#===================================================================================================
# TAB 1: KUNDLI GENERATOR (& VARGAS) - **REBUILT UI**
#===================================================================================================
class KundliGeneratorTab(ttk.Frame):
    """
    This tab provides the primary functionality of generating a Vedic birth chart (Kundli)
    and its associated Divisional Charts (Vargas). The UI has been redesigned for
    better information hierarchy and to accommodate a new dynamic analysis engine.
    """

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.planet_positions = {}
        self.varga_map = {
            "D1 - Rashi": 1, "D2 - Hora": 2, "D3 - Drekkana": 3, "D4 - Chaturthamsa": 4,
            "D7 - Saptamsa": 7, "D9 - Navamsa": 9, "D10 - Dasamsa": 10, "D12 - Dwadasamsa": 12,
            "D16 - Shodasamsa": 16, "D20 - Vimsamsa": 20, "D24 - Siddhamsa": 24,
            "D30 - Trimsamsa": 30, "D60 - Shashtyamsa": 60
        }

        # Main layout with a PanedWindow
        main_paned = ttk.PanedWindow(self, orient='horizontal')
        main_paned.pack(expand=True, fill='both', padx=10, pady=10)

        # Left panel for user inputs.
        left_panel = ttk.Frame(main_paned, padding=10)
        main_paned.add(left_panel, weight=1)

        # Right panel for displaying results.
        right_panel = ttk.Frame(main_paned, padding=(10, 10, 0, 10))
        main_paned.add(right_panel, weight=3)

        # Build the UI components for each panel.
        self.create_input_panel(left_panel)
        self.create_results_panel(right_panel)

    def create_input_panel(self, parent):
        # ... (This method is functionally the same as before, only layout adjusted) ...
        """Creates the input form for birth name, date, time, and location."""
        birth_frame = ttk.LabelFrame(parent, text="Birth Details", padding=15)
        birth_frame.pack(fill='x', pady=(0, 10))
        birth_frame.grid_columnconfigure(1, weight=1)

        ttk.Label(birth_frame, text="Name:").grid(row=0, column=0, sticky='w', pady=5, padx=5)
        self.name_var = tk.StringVar()
        ttk.Entry(birth_frame, textvariable=self.name_var).grid(row=0, column=1, sticky='ew', pady=5, padx=5)

        ttk.Label(birth_frame, text="Date (DD/MM/YYYY):").grid(row=1, column=0, sticky='w', pady=5, padx=5)
        date_frame = ttk.Frame(birth_frame)
        date_frame.grid(row=1, column=1, sticky='ew', pady=5, padx=5)
        self.day_var = tk.StringVar(value="14")
        self.month_var = tk.StringVar(value="11")
        self.year_var = tk.StringVar(value="2003")
        ttk.Spinbox(date_frame, from_=1, to=31, textvariable=self.day_var, width=5).pack(side='left', fill='x', expand=True)
        ttk.Spinbox(date_frame, from_=1, to=12, textvariable=self.month_var, width=5).pack(side='left', fill='x', expand=True)
        ttk.Spinbox(date_frame, from_=1900, to=2100, textvariable=self.year_var, width=8).pack(side='left', fill='x', expand=True)

        ttk.Label(birth_frame, text="Time (24h format):").grid(row=2, column=0, sticky='w', pady=5, padx=5)
        time_frame = ttk.Frame(birth_frame)
        time_frame.grid(row=2, column=1, sticky='ew', pady=5, padx=5)
        self.hour_var = tk.StringVar(value="19")
        self.minute_var = tk.StringVar(value="41")
        self.second_var = tk.StringVar(value="46")
        ttk.Spinbox(time_frame, from_=0, to=23, textvariable=self.hour_var, width=5, format="%02.0f").pack(side='left', fill='x', expand=True)
        ttk.Spinbox(time_frame, from_=0, to=59, textvariable=self.minute_var, width=5, format="%02.0f").pack(side='left', fill='x', expand=True)
        ttk.Spinbox(time_frame, from_=0, to=59, textvariable=self.second_var, width=5, format="%02.0f").pack(side='left', fill='x', expand=True)

        location_frame = ttk.LabelFrame(parent, text="Location", padding=15)
        location_frame.pack(fill='x', pady=(10, 10))
        location_frame.grid_columnconfigure(1, weight=1)

        ttk.Label(location_frame, text="City:").grid(row=0, column=0, sticky='w', pady=5, padx=5)
        self.city_var = tk.StringVar(value="Ghaziabad")
        ttk.Entry(location_frame, textvariable=self.city_var).grid(row=0, column=1, sticky='ew', pady=5, padx=5)

        ttk.Label(location_frame, text="Latitude:").grid(row=1, column=0, sticky='w', pady=5, padx=5)
        self.lat_var = tk.StringVar(value="28.6692")
        ttk.Entry(location_frame, textvariable=self.lat_var).grid(row=1, column=1, sticky='ew', pady=5, padx=5)

        ttk.Label(location_frame, text="Longitude:").grid(row=2, column=0, sticky='w', pady=5, padx=5)
        self.lon_var = tk.StringVar(value="77.4538")
        ttk.Entry(location_frame, textvariable=self.lon_var).grid(row=2, column=1, sticky='ew', pady=5, padx=5)

        ttk.Label(location_frame, text="Timezone Offset (UTC):").grid(row=3, column=0, sticky='w', pady=5, padx=5)
        self.tz_var = tk.StringVar(value="5.5")
        ttk.Entry(location_frame, textvariable=self.tz_var).grid(row=3, column=1, sticky='ew', pady=5, padx=5)

        ttk.Button(parent, text="🎯 Generate Kundli", command=self.generate_kundli, style='Accent.TButton').pack(fill='x', pady=20, ipady=10)

    def create_results_panel(self, parent):
        """Creates the redesigned results panel with quick info, varga controls, and analysis notebook."""
        # Top section for quick info and varga selection
        top_frame = ttk.Frame(parent)
        top_frame.pack(fill='x', pady=(0, 10))

        # Quick Info Display
        info_frame = ttk.LabelFrame(top_frame, text="Quick Info", padding=10)
        info_frame.pack(side='left', fill='x', expand=True, padx=(0, 10))
        self.info_text = tk.Text(info_frame, height=5, width=40, wrap='word', font=('Segoe UI', 9))
        self.info_text.pack(fill='both', expand=True)
        self.info_text.insert('1.0', "Generate a chart to see quick information...")
        self.info_text.config(state='disabled')

        # Varga Controls
        varga_control_frame = ttk.LabelFrame(top_frame, text="Divisional Chart Controls", padding=10)
        varga_control_frame.pack(side='left', fill='x', expand=True)
        ttk.Label(varga_control_frame, text="Select Chart:").pack(pady=(0, 5))
        self.varga_var = tk.StringVar()
        varga_combo = ttk.Combobox(varga_control_frame, textvariable=self.varga_var,
                                   values=list(self.varga_map.keys()), state="readonly", width=25)
        varga_combo.pack(pady=(0,5))
        varga_combo.set("D1 - Rashi")
        varga_combo.bind("<<ComboboxSelected>>", self.update_all_displays)

        # Main analysis notebook
        self.analysis_notebook = ttk.Notebook(parent)
        self.analysis_notebook.pack(fill='both', expand=True)

        # Tab 1: D1 Planetary Positions Table
        d1_positions_frame = ttk.Frame(self.analysis_notebook, padding=5)
        self.analysis_notebook.add(d1_positions_frame, text="D1 Positions")
        columns = ('planet', 'rashi', 'dms', 'nakshatra', 'lord', 'state')
        self.positions_tree = ttk.Treeview(d1_positions_frame, columns=columns, show='headings')
        self.positions_tree.heading('planet', text='Planet (Graha)')
        self.positions_tree.heading('rashi', text='Rashi')
        self.positions_tree.heading('dms', text='Longitude')
        self.positions_tree.heading('nakshatra', text='Nakshatra')
        self.positions_tree.heading('lord', text='Nak Lord')
        self.positions_tree.heading('state', text='State')
        for col, width in [('planet', 150), ('rashi', 120), ('dms', 100), ('nakshatra', 180), ('lord', 80), ('state', 120)]:
            self.positions_tree.column(col, width=width, anchor='w')
        self.positions_tree.pack(fill='both', expand=True)

        # Tab 2: Varga Planetary Positions Table
        varga_positions_frame = ttk.Frame(self.analysis_notebook, padding=5)
        self.analysis_notebook.add(varga_positions_frame, text="Varga Positions")
        varga_columns = ('planet', 'varga_rashi', 'varga_dms', 'details')
        self.varga_tree = ttk.Treeview(varga_positions_frame, columns=varga_columns, show='headings')
        self.varga_tree.heading('planet', text='Planet')
        self.varga_tree.heading('varga_rashi', text='Varga Rashi')
        self.varga_tree.heading('varga_dms', text='Varga Longitude')
        self.varga_tree.heading('details', text='Details')
        self.varga_tree.pack(fill='both', expand=True)

        # Tab 3: NEW Detailed Analysis
        analysis_frame = ttk.Frame(self.analysis_notebook, padding=5)
        self.analysis_notebook.add(analysis_frame, text="💡 Detailed Analysis")
        self.analysis_text = scrolledtext.ScrolledText(analysis_frame, wrap='word', font=('Segoe UI', 11))
        self.analysis_text.pack(fill='both', expand=True)
        self.analysis_text.config(state='disabled')

        # Tab 4: NEW Varga Meanings
        varga_desc_frame = ttk.Frame(self.analysis_notebook, padding=5)
        self.analysis_notebook.add(varga_desc_frame, text="📖 Varga Meanings")
        self.varga_desc_text = scrolledtext.ScrolledText(varga_desc_frame, wrap='word', font=('Segoe UI', 11))
        self.varga_desc_text.pack(fill='both', expand=True)
        self.populate_varga_descriptions()
        self.varga_desc_text.config(state='disabled')

    def generate_kundli(self):
        """
        Main logic function: gathers input, calls calculation engine, and populates all output widgets.
        """
        try:
            name = self.name_var.get()
            day, month, year = int(self.day_var.get()), int(self.month_var.get()), int(self.year_var.get())
            hour, minute, second = int(self.hour_var.get()), int(self.minute_var.get()), int(self.second_var.get())
            lat, lon = float(self.lat_var.get()), float(self.lon_var.get())
            tz_offset = float(self.tz_var.get())
            city = self.city_var.get()
            self.birth_dt_local = datetime(year, month, day, hour, minute, second)

            self.app.status_var.set("Calculating Sidereal positions (Lahiri)...")
            self.planet_positions = self.app.calculator.calculate_planet_positions(self.birth_dt_local, lat, lon, tz_offset)

            if not self.planet_positions:
                self.app.status_var.set("Calculation failed. Please check inputs and console.")
                return

            self.update_all_displays()
            self.app.status_var.set("Kundli generated successfully!")
            messagebox.showinfo("Success", "Kundli generated successfully using the Sidereal (Lahiri) Engine!")

        except ValueError:
            messagebox.showerror("Input Error", "Please ensure all fields have valid numbers.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate Kundli:\n{str(e)}")
            self.app.status_var.set("Error generating Kundli")

    def update_all_displays(self, event=None):
        """A single function to refresh all display widgets based on current data."""
        if not self.planet_positions:
            return

        self.update_positions_tree()
        self.update_quick_info()
        self.update_varga_positions_display()
        self.update_detailed_analysis()

    def update_positions_tree(self):
        """Populates the D1 planetary positions table."""
        self.positions_tree.delete(*self.positions_tree.get_children())
        planet_order = ["Ascendant", "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
        sun_longitude = self.planet_positions.get('Sun', {}).get('longitude', 0)

        for planet_name in planet_order:
            if planet_name in self.planet_positions:
                pos_data = self.planet_positions[planet_name]
                nak_info = next((n for n in self.app.astro_data.get_all_nakshatras() if n['name'] == pos_data['nakshatra']), {})
                
                # Check for special states
                state = ""
                if pos_data.get('speed', 0) < 0:
                    state += "R "
                
                separation = abs(pos_data['longitude'] - sun_longitude)
                if separation > 180: separation = 360 - separation
                if planet_name not in ["Sun", "Rahu", "Ketu"] and separation < 8.5:
                    state += "C"

                self.positions_tree.insert('', 'end', values=(
                    planet_name, pos_data['rashi'], pos_data['dms'],
                    pos_data['nakshatra'], nak_info.get('lord', 'N/A'), state
                ))

    def update_quick_info(self):
        """Updates the quick info panel."""
        self.info_text.config(state='normal')
        self.info_text.delete('1.0', tk.END)
        info = "═══ QUICK REFERENCE ═══\n\n"
        if 'Ascendant' in self.planet_positions:
            asc_info = self.planet_positions['Ascendant']
            info += f"🔸 Ascendant: {asc_info['rashi']} ({asc_info['dms']})\n"
        if 'Moon' in self.planet_positions:
            moon_info = self.planet_positions['Moon']
            info += f"🌙 Moon Sign: {moon_info['rashi']}\n"
            info += f"⭐ Birth Star: {moon_info['nakshatra']}\n"
        if 'Sun' in self.planet_positions:
            sun_info = self.planet_positions['Sun']
            info += f"☀️ Sun Sign: {sun_info['rashi']}\n"
        self.info_text.insert('1.0', info)
        self.info_text.config(state='disabled')

    def update_varga_positions_display(self):
        """Calculates and displays the selected divisional chart positions."""
        self.varga_tree.delete(*self.varga_tree.get_children())
        selected_varga_key = self.varga_var.get()
        varga_num = self.varga_map[selected_varga_key]

        if varga_num == 1:
             self.varga_tree.insert('', 'end', values=("This is the D1 chart.", "See 'D1 Positions' tab.", "", ""))
             return

        planet_order = ["Ascendant", "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
        for planet_name in planet_order:
            if planet_name in self.planet_positions:
                d1_data = self.planet_positions[planet_name]
                varga_sign_num, varga_lon_dec, details = self.app.varga_calculator.calculate_varga_position(
                    varga_num, d1_data['degree_in_rashi'], EnhancedAstrologicalData.SIGN_NAME_TO_NUM[d1_data['rashi']]
                )
                if varga_sign_num is not None:
                    varga_sign_name = EnhancedAstrologicalData.SIGNS[varga_sign_num]
                    varga_lon_dms = decimal_to_dms(varga_lon_dec)
                    self.varga_tree.insert('', 'end', values=(planet_name, varga_sign_name, varga_lon_dms, details))
    
    def update_detailed_analysis(self):
        """Generates and displays the new, dynamic, multi-layered analysis."""
        self.analysis_text.config(state='normal')
        self.analysis_text.delete('1.0', tk.END)

        selected_varga_key = self.varga_var.get()
        varga_num = self.varga_map[selected_varga_key]

        analysis_str = f"╔═══════ DETAILED ANALYSIS FOR {selected_varga_key.upper()} ═══════╗\n\n"

        # Calculate Varga positions
        varga_positions = {}
        for planet_name, d1_data in self.planet_positions.items():
            varga_sign_num, varga_lon_dec, _ = self.app.varga_calculator.calculate_varga_position(
                varga_num, d1_data['degree_in_rashi'], EnhancedAstrologicalData.SIGN_NAME_TO_NUM[d1_data['rashi']]
            )
            if varga_sign_num:
                varga_positions[planet_name] = {
                    'sign': EnhancedAstrologicalData.SIGNS[varga_sign_num],
                    'house': (varga_sign_num - EnhancedAstrologicalData.SIGN_NAME_TO_NUM[varga_positions.get('Ascendant', {}).get('sign', d1_data['rashi'])] + 12) % 12 + 1 if 'Ascendant' in varga_positions else 0
                }
        
        # Group planets by house for conjunction analysis
        houses = {i: [] for i in range(1, 13)}
        for planet, data in varga_positions.items():
            if data['house'] > 0 and planet != 'Ascendant':
                houses[data['house']].append({'name': planet})


        # Generate analysis for each house
        for house_num in range(1, 13):
            planets_in_house = houses[house_num]
            if planets_in_house:
                analysis_str += f"═══ HOUSE {house_num} ═══\n"
                
                # Conjunction analysis first
                conjunction_analysis = self.app.interpreter.get_conjunction_analysis(planets_in_house)
                if conjunction_analysis:
                    analysis_str += conjunction_analysis + "\n\n"

                # Individual planet analysis
                for planet_data in planets_in_house:
                    planet_name = planet_data['name']
                    # Planet in House analysis
                    analysis_str += self.app.interpreter.get_planet_in_house_analysis(planet_name, house_num, varga_num) + "\n"
                    # Planet in Sign analysis
                    analysis_str += self.app.interpreter.get_planet_in_sign_analysis(planet_name, varga_positions[planet_name]['sign']) + "\n"
                    
                    # Special states from D1 data
                    if varga_num == 1:
                        d1_planet_data = self.planet_positions[planet_name]
                        special_states = self.app.interpreter.get_special_state_analysis(
                            planet_name, d1_planet_data.get('speed', 0),
                            self.planet_positions.get('Sun', {}).get('longitude', 0),
                            d1_planet_data['longitude']
                        )
                        if special_states:
                            analysis_str += special_states + "\n"
                    
                    analysis_str += "─" * 20 + "\n"
                analysis_str += "\n"

        self.analysis_text.insert('1.0', analysis_str)
        self.analysis_text.config(state='disabled')

    def populate_varga_descriptions(self):
        """Fills the Varga Meanings tab with information."""
        self.varga_desc_text.config(state='normal')
        self.varga_desc_text.delete('1.0', tk.END)
        
        all_descs = EnhancedAstrologicalData.get_varga_descriptions()
        full_text = ""
        for key in self.varga_map.keys():
            if key in all_descs:
                desc_data = all_descs[key]
                full_text += f"╔═══════ {desc_data['title'].upper()} ═══════╗\n\n"
                full_text += f"{desc_data['description']}\n\n\n"

        self.varga_desc_text.insert('1.0', full_text)
        self.varga_desc_text.config(state='disabled')

#===================================================================================================
# TAB 2-8: OTHER TABS (Unchanged from previous version for brevity)
#===================================================================================================
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
        ttk.Label(main_frame, text="⚡ VIGHATI BIRTH TIME RECTIFIER", style='Title.TLabel').pack(pady=(0, 20))
        input_frame = ttk.LabelFrame(main_frame, text="Input Parameters", padding=20)
        input_frame.pack(fill='x', pady=(0, 15))
        input_frame.grid_columnconfigure(1, weight=1)
        ttk.Label(input_frame, text="Approximate Birth Time:", style='Heading.TLabel').grid(row=0, column=0, sticky='w', pady=10)
        time_frame = ttk.Frame(input_frame)
        time_frame.grid(row=0, column=1, sticky='ew', padx=20)
        self.hour_var = tk.StringVar(value="12")
        self.minute_var = tk.StringVar(value="0")
        self.second_var = tk.StringVar(value="0")
        ttk.Spinbox(time_frame, from_=0, to=23, textvariable=self.hour_var, width=5, format="%02.0f").pack(side='left', fill='x', expand=True)
        ttk.Spinbox(time_frame, from_=0, to=59, textvariable=self.minute_var, width=5, format="%02.0f").pack(side='left', fill='x', expand=True)
        ttk.Spinbox(time_frame, from_=0, to=59, textvariable=self.second_var, width=5, format="%02.0f").pack(side='left', fill='x', expand=True)
        ttk.Label(input_frame, text="Sunrise Time:", style='Heading.TLabel').grid(row=1, column=0, sticky='w', pady=10)
        sunrise_frame = ttk.Frame(input_frame)
        sunrise_frame.grid(row=1, column=1, sticky='ew', padx=20)
        self.sunrise_hour = tk.StringVar(value="6")
        self.sunrise_min = tk.StringVar(value="0")
        ttk.Spinbox(sunrise_frame, from_=0, to=23, textvariable=self.sunrise_hour, width=5, format="%02.0f").pack(side='left', fill='x', expand=True)
        ttk.Spinbox(sunrise_frame, from_=0, to=59, textvariable=self.sunrise_min, width=5, format="%02.0f").pack(side='left', fill='x', expand=True)
        ttk.Label(input_frame, text="Target Nakshatra:", style='Heading.TLabel').grid(row=2, column=0, sticky='w', pady=10)
        self.nak_var = tk.StringVar()
        nak_values = [f"{n['name']} ({n['devanagari']})" for n in self.nakshatras]
        nak_combo = ttk.Combobox(input_frame, textvariable=self.nak_var, values=nak_values, state='readonly')
        nak_combo.grid(row=2, column=1, sticky='ew', padx=20)
        nak_combo.set(nak_values[0])
        ttk.Label(input_frame, text="Search Range (minutes):", style='Heading.TLabel').grid(row=3, column=0, sticky='w', pady=10)
        range_frame = ttk.Frame(input_frame)
        range_frame.grid(row=3, column=1, sticky='ew', padx=20)
        self.range_var = tk.IntVar(value=30)
        range_scale = ttk.Scale(range_frame, from_=5, to=120, variable=self.range_var, orient='horizontal')
        range_scale.pack(side='left', fill='x', expand=True)
        self.range_label = ttk.Label(range_frame, text="30 min")
        self.range_label.pack(side='left', padx=10)
        self.range_var.trace_add('write', lambda *args: self.range_label.config(text=f"{self.range_var.get()} min"))
        ttk.Button(input_frame, text="🚀 Calculate & Rectify", command=self.calculate, style='Accent.TButton').grid(row=4, column=0, columnspan=2, pady=20, ipadx=30, ipady=10)
        results_frame = ttk.LabelFrame(main_frame, text="Results", padding=10)
        results_frame.pack(fill='both', expand=True)
        self.results_text = scrolledtext.ScrolledText(results_frame, font=('Courier New', 10), wrap='word')
        self.results_text.pack(fill='both', expand=True)
        self.results_text.insert('1.0', "Enter parameters and click Calculate...")
    def calculate(self):
        """
        Performs the Vighati calculation and searches for matching birth times.
        """
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
        results = f"""
╔════════════════════════════════════════════════════════════════════════════════════════╗
║                               VIGHATI RECTIFICATION RESULTS                              ║
╚════════════════════════════════════════════════════════════════════════════════════════╝
Input Parameters:
• Birth Time: {hour:02d}:{minute:02d}:{second:02d}
• Sunrise Time: {sunrise_h:02d}:{sunrise_m:02d}:00
• Target Nakshatra: {target_nak_full} (Expected Remainder: {target_remainder})
• Search Range: ±{search_range} minutes
════════════════════════════════════════════════════════════════════════════════════════
INITIAL CALCULATION:
Time from Sunrise   : {time_diff // 3600:.0f}h {(time_diff % 3600) // 60:.0f}m {time_diff % 60:.0f}s
Vighati Value       : {vighati_value:.2f}
Vighati (Rounded)   : {vighati_rounded}
Computed Remainder  : {computed_remainder}
Match Status        : {'✓ MATCH!' if is_match else '✗ NO MATCH - Searching...'}
════════════════════════════════════════════════════════════════════════════════════════
"""
        matches_found = 0
        if is_match:
            results += "\n🎉 PERFECT MATCH! The given birth time already matches the target Nakshatra.\n"
        else:
            results += "SEARCHING FOR MATCHING TIMES:\n\n"
            results += f"{'Time':<12} | {'Offset':<12} | {'Vighati':<10} | {'Rem':<5} | {'Status':<8}\n"
            results += "-" * 75 + "\n"
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
                    offset_sign, offset_m, offset_s = "+" if offset >= 0 else "-", abs(offset) // 60, abs(offset) % 60
                    offset_str = f"{offset_sign}{offset_m:02d}m{offset_s:02d}s"
                    results += f"{test_h:02d}:{test_m:02d}:{test_s:02d} | {offset_str:<11} | {new_vighati_rounded:>8} | {new_remainder:>3} | ✓ MATCH\n"
                    if matches_found >= 15:
                        results += "\n... (showing first 15 matches only)\n"
                        break
            results += "-" * 75 + "\n"
            results += f"\n📊 SUMMARY: Found {matches_found} matching time(s) within ±{search_range} minutes.\n"
        results += """
════════════════════════════════════════════════════════════════════════════════════════
VIGHATI SYSTEM EXPLANATION:
The Vighati system divides the time from sunrise into 3600 Vighatis (each 24 seconds).
The birth Nakshatra is determined by the formula: Remainder = (Vighati × 4 ÷ 9) mod 9.
This remainder (0-8) corresponds to the repeating sequence of Nakshatra lords.
"""
        self.results_text.insert('1.0', results)
        self.app.status_var.set(f"Vighati calculation complete - Found {matches_found} matches.")

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
        ttk.Button(control_frame, text="🔮 Show General Predictions", command=self.show_predictions).pack(side='left', padx=5, ipady=8)
        results_notebook = ttk.Notebook(main_frame)
        results_notebook.pack(fill='both', expand=True)
        transit_frame = ttk.Frame(results_notebook)
        results_notebook.add(transit_frame, text="Current Positions")
        self.transit_text = scrolledtext.ScrolledText(transit_frame, font=('Courier New', 10), wrap='word')
        self.transit_text.pack(fill='both', expand=True)
        pred_frame = ttk.Frame(results_notebook)
        results_notebook.add(pred_frame, text="Predictions")
        self.prediction_text = scrolledtext.ScrolledText(pred_frame, font=('Segoe UI', 10), wrap='word')
        self.prediction_text.pack(fill='both', expand=True)
        self.transit_text.insert('1.0', "Click 'Show Current Transits' to see real-time planetary positions...")
        self.prediction_text.insert('1.0', "Click 'Show General Predictions' for insights on major transits...")
    def show_current_transits(self):
        now_utc = datetime.utcnow()
        now_local = datetime.now()
        positions = self.app.calculator.calculate_planet_positions(now_utc, 28.6139, 77.2090, 0)
        text = f"""
╔══════════════════════════════════════════════════════════════════╗
║                       CURRENT PLANETARY TRANSITS                     ║
╚══════════════════════════════════════════════════════════════════╝
Date & Time: {now_local.strftime('%d %B %Y, %H:%M:%S')} (Local Time)
Calculated for: Universal Time (UTC)
════════════════════════════════════════════════════════════════════
SIDEREAL POSITIONS (LAHIRI AYANAMSA):
"""
        planet_order = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
        for planet in planet_order:
            if planet in positions:
                data = positions[planet]
                rashi_info = next((r for r in self.app.astro_data.get_all_rashis() if r['name'] == data.get('rashi')), {})
                planet_display = f"{planet} ({next((p.get('devanagari') for p in self.app.astro_data.get_all_planets() if p['name'] == planet), '')})"
                rashi_display = f"{rashi_info.get('name')} ({rashi_info.get('devanagari')})"
                degree = data.get('degree_in_rashi', 0)
                text += f"{planet_display:<20}: {rashi_display:<25} {degree:>6.2f}°\n"
        text += "\n" + "═"*68 + "\n"
        self.transit_text.delete('1.0', tk.END)
        self.transit_text.insert('1.0', text)
        self.app.status_var.set("Current transits calculated successfully")
    def show_predictions(self):
        pred_text = """
╔══════════════════════════════════════════════════════════════════╗
║                   TRANSIT PREDICTIONS (GENERAL)                    ║
╚══════════════════════════════════════════════════════════════════╝
IMPORTANT UPCOMING TRANSITS:
🌟 JUPITER (गुरु) TRANSIT:
   Jupiter's transit generally brings expansion, optimism, and growth. When it
   transits through key houses in your natal chart, expect opportunities.
♄ SATURN (शनि) TRANSIT:
   Saturn's transit demands discipline and patience. The Sade Sati (साढ़े साती)
   period is a particularly significant phase of karmic restructuring.
☊ RAHU-KETU (राहु-केतु) AXIS:
   The nodal axis creates significant karmic shifts. Pay attention to the
   houses they are transiting in your natal chart.
═══════════════════════════════════════════════════════════════════
GENERAL GUIDANCE:
• Monitor slow-moving planets (Saturn, Jupiter, Rahu, Ketu).
• Fast-moving planets (Sun, Moon, etc.) influence mood and short-term events.
• Pay special attention when any planet transits your natal Moon sign (Janma Rashi).
NOTE: These are general predictions. Personalized results require analysis of
your unique birth chart and current Dasha periods.
"""
        self.prediction_text.delete('1.0', tk.END)
        self.prediction_text.insert('1.0', pred_text)

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
        input_frame.grid_columnconfigure(1, weight=1)
        ttk.Label(input_frame, text="Birth Date (for age ref):").grid(row=0, column=0, sticky='w', pady=5)
        self.birth_date_var = tk.StringVar(value="01/01/2000")
        ttk.Entry(input_frame, textvariable=self.birth_date_var, width=20).grid(row=0, column=1, sticky='ew', padx=10)
        ttk.Label(input_frame, text="Moon Nakshatra:").grid(row=1, column=0, sticky='w', pady=5)
        self.moon_nak_var = tk.StringVar()
        nak_values = [f"{n['name']} ({n['devanagari']})" for n in self.app.astro_data.get_all_nakshatras()]
        nak_combo = ttk.Combobox(input_frame, textvariable=self.moon_nak_var, values=nak_values, state='readonly', width=25)
        nak_combo.grid(row=1, column=1, sticky='ew', padx=10)
        nak_combo.set(nak_values[0])
        ttk.Button(input_frame, text="Auto-Fill from Kundli Tab", command=self.autofill_from_kundli).grid(row=2, column=0, pady=10, padx=5, sticky='w')
        ttk.Button(input_frame, text="Calculate Dasha Timeline", command=self.calculate_dasha, style='Accent.TButton').grid(row=2, column=1, pady=15, ipady=8, sticky='e')
        self.dasha_text = scrolledtext.ScrolledText(main_frame, font=('Courier New', 10), wrap='word')
        self.dasha_text.pack(fill='both', expand=True)
        self.dasha_text.insert('1.0', "Enter birth Nakshatra and click 'Calculate'...")
    def autofill_from_kundli(self):
        kundli_tab = self.app.kundli_tab
        if not kundli_tab.planet_positions:
            messagebox.showwarning("No Data", "Please generate a chart in the 'Kundli & Vargas' tab first.")
            return
        try:
            self.birth_date_var.set(f"{kundli_tab.day_var.get()}/{kundli_tab.month_var.get()}/{kundli_tab.year_var.get()}")
            moon_data = kundli_tab.planet_positions.get("Moon")
            if moon_data:
                moon_nak_info = next((n for n in self.app.astro_data.get_all_nakshatras() if n['name'] == moon_data['nakshatra']), None)
                if moon_nak_info:
                    self.moon_nak_var.set(f"{moon_nak_info['name']} ({moon_nak_info['devanagari']})")
                    self.app.status_var.set("Dasha details auto-filled.")
        except Exception as e:
            messagebox.showerror("Auto-Fill Error", f"Could not auto-fill data: {e}")
    def calculate_dasha(self):
        try:
            dasha_periods = {"Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7, "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17}
            planet_order = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
            nak_name_full = self.moon_nak_var.get()
            nak_name_eng = nak_name_full.split(' (')[0]
            birth_date = datetime.strptime(self.birth_date_var.get(), "%d/%m/%Y")
            nak_data = next((n for n in self.app.astro_data.get_all_nakshatras() if n['name'] == nak_name_eng), None)
            if not nak_data: return
            starting_lord = nak_data['lord']
            start_idx = planet_order.index(starting_lord)
            text = f"""
╔══════════════════════════════════════════════════════════════════╗
║                      VIMSHOTTARI DASHA TIMELINE                    ║
╚══════════════════════════════════════════════════════════════════╝
Birth Nakshatra: {nak_name_full}
Starting Mahadasha: {starting_lord}
════════════════════════════════════════════════════════════════════
MAHADASHA SEQUENCE (Major Periods):
"""
            current_date = birth_date
            for i in range(len(planet_order)):
                planet_eng = planet_order[(start_idx + i) % len(planet_order)]
                years = dasha_periods[planet_eng]
                planet_info = next((p for p in self.app.astro_data.get_all_planets() if p['name'] == planet_eng), {})
                planet_display = f"{planet_eng} ({planet_info.get('devanagari')})"
                start_date_str = current_date.strftime('%d-%b-%Y')
                end_date = current_date + timedelta(days=years * 365.25)
                end_date_str = end_date.strftime('%d-%b-%Y')
                text += f"\n{i+1}. {planet_display:<20} Mahadasha ({years} years): {start_date_str} to {end_date_str}\n"
                text += f"   └─ This period emphasizes themes of {self.get_dasha_interpretation(planet_eng)}.\n"
                current_date = end_date
            text += "\n" + "═"*68 + "\nNOTE: This is a simplified timeline. Precise start dates depend on the Moon's exact degree at birth.\n"
            self.dasha_text.delete('1.0', tk.END)
            self.dasha_text.insert('1.0', text)
            self.app.status_var.set("Dasha timeline calculated.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not calculate Dasha: {e}")
    def get_dasha_interpretation(self, planet):
        interpretations = {"Sun": "authority, career, self-expression, and father", "Moon": "emotions, home life, nurturing, and mother", "Mars": "energy, action, conflicts, courage, and property", "Mercury": "learning, communication, business, and intellect", "Jupiter": "wisdom, expansion, wealth, children, and spiritual growth", "Venus": "love, relationships, luxury, arts, and comfort", "Saturn": "discipline, hard work, responsibility, and karmic lessons", "Rahu": "material desires, foreign connections, ambition, and illusion", "Ketu": "spirituality, detachment, intuition, and past karma resolution"}
        return interpretations.get(planet, "transformation")

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
        self.search_var = tk.StringVar()
        self.search_var.trace_add('write', self.filter_nakshatras)
        ttk.Entry(left_panel, textvariable=self.search_var).pack(fill='x', pady=(0, 10))
        self.nak_listbox = tk.Listbox(left_panel, font=('Segoe UI', 11), exportselection=False)
        self.nak_listbox.pack(fill='both', expand=True)
        self.nak_listbox.bind('<<ListboxSelect>>', self.on_select)
        self.populate_list()
        right_panel = ttk.Frame(paned, padding=10)
        paned.add(right_panel, weight=2)
        self.details_text = scrolledtext.ScrolledText(right_panel, font=('Segoe UI', 11), wrap='word')
        self.details_text.pack(fill='both', expand=True)
        self.nak_listbox.selection_set(0)
        self.on_select(None)
    def populate_list(self):
        self.nak_listbox.delete(0, tk.END)
        for nak in self.app.astro_data.get_all_nakshatras():
            self.nak_listbox.insert(tk.END, f"{nak['name']} ({nak['devanagari']})")
    def filter_nakshatras(self, *args):
        search_term = self.search_var.get().lower()
        self.nak_listbox.delete(0, tk.END)
        for nak in self.app.astro_data.get_all_nakshatras():
            if (search_term in nak['name'].lower() or search_term in nak['lord'].lower() or search_term in nak['sanskrit'].lower()):
                self.nak_listbox.insert(tk.END, f"{nak['name']} ({nak['devanagari']})")
    def on_select(self, event):
        selection = self.nak_listbox.curselection()
        if not selection: return
        nak_name_full = self.nak_listbox.get(selection[0])
        nak_name_eng = nak_name_full.split(' (')[0]
        nak_data = next((n for n in self.app.astro_data.get_all_nakshatras() if n['name'] == nak_name_eng), None)
        if nak_data: self.show_details(nak_data)
    def show_details(self, nak):
        self.details_text.delete('1.0', tk.END)
        title = f"{nak['name'].upper()} ({nak['devanagari']})"
        details = f"""
╔══════════════════════════════════════════════════════════════════╗
║  {title.center(62)}  ║
╚══════════════════════════════════════════════════════════════════╝
CORE ATTRIBUTES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Ruling Lord         : {nak['lord']}
Presiding Deity     : {nak.get('deity', 'N/A')}
Symbol              : {nak.get('symbol', 'N/A')}
CLASSIFICATION:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Gana (Temperament)  : {nak.get('gana', 'N/A')}
Guna (Quality)      : {nak.get('guna', 'N/A')}
Tattva (Element)    : {nak.get('tattva', 'N/A')}
Motivation          : {nak.get('motivation', 'N/A')}
PADA (QUARTERS):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Pada 1: {nak['padas'][0]} | Pada 2: {nak['padas'][1]} | Pada 3: {nak['padas'][2]} | Pada 4: {nak['padas'][3]}
"""
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
        ttk.Label(left_panel, text="🪐 NAVAGRAHA (नवग्रह)", style='Heading.TLabel').pack(pady=(0, 10))
        for planet in self.app.astro_data.get_all_planets():
            btn = ttk.Button(left_panel, text=f" {planet['symbol']} {planet['name']} ({planet['devanagari']})", command=lambda p=planet: self.show_planet(p), width=20)
            btn.pack(fill='x', pady=2, ipady=4)
        right_panel = ttk.Frame(paned, padding=10)
        paned.add(right_panel, weight=3)
        self.planet_text = scrolledtext.ScrolledText(right_panel, font=('Segoe UI', 10), wrap='word')
        self.planet_text.pack(fill='both', expand=True)
        self.show_planet(self.app.astro_data.get_all_planets()[0])
    def show_planet(self, planet):
        self.planet_text.delete('1.0', tk.END)
        title = f"{planet['name'].upper()} ({planet['sanskrit']} / {planet['devanagari']}) {planet['symbol']}"
        details = f"""
╔══════════════════════════════════════════════════════════════════╗
║  {title.center(62)}  ║
╚══════════════════════════════════════════════════════════════════╝
KARAKA (SIGNIFICATOR):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{planet['karaka']}
DIGNITIES & STRENGTH:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        for dignity, value in planet['dignities'].items(): details += f"{dignity:<20}: {value}\n"
        details += f"""
BASIC PROPERTIES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Nature              : {planet['nature']}
Vimshottari Dasha   : {planet['vimshottari_dasha']}
RELATIONSHIPS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Friends             : {', '.join(planet['friendly'])}
Neutral             : {', '.join(planet.get('neutral', []))}
Enemies             : {', '.join(planet['enemy'])}
"""
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
        ttk.Label(left_panel, text="♈ ZODIAC SIGNS (राशि)", style='Heading.TLabel').pack(pady=(0, 10))
        self.rashi_listbox = tk.Listbox(left_panel, font=('Segoe UI', 12), exportselection=False)
        self.rashi_listbox.pack(fill='both', expand=True)
        self.rashi_listbox.bind('<<ListboxSelect>>', self.on_select)
        for rashi in self.app.astro_data.get_all_rashis(): self.rashi_listbox.insert(tk.END, f" {rashi['name']} ({rashi['devanagari']})")
        right_panel = ttk.Frame(paned, padding=10)
        paned.add(right_panel, weight=2)
        self.rashi_text = scrolledtext.ScrolledText(right_panel, font=('Segoe UI', 11), wrap='word')
        self.rashi_text.pack(fill='both', expand=True)
        self.rashi_listbox.selection_set(0)
        self.on_select(None)
    def on_select(self, event):
        selection = self.rashi_listbox.curselection()
        if not selection: return
        rashi_name_full = self.rashi_listbox.get(selection[0]).strip()
        rashi_name_eng = rashi_name_full.split(' (')[0]
        rashi_data = next((r for r in self.app.astro_data.get_all_rashis() if r['name'] == rashi_name_eng), None)
        if rashi_data: self.show_details(rashi_data)
    def show_details(self, rashi):
        self.rashi_text.delete('1.0', tk.END)
        title = f"{rashi['name'].upper()} ({rashi['sanskrit']} / {rashi['devanagari']})"
        details = f"""
╔══════════════════════════════════════════════════════════════════╗
║  {title.center(62)}  ║
╚══════════════════════════════════════════════════════════════════╝
CORE ATTRIBUTES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Ruling Lord         : {rashi['lord']}
Element (Tattva)    : {rashi['tattva']}
Modality            : {rashi['modality']}
DESCRIPTION:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{rashi['description']}
"""
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
        self.rajyoga_text.pack(fill='both', expand=True, padx=5, pady=5)
        self.rajyoga_text.insert('1.0', self.get_rajyoga_info())
        dosha_frame = ttk.Frame(notebook)
        notebook.add(dosha_frame, text="Doshas")
        self.dosha_text = scrolledtext.ScrolledText(dosha_frame, font=('Segoe UI', 10), wrap='word')
        self.dosha_text.pack(fill='both', expand=True, padx=5, pady=5)
        self.dosha_text.insert('1.0', self.get_dosha_info())
        mahapurusha_frame = ttk.Frame(notebook)
        notebook.add(mahapurusha_frame, text="Pancha Mahapurusha Yogas")
        self.mahapurusha_text = scrolledtext.ScrolledText(mahapurusha_frame, font=('Segoe UI', 10), wrap='word')
        self.mahapurusha_text.pack(fill='both', expand=True, padx=5, pady=5)
        self.mahapurusha_text.insert('1.0', self.get_mahapurusha_info())
    def get_rajyoga_info(self):
        return """
╔══════════════════════════════════════════════════════════════════╗
║              RAJYOGAS (राजयोग) - ROYAL COMBINATIONS              ║
╚══════════════════════════════════════════════════════════════════╝
1. Gaja Kesari Yoga (गज केसरी योग): Jupiter in a Kendra from the Moon.
2. Dharma-Karmadhipati Yoga: Connection between lords of 9th & 10th houses.
3. Neecha Bhanga Rajyoga (नीच भंग राजयोग): Cancellation of a planet's debilitation.
4. Viparita Rajyoga (विपरीत राजयोग): Lords of 6, 8, 12 in other challenging houses.
"""
    def get_dosha_info(self):
        return """
╔══════════════════════════════════════════════════════════════════╗
║                DOSHAS (दोष) - PLANETARY AFFLICTIONS              ║
╚══════════════════════════════════════════════════════════════════╝
1. Manglik Dosha (मांगलिक दोष): Mars in 1, 2, 4, 7, 8, or 12th house.
2. Kaal Sarpa Dosha (काल सर्प दोष): All planets hemmed between Rahu and Ketu.
3. Pitra Dosha (पितृ दोष): Affliction to the Sun, 9th house, or 9th lord.
4. Grahan Dosha (ग्रहण दोष): Sun or Moon conjunct with Rahu or Ketu.
"""
    def get_mahapurusha_info(self):
        return """
╔══════════════════════════════════════════════════════════════════╗
║            PANCHA MAHAPURUSHA YOGAS (पंच महापुरुष योग)            ║
╚══════════════════════════════════════════════════════════════════╝
1. Ruchaka Yoga (रूचक योग) - Mars: Courageous and commanding.
2. Bhadra Yoga (भद्र योग) - Mercury: Intelligent and articulate.
3. Hamsa Yoga (हंस योग) - Jupiter: Wise and spiritual.
4. Malavya Yoga (मालव्य योग) - Venus: Charming and artistic.
5. Sasa Yoga (शश योग) - Saturn: Disciplined and influential leader.
"""
#===================================================================================================
# MAIN EXECUTION BLOCK
#===================================================================================================
if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = AstroVighatiElite(root)
        welcome_msg = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                     🌟 ASTROVIGHATI PRO ELITE v5.0 🌟                       ║
║                     Advanced Vedic Astrology Suite                           ║
║           (Featuring an Integrated, Research-Based Knowledge Engine)         ║
║                                                                              ║
║     Welcome! The application is now running. Please use the GUI window.      ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
        print(welcome_msg)
        root.mainloop()
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"\n{'='*70}\nA CRITICAL APPLICATION ERROR OCCURRED\n{'='*70}\n{error_details}\n{'='*70}")
        try:
            error_root = tk.Tk()
            error_root.withdraw()
            messagebox.showerror("Critical Application Error", f"A fatal error occurred and the application must close.\n\nError: {str(e)}\n\nPlease check the console for the full traceback.")
        except:
            pass
        