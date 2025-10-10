"""
AstroVighati Pro Elite: Advanced Vedic Astrology Suite
Version: 4.3 with Divisional Charts (Vargas)

Description:
This script creates a comprehensive desktop application for Vedic astrology using Python's Tkinter library.
The application is designed with a modular, tab-based interface, where each tab provides a specific
astrological tool. This version incorporates Devanagari script for key astrological terms and utilizes
a professionally accurate, Sidereal (Lahiri Ayanamsa) calculation engine for both the Natal (D1)
and Divisional (Varga) charts.

Core Architecture:
- Main Application Class (`AstroVighatiElite`): Initializes the main window, manages themes, menus, and all the UI tabs.
- Tab Classes (e.g., `KundliGeneratorTab`, `EnhancedVighatiTab`): Each tab is a self-contained class inheriting
  from `ttk.Frame`, responsible for its own UI layout and functionality.
- Data Class (`EnhancedAstrologicalData`): Acts as a centralized, static database for astrological
  information like planet properties, nakshatras, and rashis, now including Devanagari names.
- Calculation Engine (`AstronomicalCalculator` & `VargaCalculator`): This is the new, highly accurate engine
  transplanted from your proven script. It handles the complex astronomical calculations for planetary positions,
  leveraging the professional-grade Swiss Ephemeris library (`pyswisseph`) with correct timezone handling and
  Lahiri Ayanamsa for both D1 and all subsequent Varga charts.
- Theming Engine (`EnhancedThemeManager`): Manages the visual styling of the application, allowing for
  dynamic theme switching with improved contrast and modern aesthetics.
- Image Generation (`PlanetImageGenerator`): Uses the Pillow library (`PIL`) to programmatically create
  visual elements like planet icons and zodiac wheels, enhancing the user experience.

The application starts by checking for and installing any missing dependencies to ensure a smooth setup.
It then launches the main GUI, ready for user interaction.

Features:
- Real-time astronomical data from Swiss Ephemeris (Sidereal, Lahiri Ayanamsa)
- Natal Chart (D1) and Divisional Chart (Varga) generation (D2, D3, D9, D60, etc.)
- Beautiful planetary visualizations with actual images
- Interactive chart wheels with customizable themes
- Advanced transit calculations and predictions
- Comprehensive Kundli (Birth Chart) generation with Sanskrit/Hindi names
- Dasha timeline visualization
- Yogas and Doshas detection

Requirements:
pip install pillow requests pyswisseph geopy timezonefinder skyfield matplotlib numpy pandas reportlab
"""

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
        # This is more reliable than using pip's internal APIs.
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ Successfully installed {package}")

# --- Dependency Check Block ---
# This block iterates through the list of required packages and ensures each one is installed.
# It provides a user-friendly setup experience.
print("🚀 Initializing AstroVighati Pro Elite: Checking dependencies...")
for pkg in required_packages:
    install_if_missing(pkg)

# If any dependencies were installed, inform the user that a restart might be needed.
# This is because some environments, like VS Code's integrated terminal, may not
# immediately recognize newly installed packages without a reload.
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
# This section attempts to import optional, feature-critical libraries.
# It sets boolean flags to track availability, allowing the application
# to run with reduced functionality if a library is missing, preventing crashes.

# Try importing Pillow (PIL) for image manipulation.
try:
    from PIL import Image, ImageTk, ImageDraw, ImageFont, ImageFilter
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("⚠️ Pillow (PIL) not found. Advanced image features will be disabled.")

# Try importing Requests for network operations.
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("⚠️ Requests not found. Online features will be disabled.")

# Try importing Swiss Ephemeris for high-precision astronomical calculations.
try:
    import swisseph as swe
    SWISSEPH_AVAILABLE = True
    # Set the path to the ephemeris files (optional, but good practice)
    # swe.set_ephe_path(os.path.join(Path.home(), 'sweph/ephe'))
except ImportError:
    SWISSEPH_AVAILABLE = False
    print("⚠️ Swiss Ephemeris (pyswisseph) not found. Calculations will be approximate.")

# Try importing Matplotlib for plotting and charting.
try:
    import matplotlib
    matplotlib.use('TkAgg')  # Set backend for Tkinter compatibility
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("⚠️ Matplotlib not found. Chart visualization will be disabled.")

# Try importing NumPy for numerical operations.
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    print("⚠️ NumPy not found. Advanced numerical calculations will be disabled.")

#===================================================================================================
# HELPER FUNCTIONS (e.g., DMS Conversion)
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
# ENHANCED DATA STORE WITH IMAGES AND EXTENDED INFORMATION
#===================================================================================================
class EnhancedAstrologicalData:
    """
    A static class acting as a central repository for all core astrological data.
    This includes detailed information about planets, nakshatras (lunar mansions),
    rashis (zodiac signs), and now, detailed descriptions for all major Varga charts.
    """

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
        """Returns a dictionary of detailed descriptions for each major Varga chart."""
        return {
            "D1 - Rashi": {
                "title": "D1 - Rashi Kundali (Lagna Chart)",
                "description": "The Rashi chart is the foundational birth chart, the most important of all Vargas. It represents the physical body, the environment you were born into, and the totality of your life's potential.\n\n"
                               "It is the 'tree' from which all other 'fruits' (Vargas) grow. All planetary positions, aspects, and yogas in this chart manifest on the physical, tangible plane. The Ascendant (Lagna) is the key, representing your personality, health, and life's path. The Moon's position determines your mind and emotional well-being (Chandra Lagna)."
            },
            "D2 - Hora": {
                "title": "D2 - Hora Chart (Wealth)",
                "description": "The Hora chart divides each sign into two halves (Horas) of 15 degrees, ruled by the Sun (for masculine energy, authority) and the Moon (for feminine energy, nurturing).\n\n"
                               "**Significance:** This chart is paramount for assessing wealth, financial prosperity, and resources. It reveals your capacity to accumulate and sustain wealth.\n\n"
                               "**Interpretation:** Planets in the Sun's Hora indicate wealth earned through self-effort, power, and authority. Planets in the Moon's Hora suggest wealth accumulated through family, the public, or nourishment. Benefic planets (Jupiter, Venus, Moon, Mercury) in their own Horas are excellent for wealth, while malefics can indicate struggles."
            },
            "D3 - Drekkana": {
                "title": "D3 - Drekkana Chart (Siblings & Courage)",
                "description": "The Drekkana divides each sign into three parts of 10 degrees each. It provides deep insights into one's siblings, courage, initiative, and co-borns.\n\n"
                               "**Significance:** It is the primary chart for analyzing relationships with younger and elder siblings, one's personal drive, motivation, and courage. It also relates to talents and short journeys.\n\n"
                               "**Interpretation:** The 3rd house and its lord in the D3 chart are crucial for younger siblings, while the 11th house and its lord relate to elder siblings. Mars (the natural karaka for siblings and courage) and its placement in D3 are very important. Benefics in the 3rd/11th show harmonious sibling relationships, while malefics can show conflict."
            },
            "D4 - Chaturthamsa": {
                "title": "D4 - Chaturthamsa Chart (Property & Fortune)",
                "description": "This chart divides each sign into four parts of 7.5 degrees. It is also known as the Turyamsa.\n\n"
                               "**Significance:** The D4 chart is analyzed for matters of property, land, homes, vehicles, and one's overall fortune and happiness ('Bhagya'). It relates to one's fixed assets and sense of belonging.\n\n"
                               "**Interpretation:** The 4th house and its lord in the D4 chart are of primary importance. The Moon (karaka for home) and Venus (karaka for vehicles) should be well-placed. A strong D4 Lagna lord promises acquisition of properties. Malefic influences on the 4th house in D4 can indicate disputes or losses related to property."
            },
            "D5 - Panchamsa": {
                "title": "D5 - Panchamsa Chart (Fame, Power & Authority)",
                "description": "The Panchamsa chart divides each sign into five parts of 6 degrees each.\n\n"
                               "**Significance:** This chart reveals one's creative abilities, intelligence, past life merits (purva punya), fame, power, and followers. It is a key chart for politicians, artists, and leaders.\n\n"
                               "**Interpretation:** The strength of the Sun, Jupiter, and Venus in the D5 chart is crucial. The Lagna lord of D5 and its placement show one's innate creative intelligence. The 5th house of the D5 chart relates to followers and fame. Strong planets in Kendras or Trikonas in D5 can bestow significant authority and recognition."
            },
            "D6 - Shashthamsa": {
                "title": "D6 - Shashthamsa Chart (Health & Diseases)",
                "description": "This chart divides each sign into six parts of 5 degrees each. It is a critical chart for medical astrology.\n\n"
                               "**Significance:** The D6 is used for a microscopic analysis of health, diseases, debts, and conflicts. It can indicate the timing of illnesses and the parts of the body that are vulnerable.\n\n"
                               "**Interpretation:** The 6th house and its lord in the D6 chart are key indicators of disease. Saturn and Mars, being primary malefics, can cause significant health issues if they afflict the Lagna or other sensitive points in this chart. The Lagna of D6 represents overall vitality. A weak or afflicted D6 Lagna can indicate a life prone to health struggles."
            },
            "D7 - Saptamsa": {
                "title": "D7 - Saptamsa Chart (Children & Progeny)",
                "description": "The Saptamsa chart divides each sign into seven parts of approximately 4.28 degrees. It is the primary chart for all matters related to children.\n\n"
                               "**Significance:** It governs progeny, grandchildren, creative legacy, and the happiness one derives from them. It shows the potential for having children, their well-being, and one's relationship with them.\n\n"
                               "**Interpretation:** Jupiter (the natural karaka for children) is the most important planet in this chart. The 5th house (for the first child), 7th (for the second), and 9th (for the third) in the D7 chart are analyzed. A strong D7 Lagna and a well-placed Jupiter indicate happiness from children."
            },
            "D9 - Navamsa": {
                "title": "D9 - Navamsa Chart (Spouse, Dharma & Fortune)",
                "description": "The Navamsa is arguably the most important divisional chart after the D1 Rashi chart. It divides each sign into nine parts of 3°20' each. It is often called the 'fruit' of the D1 'tree'.\n\n"
                               "**Significance:** Its primary indication is marriage, the spouse, and marital life. Beyond that, it represents one's dharma (righteous path), inner talents, skills, and overall fortune in the second half of life.\n\n"
                               "**Interpretation:** A planet's position in the Navamsa chart reveals its true inner strength. A planet that is exalted or in its own sign in both D1 and D9 is called 'Vargottama' and becomes exceptionally powerful. The 7th house and its lord in D9 describe the spouse and marriage quality. The Lagna of D9 shows one's inner self and spiritual path."
            },
            "D10 - Dasamsa": {
                "title": "D10 - Dasamsa Chart (Career & Profession)",
                "description": "The Dasamsa divides each sign into ten parts of 3 degrees each. It is the microscopic view of the 10th house of the Rashi chart.\n\n"
                               "**Significance:** This is the primary chart for analyzing career, profession, achievements, status in society, and karma (actions).\n\n"
                               "**Interpretation:** The 10th house and its lord in the D10 chart are paramount. The Sun (authority), Mercury (commerce), Jupiter (wisdom), and Saturn (service) are key planets. The D10 Lagna lord's placement shows the environment of one's work, and its strength indicates one's influence and success. Planets in the 10th house of D10 strongly influence the nature of one's profession."
            },
            "D12 - Dwadasamsa": {
                "title": "D12 - Dwadasamsa Chart (Parents & Lineage)",
                "description": "The Dwadasamsa divides each sign into twelve parts of 2.5 degrees each.\n\n"
                               "**Significance:** This chart is used to analyze one's parents, grandparents, and ancestral lineage (Pitra). It shows the karma inherited from one's lineage and the relationship one has with their parents.\n\n"
                               "**Interpretation:** The Sun is the karaka for the father, and the Moon is the karaka for the mother. Their condition in the D12 chart is crucial. The 4th house and its lord in D12 represent the mother, while the 9th house and its lord represent the father. Afflictions in this chart can indicate ancestral curses or health issues inherited from parents."
            },
            "D16 - Shodasamsa": {
                "title": "D16 - Shodasamsa Chart (Vehicles, Comforts & Discomforts)",
                "description": "This chart divides each sign into sixteen parts of 1°52'30\" each.\n\n"
                               "**Significance:** It is analyzed for gains and losses related to vehicles, luxuries, and general comforts and discomforts in life. It is a chart of material pleasures and the happiness or sorrow derived from them.\n\n"
                               "**Interpretation:** Venus is the natural karaka for vehicles and luxury. The 4th house and its lord in the D16 chart are also key. Benefic influences promise comfortable vehicles and luxuries. Malefic influences, especially from Mars (accidents) or Saturn (breakdowns), can indicate troubles related to vehicles."
            },
            "D20 - Vimsamsa": {
                "title": "D20 - Vimsamsa Chart (Spiritual Pursuits)",
                "description": "The Vimsamsa divides each sign into twenty parts of 1.5 degrees each.\n\n"
                               "**Significance:** This is a key chart for assessing one's spiritual inclinations, religious devotion, worship, and progress on the spiritual path. It shows one's connection to the divine.\n\n"
                               "**Interpretation:** Jupiter (karaka for wisdom) and Ketu (karaka for moksha/liberation) are the most important planets. The 9th house and its lord in the D20 chart indicate one's spiritual practices and guru. A strong D20 Lagna with benefic influences suggests a genuinely spiritual person."
            },
            "D24 - Siddhamsa": {
                "title": "D24 - Siddhamsa Chart (Education & Knowledge)",
                "description": "The Siddhamsa divides each sign into twenty-four parts of 1°15' each.\n\n"
                               "**Significance:** This chart is used for a detailed analysis of one's formal education, learning capacity, knowledge (Vidya), and academic achievements.\n\n"
                               "**Interpretation:** Mercury (karaka for intellect) and Jupiter (karaka for knowledge) are key planets. The 5th house and its lord in the D24 chart show one's intelligence and learning ability, while the 4th house shows formal schooling. Strong planets in these houses promise high academic success."
            },
            "D30 - Trimsamsa": {
                "title": "D30 - Trimsamsa Chart (Misfortunes & Character)",
                "description": "The Trimsamsa has a unique division system. It is primarily used to analyze evils, misfortunes, punishments, and the inner character and weaknesses of a person. It is a key chart for predicting evils and is especially important for female horoscopy.\n\n"
                               "**Significance:** It reveals the source of troubles in one's life, be it health, character flaws, or external enemies. It is a chart of karmic difficulties.\n\n"
                               "**Interpretation:** Only the five non-luminary planets (Mars, Mercury, Jupiter, Venus, Saturn) rule the Trimsamsas. Saturn and Mars ruling the Lagna Trimsamsa can indicate significant life struggles and health issues. The nature of the planet ruling the Lagna Trimsamsa reveals a lot about the native's subconscious weaknesses."
            },
            "D40 - Khavedamsa": {
                "title": "D40 - Khavedamsa Chart (Auspicious & Inauspicious Effects)",
                "description": "The Khavedamsa divides each sign into forty parts. This chart is used to determine the specific auspicious and inauspicious effects inherited from the maternal lineage.\n\n"
                               "**Significance:** It provides a general overview of the quality of life, distinguishing between generally fortunate and unfortunate nativities. It's a subtle chart that fine-tunes the promises seen in the D1 chart, specifically from the mother's side.\n\n"
                               "**Interpretation:** The Moon, as the karaka for the mother, is significant. The placement of benefics versus malefics in Kendras and Trikonas gives a quick assessment. A predominance of benefics suggests a life of general ease and fortune inherited from the mother's family."
            },
            "D45 - Akshavedamsa": {
                "title": "D45 - Akshavedamsa Chart (General Character & Paternal Lineage)",
                "description": "The Akshavedamsa divides each sign into forty-five parts. It is used to assess all matters related to character and conduct, and the specific auspicious and inauspicious effects inherited from the paternal lineage.\n\n"
                               "**Significance:** Similar to the D40 for the maternal side, the D45 focuses on the karma and blessings/curses coming from the father's side. It offers deep insights into one's innate character and moral compass.\n\n"
                               "**Interpretation:** The Sun, as the karaka for the father, is significant. The general disposition of planets (benefic/malefic) and the strength of the D45 Lagna lord indicate the moral fiber of the individual and the karmic inheritance from the father's lineage."
            },
            "D60 - Shashtyamsa": {
                "title": "D60 - Shashtyamsa Chart (Past Karma & All Matters)",
                "description": "The Shashtyamsa is a highly sensitive and important chart, dividing each sign into sixty parts of 30 minutes each. Each division has a specific deity and nature (benefic or malefic).\n\n"
                               "**Significance:** Sage Parashara gives this chart a weight almost equal to the D1 Rashi chart. It is said to reveal the fine print of karma from past lives and is used as a final confirmatory tool for all matters. A good D1 chart can be ruined by a bad D60, and vice versa.\n\n"
                               "**Interpretation:** This chart requires a very precise birth time. The interpretation is based on the nature of the Shashtyamsa in which a planet falls. If the Lagna and most planets fall in benefic Shashtyamsas ruled by gentle deities, the life will be fortunate despite challenges in the D1. If they fall in cruel Shashtyamsas, life can be full of struggle even if the D1 looks good."
            }
        }

    @staticmethod
    def get_all_nakshatras():
        # ... (This method is complete and correct) ...
        """Returns a list of dictionaries, each containing detailed information about a Nakshatra."""
        return [
            {"name": "1. Ashwini", "sanskrit": "Ashwini", "devanagari": "अश्विनी", "lord": "Ketu", "remainder": "1", "deity": "Ashwini Kumaras",
             "gana": "Deva", "guna": "Sattva", "tattva": "Fire", "start_degree": 0.0, "end_degree": 13.3333,
             "padas": ["Aries", "Taurus", "Gemini", "Cancer"], "motivation": "Dharma",
             "nature": "Movable", "keywords": "Swift, Healing, Pioneering",
             "symbol": "Horse's Head", "animal": "Male Horse", "tree": "Poison Nut Tree"},
            {"name": "2. Bharani", "sanskrit": "Bharani", "devanagari": "भरणी", "lord": "Venus", "remainder": "2", "deity": "Yama",
             "gana": "Manushya", "guna": "Rajas", "tattva": "Earth", "start_degree": 13.3333, "end_degree": 26.6666,
             "padas": ["Leo", "Virgo", "Libra", "Scorpio"], "motivation": "Artha",
             "nature": "Fierce", "keywords": "Bearer, Transformative, Creative",
             "symbol": "Yoni", "animal": "Elephant", "tree": "Amla Tree"},
            {"name": "3. Krittika", "sanskrit": "Krittika", "devanagari": "कृत्तिका", "lord": "Sun", "remainder": "3", "deity": "Agni",
             "gana": "Rakshasa", "guna": "Rajas", "tattva": "Fire", "start_degree": 26.6666, "end_degree": 40.0,
             "padas": ["Sagittarius", "Capricorn", "Aquarius", "Pisces"], "motivation": "Kama",
             "nature": "Mixed", "keywords": "The Cutter, Purifying, Sharp",
             "symbol": "Razor/Axe", "animal": "Female Sheep", "tree": "Fig Tree"},
            {"name": "4. Rohini", "sanskrit": "Rohini", "devanagari": "रोहिणी", "lord": "Moon", "remainder": "4", "deity": "Brahma",
             "gana": "Manushya", "guna": "Rajas", "tattva": "Earth", "start_degree": 40.0, "end_degree": 53.3333,
             "padas": ["Aries", "Taurus", "Gemini", "Cancer"], "motivation": "Moksha",
             "nature": "Fixed", "keywords": "The Beloved, Fertile, Growing",
             "symbol": "Chariot", "animal": "Male Serpent", "tree": "Jamun Tree"},
            {"name": "5. Mrigashira", "sanskrit": "Mrigashira", "devanagari": "मृगशिरा", "lord": "Mars", "remainder": "5", "deity": "Soma",
             "gana": "Deva", "guna": "Tamas", "tattva": "Air", "start_degree": 53.3333, "end_degree": 66.6666,
             "padas": ["Leo", "Virgo", "Libra", "Scorpio"], "motivation": "Moksha",
             "nature": "Soft", "keywords": "The Searcher, Curious, Restless",
             "symbol": "Deer's Head", "animal": "Female Serpent", "tree": "Khadira Tree"},
            {"name": "6. Ardra", "sanskrit": "Ardra", "devanagari": "आर्द्रा", "lord": "Rahu", "remainder": "6", "deity": "Rudra",
             "gana": "Manushya", "guna": "Tamas", "tattva": "Water", "start_degree": 66.6666, "end_degree": 80.0,
             "padas": ["Sagittarius", "Capricorn", "Aquarius", "Pisces"], "motivation": "Kama",
             "nature": "Sharp", "keywords": "The Moist One, Intense, Transformative",
             "symbol": "Teardrop/Diamond", "animal": "Female Dog", "tree": "Krishna Kamal"},
            {"name": "7. Punarvasu", "sanskrit": "Punarvasu", "devanagari": "पुनर्वसु", "lord": "Jupiter", "remainder": "7", "deity": "Aditi",
             "gana": "Deva", "guna": "Sattva", "tattva": "Air", "start_degree": 80.0, "end_degree": 93.3333,
             "padas": ["Aries", "Taurus", "Gemini", "Cancer"], "motivation": "Artha",
             "nature": "Movable", "keywords": "The Returner, Hopeful, Nurturing",
             "symbol": "Quiver of Arrows", "animal": "Female Cat", "tree": "Bamboo"},
            {"name": "8. Pushya", "sanskrit": "Pushya", "devanagari": "पुष्य", "lord": "Saturn", "remainder": "8", "deity": "Brihaspati",
             "gana": "Deva", "guna": "Sattva", "tattva": "Water", "start_degree": 93.3333, "end_degree": 106.6666,
             "padas": ["Leo", "Virgo", "Libra", "Scorpio"], "motivation": "Dharma",
             "nature": "Light", "keywords": "The Nourisher, Auspicious, Protective",
             "symbol": "Cow's Udder", "animal": "Male Goat", "tree": "Peepal Tree"},
            {"name": "9. Ashlesha", "sanskrit": "Ashlesha", "devanagari": "आश्लेषा", "lord": "Mercury", "remainder": "0", "deity": "Nagas",
             "gana": "Rakshasa", "guna": "Sattva", "tattva": "Water", "start_degree": 106.6666, "end_degree": 120.0,
             "padas": ["Sagittarius", "Capricorn", "Aquarius", "Pisces"], "motivation": "Dharma",
             "nature": "Sharp", "keywords": "The Serpent, Mystical, Cunning",
             "symbol": "Coiled Serpent", "animal": "Male Cat", "tree": "Nag Kesar"},
            {"name": "10. Magha", "sanskrit": "Magha", "devanagari": "मघा", "lord": "Ketu", "remainder": "1", "deity": "Pitrs",
             "gana": "Rakshasa", "guna": "Tamas", "tattva": "Fire", "start_degree": 120.0, "end_degree": 133.3333,
             "padas": ["Aries", "Taurus", "Gemini", "Cancer"], "motivation": "Artha",
             "nature": "Fixed", "keywords": "Royal, Ancestral, Authoritative",
             "symbol": "Throne", "animal": "Male Rat", "tree": "Banyan Tree"},
            {"name": "11. Purva Phalguni", "sanskrit": "Purva Phalguni", "devanagari": "पूर्व फाल्गुनी", "lord": "Venus", "remainder": "2", "deity": "Bhaga",
             "gana": "Manushya", "guna": "Rajas", "tattva": "Water", "start_degree": 133.3333, "end_degree": 146.6666,
             "padas": ["Leo", "Virgo", "Libra", "Scorpio"], "motivation": "Kama",
             "nature": "Fierce", "keywords": "Pleasure-loving, Creative, Social",
             "symbol": "Front Legs of Bed", "animal": "Female Rat", "tree": "Palash Tree"},
            {"name": "12. Uttara Phalguni", "sanskrit": "Uttara Phalguni", "devanagari": "उत्तर फाल्गुनी", "lord": "Sun", "remainder": "3", "deity": "Aryaman",
             "gana": "Manushya", "guna": "Rajas", "tattva": "Earth", "start_degree": 146.6666, "end_degree": 160.0,
             "padas": ["Sagittarius", "Capricorn", "Aquarius", "Pisces"], "motivation": "Moksha",
             "nature": "Fixed", "keywords": "Generous, Helpful, Committed",
             "symbol": "Back Legs of Bed", "animal": "Male Bull", "tree": "Peepal Tree"},
            {"name": "13. Hasta", "sanskrit": "Hasta", "devanagari": "हस्त", "lord": "Moon", "remainder": "4", "deity": "Savitar",
             "gana": "Deva", "guna": "Rajas", "tattva": "Earth", "start_degree": 160.0, "end_degree": 173.3333,
             "padas": ["Aries", "Taurus", "Gemini", "Cancer"], "motivation": "Moksha",
             "nature": "Light", "keywords": "The Hand, Skillful, Clever",
             "symbol": "Hand/Palm", "animal": "Female Buffalo", "tree": "Jasmine"},
            {"name": "14. Chitra", "sanskrit": "Chitra", "devanagari": "चित్రా", "lord": "Mars", "remainder": "5", "deity": "Tvashtar",
             "gana": "Rakshasa", "guna": "Tamas", "tattva": "Air", "start_degree": 173.3333, "end_degree": 186.6666,
             "padas": ["Leo", "Virgo", "Libra", "Scorpio"], "motivation": "Kama",
             "nature": "Soft", "keywords": "The Bright One, Artistic, Magical",
             "symbol": "Bright Jewel/Pearl", "animal": "Female Tiger", "tree": "Bael Tree"},
            {"name": "15. Swati", "sanskrit": "Swati", "devanagari": "स्वाति", "lord": "Rahu", "remainder": "6", "deity": "Vayu",
             "gana": "Deva", "guna": "Tamas", "tattva": "Air", "start_degree": 186.6666, "end_degree": 200.0,
             "padas": ["Sagittarius", "Capricorn", "Aquarius", "Pisces"], "motivation": "Artha",
             "nature": "Movable", "keywords": "The Sword, Independent, Flexible",
             "symbol": "Young Sprout", "animal": "Male Buffalo", "tree": "Arjun Tree"},
            {"name": "16. Vishakha", "sanskrit": "Vishakha", "devanagari": "विशाखा", "lord": "Jupiter", "remainder": "7", "deity": "Indra-Agni",
             "gana": "Rakshasa", "guna": "Tamas", "tattva": "Fire", "start_degree": 200.0, "end_degree": 213.3333,
             "padas": ["Aries", "Taurus", "Gemini", "Cancer"], "motivation": "Dharma",
             "nature": "Mixed", "keywords": "The Forked Branch, Determined",
             "symbol": "Archway", "animal": "Male Tiger", "tree": "Wood Apple"},
            {"name": "17. Anuradha", "sanskrit": "Anuradha", "devanagari": "अनुराधा", "lord": "Saturn", "remainder": "8", "deity": "Mitra",
             "gana": "Deva", "guna": "Sattva", "tattva": "Fire", "start_degree": 213.3333, "end_degree": 226.6666,
             "padas": ["Leo", "Virgo", "Libra", "Scorpio"], "motivation": "Dharma",
             "nature": "Soft", "keywords": "The Follower, Devoted, Friendly",
             "symbol": "Lotus", "animal": "Female Deer", "tree": "Nagkesar"},
            {"name": "18. Jyestha", "sanskrit": "Jyestha", "devanagari": "ज्येष्ठा", "lord": "Mercury", "remainder": "0", "deity": "Indra",
             "gana": "Rakshasa", "guna": "Sattva", "tattva": "Air", "start_degree": 226.6666, "end_degree": 240.0,
             "padas": ["Sagittarius", "Capricorn", "Aquarius", "Pisces"], "motivation": "Artha",
             "nature": "Sharp", "keywords": "The Eldest, Protective, Responsible",
             "symbol": "Earring/Umbrella", "animal": "Male Deer", "tree": "Shalmali"},
            {"name": "19. Mula", "sanskrit": "Mula", "devanagari": "मूल", "lord": "Ketu", "remainder": "1", "deity": "Nirriti",
             "gana": "Rakshasa", "guna": "Tamas", "tattva": "Air", "start_degree": 240.0, "end_degree": 253.3333,
             "padas": ["Aries", "Taurus", "Gemini", "Cancer"], "motivation": "Kama",
             "nature": "Sharp", "keywords": "The Root, Investigative, Destructive",
             "symbol": "Bunch of Roots", "animal": "Male Dog", "tree": "Sarjaka"},
            {"name": "20. Purva Ashadha", "sanskrit": "Purva Ashadha", "devanagari": "पूर्वाषाढ़ा", "lord": "Venus", "remainder": "2", "deity": "Apas",
             "gana": "Manushya", "guna": "Rajas", "tattva": "Fire", "start_degree": 253.3333, "end_degree": 266.6666,
             "padas": ["Leo", "Virgo", "Libra", "Scorpio"], "motivation": "Moksha",
             "nature": "Fierce", "keywords": "Victorious, Purifying, Invincible",
             "symbol": "Elephant's Tusk", "animal": "Male Monkey", "tree": "Ashoka"},
            {"name": "21. Uttara Ashadha", "sanskrit": "Uttara Ashadha", "devanagari": "उत्तराषाढ़ा", "lord": "Sun", "remainder": "3", "deity": "Vishvadevas",
             "gana": "Manushya", "guna": "Rajas", "tattva": "Earth", "start_degree": 266.6666, "end_degree": 280.0,
             "padas": ["Sagittarius", "Capricorn", "Aquarius", "Pisces"], "motivation": "Moksha",
             "nature": "Fixed", "keywords": "Permanent Victory, Virtuous",
             "symbol": "Elephant's Tusk", "animal": "Female Mongoose", "tree": "Jackfruit"},
            {"name": "22. Shravana", "sanskrit": "Shravana", "devanagari": "श्रवण", "lord": "Moon", "remainder": "4", "deity": "Vishnu",
             "gana": "Deva", "guna": "Sattva", "tattva": "Air", "start_degree": 280.0, "end_degree": 293.3333,
             "padas": ["Aries", "Taurus", "Gemini", "Cancer"], "motivation": "Artha",
             "nature": "Movable", "keywords": "The Listener, Learning, Preserving",
             "symbol": "Three Footprints", "animal": "Female Monkey", "tree": "Arka"},
            {"name": "23. Dhanishta", "sanskrit": "Dhanishta", "devanagari": "धनिष्ठा", "lord": "Mars", "remainder": "5", "deity": "Ashta Vasus",
             "gana": "Rakshasa", "guna": "Tamas", "tattva": "Ether", "start_degree": 293.3333, "end_degree": 306.6666,
             "padas": ["Leo", "Virgo", "Libra", "Scorpio"], "motivation": "Dharma",
             "nature": "Movable", "keywords": "The Richest One, Musical, Rhythmic",
             "symbol": "Drum/Flute", "animal": "Female Lion", "tree": "Shami"},
            {"name": "24. Shatabhisha", "sanskrit": "Shatabhisha", "devanagari": "शतभिषा", "lord": "Rahu", "remainder": "6", "deity": "Varuna",
             "gana": "Rakshasa", "guna": "Tamas", "tattva": "Ether", "start_degree": 306.6666, "end_degree": 320.0,
             "padas": ["Sagittarius", "Capricorn", "Aquarius", "Pisces"], "motivation": "Dharma",
             "nature": "Movable", "keywords": "The Hundred Healers, Mysterious",
             "symbol": "Empty Circle", "animal": "Female Horse", "tree": "Kadamba"},
            {"name": "25. Purva Bhadrapada", "sanskrit": "Purva Bhadrapada", "devanagari": "पूर्व भाद्रपद", "lord": "Jupiter", "remainder": "7", "deity": "Aja Ekapada",
             "gana": "Manushya", "guna": "Sattva", "tattva": "Ether", "start_degree": 320.0, "end_degree": 333.3333,
             "padas": ["Aries", "Taurus", "Gemini", "Cancer"], "motivation": "Artha",
             "nature": "Fierce", "keywords": "Intense, Spiritual, Transformative",
             "symbol": "Sword/Two Front Legs of Bed", "animal": "Male Lion", "tree": "Neem"},
            {"name": "26. Uttara Bhadrapada", "sanskrit": "Uttara Bhadrapada", "devanagari": "उत्तर भाद्रपद", "lord": "Saturn", "remainder": "8", "deity": "Ahir Budhnya",
             "gana": "Manushya", "guna": "Sattva", "tattva": "Ether", "start_degree": 333.3333, "end_degree": 346.6666,
             "padas": ["Leo", "Virgo", "Libra", "Scorpio"], "motivation": "Kama",
             "nature": "Fixed", "keywords": "Deep, Wise, Compassionate",
             "symbol": "Two Back Legs of Bed", "animal": "Female Cow", "tree": "Neem"},
            {"name": "27. Revati", "sanskrit": "Revati", "devanagari": "रेवती", "lord": "Mercury", "remainder": "0", "deity": "Pushan",
             "gana": "Deva", "guna": "Sattva", "tattva": "Ether", "start_degree": 346.6666, "end_degree": 360.0,
             "padas": ["Sagittarius", "Capricorn", "Aquarius", "Pisces"], "motivation": "Moksha",
             "nature": "Soft", "keywords": "The Wealthy One, Nourishing, Protective",
             "symbol": "Drum/Fish", "animal": "Female Elephant", "tree": "Honey Tree"},
        ]

    @staticmethod
    def get_all_planets():
        # ... (This method is complete and correct) ...
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
    def get_all_rashis():
        # ... (This method is complete and correct) ...
        """Returns a list of dictionaries, each containing detailed information about a Rashi (Zodiac Sign)."""
        return [
            {"name": "Aries", "sanskrit": "Mesha", "devanagari": "मेष", "lord": "Mars", "tattva": "Fire",
             "modality": "Movable", "symbol": "Ram", "start_degree": 0, "end_degree": 30,
             "body_part": "Head, Face", "house": 1, "quality": "Cardinal",
             "description": "Represents initiative, courage, and new beginnings. The pioneer of the zodiac.",
             "color": "#FF6B6B", "nature": "Hot, Dry", "polarity": "Masculine"},
            {"name": "Taurus", "sanskrit": "Vrishabha", "devanagari": "वृषभ", "lord": "Venus", "tattva": "Earth",
             "modality": "Fixed", "symbol": "Bull", "start_degree": 30, "end_degree": 60,
             "body_part": "Neck, Throat", "house": 2, "quality": "Fixed",
             "description": "Represents stability, material resources, and sensual pleasures.",
             "color": "#4ECDC4", "nature": "Cold, Dry", "polarity": "Feminine"},
            {"name": "Gemini", "sanskrit": "Mithuna", "devanagari": "मिथुन", "lord": "Mercury", "tattva": "Air",
             "modality": "Dual", "symbol": "Twins", "start_degree": 60, "end_degree": 90,
             "body_part": "Arms, Shoulders, Lungs", "house": 3, "quality": "Mutable",
             "description": "Represents communication, intellect, and duality.",
             "color": "#FFE66D", "nature": "Hot, Moist", "polarity": "Masculine"},
            {"name": "Cancer", "sanskrit": "Karka", "devanagari": "कर्क", "lord": "Moon", "tattva": "Water",
             "modality": "Movable", "symbol": "Crab", "start_degree": 90, "end_degree": 120,
             "body_part": "Chest, Breasts, Stomach", "house": 4, "quality": "Cardinal",
             "description": "Represents emotion, nurturing, and the inner world.",
             "color": "#95E1D3", "nature": "Cold, Moist", "polarity": "Feminine"},
            {"name": "Leo", "sanskrit": "Simha", "devanagari": "सिंह", "lord": "Sun", "tattva": "Fire",
             "modality": "Fixed", "symbol": "Lion", "start_degree": 120, "end_degree": 150,
             "body_part": "Heart, Upper Back", "house": 5, "quality": "Fixed",
             "description": "Represents self-expression, leadership, and creative power.",
             "color": "#F38181", "nature": "Hot, Dry", "polarity": "Masculine"},
            {"name": "Virgo", "sanskrit": "Kanya", "devanagari": "कन्या", "lord": "Mercury", "tattva": "Earth",
             "modality": "Dual", "symbol": "Maiden", "start_degree": 150, "end_degree": 180,
             "body_part": "Digestive System, Intestines", "house": 6, "quality": "Mutable",
             "description": "Represents service, analysis, and perfection.",
             "color": "#AA96DA", "nature": "Cold, Dry", "polarity": "Feminine"},
            {"name": "Libra", "sanskrit": "Tula", "devanagari": "तुला", "lord": "Venus", "tattva": "Air",
             "modality": "Movable", "symbol": "Scales", "start_degree": 180, "end_degree": 210,
             "body_part": "Kidneys, Lower Back", "house": 7, "quality": "Cardinal",
             "description": "Represents harmony, relationships, and justice.",
             "color": "#FCBAD3", "nature": "Hot, Moist", "polarity": "Masculine"},
            {"name": "Scorpio", "sanskrit": "Vrischika", "devanagari": "वृश्चिक", "lord": "Mars", "tattva": "Water",
             "modality": "Fixed", "symbol": "Scorpion", "start_degree": 210, "end_degree": 240,
             "body_part": "Reproductive Organs", "house": 8, "quality": "Fixed",
             "description": "Represents transformation, intensity, and hidden power.",
             "color": "#A8E6CF", "nature": "Cold, Moist", "polarity": "Feminine"},
            {"name": "Sagittarius", "sanskrit": "Dhanu", "devanagari": "धनु", "lord": "Jupiter", "tattva": "Fire",
             "modality": "Dual", "symbol": "Archer", "start_degree": 240, "end_degree": 270,
             "body_part": "Hips, Thighs", "house": 9, "quality": "Mutable",
             "description": "Represents wisdom, expansion, and higher truth.",
             "color": "#FF8B94", "nature": "Hot, Dry", "polarity": "Masculine"},
            {"name": "Capricorn", "sanskrit": "Makara", "devanagari": "मकर", "lord": "Saturn", "tattva": "Earth",
             "modality": "Movable", "symbol": "Sea-Goat", "start_degree": 270, "end_degree": 300,
             "body_part": "Knees, Bones", "house": 10, "quality": "Cardinal",
             "description": "Represents structure, discipline, and achievement.",
             "color": "#C7CEEA", "nature": "Cold, Dry", "polarity": "Feminine"},
            {"name": "Aquarius", "sanskrit": "Kumbha", "devanagari": "कुम्भ", "lord": "Saturn", "tattva": "Air",
             "modality": "Fixed", "symbol": "Water Bearer", "start_degree": 300, "end_degree": 330,
             "body_part": "Ankles, Circulation", "house": 11, "quality": "Fixed",
             "description": "Represents innovation, humanity, and collective ideals.",
             "color": "#B4F8C8", "nature": "Hot, Moist", "polarity": "Masculine"},
            {"name": "Pisces", "sanskrit": "Meena", "devanagari": "मीन", "lord": "Jupiter", "tattva": "Water",
             "modality": "Dual", "symbol": "Two Fishes", "start_degree": 330, "end_degree": 360,
             "body_part": "Feet, Lymphatic System", "house": 12, "quality": "Mutable",
             "description": "Represents spirituality, dissolution, and universal consciousness.",
             "color": "#FBE7C6", "nature": "Cold, Moist", "polarity": "Feminine"}
        ]

#===================================================================================================
# ASTRONOMICAL CALCULATOR (INTEGRATED & ENHANCED)
#===================================================================================================
class AstronomicalCalculator:
    # ... (This entire class remains unchanged from the previous correct response) ...
    """
    Handles all core astronomical calculations. This new, integrated engine is transplanted from
    the user's accurate script. It uses the Swiss Ephemeris library with proper UTC conversion
    and, crucially, applies the Lahiri Ayanamsa to provide precise Sidereal positions
    for Vedic astrological analysis.
    """
    def __init__(self, ayanamsa='LAHIRI'):
        """
        Initializes the calculator and sets the crucial sidereal mode for all subsequent calculations.
        """
        if SWISSEPH_AVAILABLE:
            try:
                # Set the directory where ephemeris files are stored.
                # If None, pyswisseph will use its bundled files.
                swe.set_ephe_path(None)

                # This is the MOST CRITICAL step for Vedic Astrology.
                # We are setting the Ayanamsa to Lahiri, which defines the Sidereal zodiac.
                ayanamsa_code = getattr(swe, f'SIDM_{ayanamsa}')
                swe.set_sid_mode(ayanamsa_code)
                print(f"✅ AstronomicalCalculator initialized with {ayanamsa} Ayanamsa.")
            except Exception as e:
                print(f"⚠️ Error initializing Swiss Ephemeris: {e}")
                messagebox.showerror("Initialization Error", f"Could not set Swiss Ephemeris Ayanamsa mode: {e}")

    def calculate_planet_positions(self, dt_local, lat, lon, timezone_offset):
        """
        Calculate the precise Sidereal positions of all Vedic planets for a given
        local datetime, location, and timezone offset.

        This is the primary calculation function that powers the Kundli generator.

        Args:
            dt_local (datetime): The LOCAL date and time for the calculation.
            lat (float): The latitude of the location.
            lon (float): The longitude of the location.
            timezone_offset (float): The timezone offset from UTC in hours (e.g., 5.5 for India).

        Returns:
            dict: A dictionary where keys are planet names and values are dictionaries
                  of their positional data, formatted for the AstroVighati Pro Elite UI.
                  Returns None if a critical calculation error occurs.
        """
        if not SWISSEPH_AVAILABLE:
            messagebox.showerror("Dependency Missing", "The 'pyswisseph' library is required for accurate calculations.")
            return None

        try:
            # 1. Convert Local Time to Universal Time (UTC)
            # This is a mandatory step, as all astronomical calculations are based on a universal standard.
            dt_utc = dt_local - timedelta(hours=timezone_offset)

            # 2. Convert UTC datetime to Julian Day Number
            # The Julian Day is the continuous count of days since the beginning of the Julian period
            # and is the standard input for most ephemeris libraries.
            jd_utc = swe.utc_to_jd(dt_utc.year, dt_utc.month, dt_utc.day,
                                   dt_utc.hour, dt_utc.minute, dt_utc.second, 1)[1]

            # 3. Define the planets to be calculated using their Swiss Ephemeris codes.
            # We use MEAN_NODE for Rahu as it is more common in many Vedic traditions.
            planet_codes = {
                "Sun": swe.SUN, "Moon": swe.MOON, "Mercury": swe.MERCURY,
                "Venus": swe.VENUS, "Mars": swe.MARS, "Jupiter": swe.JUPITER,
                "Saturn": swe.SATURN, "Rahu": swe.MEAN_NODE,
            }

            positions = {}

            # 4. Calculate the Ascendant (Lagna)
            # This is one of the most important points in the chart, representing the self.
            # We use the Placidus house system for this calculation.
            _, ascmc = swe.houses(jd_utc, lat, lon, b'P')
            asc_longitude = ascmc[0]
            positions['Ascendant'] = self._process_longitude(asc_longitude)

            # 5. Loop through each planet and calculate its position
            for name, code in planet_codes.items():
                # The swe.calc_ut function is the core of the Swiss Ephemeris, returning
                # detailed positional data for a given Julian Day and planet code.
                # FLG_SWIEPH: Use the best available ephemeris (Swiss Ephemeris).
                # FLG_SIDEREAL: Return sidereal positions (essential for Vedic).
                planet_pos_data = swe.calc_ut(jd_utc, code, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)[0]
                planet_longitude = planet_pos_data[0]

                # Process the raw longitude into the structured format required by the UI.
                positions[name] = self._process_longitude(planet_longitude)
                positions[name]['speed'] = planet_pos_data[3] # Store speed for potential future features.

            # 6. Calculate Ketu's position
            # Ketu is always exactly 180 degrees opposite to Rahu.
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
        """
        A private helper method to convert a raw decimal longitude (0-360) into a
        structured dictionary containing all the necessary astrological data points
        required by the application's UI.

        Args:
            longitude (float): The raw sidereal longitude of a celestial point.

        Returns:
            dict: A formatted dictionary with rashi, degree, nakshatra, etc.
        """
        # Determine the Rashi (Zodiac Sign)
        rashi_index = int(longitude / 30)
        rashi_name = EnhancedAstrologicalData.get_all_rashis()[rashi_index]['name']
        
        # Determine the degree within that Rashi
        degree_in_rashi = longitude % 30
        
        # Determine the Nakshatra (Lunar Mansion)
        nakshatra_name = "Unknown"
        for nak in EnhancedAstrologicalData.get_all_nakshatras():
            if nak['start_degree'] <= longitude < nak['end_degree']:
                nakshatra_name = nak['name']
                break
        
        # Format the degree into a DMS (Degrees, Minutes, Seconds) string for display
        dms_str = decimal_to_dms(degree_in_rashi)

        # Return the final, structured dictionary in the format expected by the application
        return {
            'longitude': longitude,
            'rashi': rashi_name,
            'degree_in_rashi': degree_in_rashi,
            'nakshatra': nakshatra_name,
            'dms': dms_str
        }

# *** INTEGRATION: Added VargaCalculator class from the first script ***
class VargaCalculator:
    """
    Accurate Varga Chart calculator.
    This class is transplanted directly from your first script and contains
    the mathematical logic for calculating various divisional charts.
    """
    def __init__(self):
        self.D60_DEITIES = ("Ghora","Rakshasa","Deva","Kubera","Yaksha","Kinnara","Bhrashta","Kulaghna","Garala","Vahni","Maya","Puriihaka","Apampathi","Marutwana","Kaala","Sarpa","Amrita","Indu","Mridu","Komala","Heramba","Brahma","Vishnu","Maheshwara","Deva","Ardra","Kalinasa","Kshiteesa","Kamalakara","Gulika","Mrityu","Kaala","Davagni","Ghora","Yama","Kantaka","Sudha","Amrita","Poorna","VishaDagdha","Kulanasa","Vamshakshya","Utpata","Kaala","Saumya","Komala","Seetala","Karaladamshtra","Chandramukhi","Praveena","Kaalpavaka","Dandayudha","Nirmala","Saumya","Kroora","Atisheetala","Amrita","Payodhi","Bhramana","Chandrarekha")

    def calculate(self, varga_num, d1_lon, d1_sign):
        varga_map = {2: self._calculate_d2, 3: self._calculate_d3, 9: self._calculate_d9, 60: self._calculate_d60}
        if varga_num in varga_map: return varga_map[varga_num](d1_lon, d1_sign)
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

    def _calculate_d9(self, d1_lon, d1_sign):
        amsa_index = math.floor(d1_lon / (30/9))
        lon = (d1_lon % (30/9)) * 9
        sign_type = (d1_sign - 1) % 4
        start_signs = {0: 1, 1: 10, 2: 7, 3: 4} # Fiery, Earthy, Airy, Watery
        sign = (start_signs[sign_type] + amsa_index - 1) % 12 + 1
        return sign, lon, ""
        
    def _calculate_d60(self, d1_lon, d1_sign):
        amsa_index = math.floor(d1_lon * 2) # 60 divisions in 30 degrees
        lon = (d1_lon * 2 % 1) * 30
        sign_offset = amsa_index % 12
        d60_sign = ((d1_sign - 1 + sign_offset) % 12) + 1
        details = self.D60_DEITIES[amsa_index]
        return d60_sign, lon, details

#===================================================================================================
# IMAGE GENERATOR FOR PLANETS
#===================================================================================================
class PlanetImageGenerator:
    # ... (This entire class remains unchanged) ...
    """
    A utility class for creating astrological images programmatically using Pillow.
    This includes generating stylized icons for each planet and drawing a full
    zodiac wheel chart, complete with rashi segments and plotted planet positions.
    """

    @staticmethod
    def create_planet_icon(planet_name, size=100):
        """
        Creates a visually appealing, stylized icon for a given planet.
        Includes a colored orb, a soft glow, and the planet's astrological symbol.

        Args:
            planet_name (str): The name of the planet (e.g., "Sun", "Mars").
            size (int): The width and height of the icon in pixels.

        Returns:
            Image: A Pillow Image object, or None if Pillow is not available.
        """
        if not PIL_AVAILABLE:
            return None

        color = EnhancedAstrologicalData.PLANET_COLORS.get(planet_name, "#CCCCCC")

        # Create a new transparent image.
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Draw a multi-layered outer glow for a soft, ethereal effect.
        for i in range(5, 0, -1):
            alpha = int(50 * (i / 5))
            offset = i * 3
            glow_color = tuple(list(PlanetImageGenerator.hex_to_rgb(color)) + [alpha])
            draw.ellipse([offset, offset, size-offset, size-offset],
                         fill=glow_color, outline=None)

        # Draw the main solid planet circle.
        margin = 15
        draw.ellipse([margin, margin, size-margin, size-margin],
                      fill=color, outline="#FFFFFF", width=2)

        # Add the planet's astrological symbol to the center.
        try:
            # Attempt to load a standard system font.
            font_size = int(size * 0.4)
            font = ImageFont.truetype("arial.ttf", font_size)
        except IOError:
            # Fallback to a default font if Arial isn't found.
            font = ImageFont.load_default()

        planet_data = next((p for p in EnhancedAstrologicalData.get_all_planets()
                              if p['name'] == planet_name), None)
        if planet_data:
            symbol = planet_data.get('symbol', planet_name[0])
            # Calculate text position to center it perfectly.
            bbox = draw.textbbox((0, 0), symbol, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            text_x = (size - text_width) / 2
            text_y = (size - text_height) / 2
            draw.text((text_x, text_y), symbol, fill='white', font=font)

        return img

    @staticmethod
    def hex_to_rgb(hex_color):
        """Helper function to convert a hex color string (e.g., "#FF6B6B") to an RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    @staticmethod
    def create_zodiac_wheel(size=800, planet_positions=None):
        """
        Creates a complete South-Indian style zodiac wheel chart image.

        Args:
            size (int): The width and height of the chart image.
            planet_positions (dict): A dictionary of planetary positions from AstronomicalCalculator.

        Returns:
            Image: A Pillow Image object, or None if Pillow is not available.
        """
        if not PIL_AVAILABLE:
            return None

        # Create a blank white canvas.
        img = Image.new('RGBA', (size, size), (255, 255, 255, 255))
        draw = ImageDraw.Draw(img)

        center_x, center_y = size // 2, size // 2
        outer_radius = size // 2 - 20
        inner_radius = outer_radius - 80

        rashis = EnhancedAstrologicalData.get_all_rashis()

        # Draw the 12 zodiac sections as colored pie slices.
        for i, rashi in enumerate(rashis):
            start_angle = i * 30
            end_angle = (i + 1) * 30

            # Convert astrological angles (0° at Aries) to PIL angles (0° at 3 o'clock).
            pil_start = start_angle
            pil_end = end_angle

            color = rashi['color']
            # Draw the outer colored band for the rashi.
            draw.pieslice([center_x - outer_radius, center_y - outer_radius,
                           center_x + outer_radius, center_y + outer_radius],
                          pil_start, pil_end, fill=color + '80', outline='#555', width=2)

        # Draw the inner white area.
        draw.ellipse([center_x - inner_radius, center_y - inner_radius,
                      center_x + inner_radius, center_y + inner_radius],
                     fill='white', outline='#555', width=2)

        # Draw the 12 radial lines separating the signs.
        for i in range(12):
            angle = math.radians(i * 30)
            x1 = center_x + inner_radius * math.cos(angle)
            y1 = center_y + inner_radius * math.sin(angle)
            x2 = center_x + outer_radius * math.cos(angle)
            y2 = center_y + outer_radius * math.sin(angle)
            draw.line([x1, y1, x2, y2], fill='#333333', width=2)

        # Add abbreviated rashi names inside each segment.
        try:
            font = ImageFont.truetype("arialbd.ttf", 16) # Bold font
        except IOError:
            font = ImageFont.load_default()

        for i, rashi in enumerate(rashis):
            angle = math.radians(i * 30 + 15) # Angle to the middle of the segment
            text_radius = (outer_radius + inner_radius) / 2
            x = center_x + text_radius * math.cos(angle)
            y = center_y + text_radius * math.sin(angle)
            text = rashi['name'][:3].upper()
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            draw.text((x - text_width/2, y - text_height/2), text, fill='#000000', font=font)

        # Plot the planets on the chart if their positions are provided.
        if planet_positions:
            try:
                planet_font = ImageFont.truetype("arial.ttf", 14)
            except IOError:
                planet_font = ImageFont.load_default()

            for planet_name, pos_data in planet_positions.items():
                if planet_name == 'Ascendant':
                    # Draw Ascendant as a special line.
                    asc_degree = pos_data['longitude']
                    angle = math.radians(asc_degree)
                    x1 = center_x + (inner_radius-10) * math.cos(angle)
                    y1 = center_y + (inner_radius-10) * math.sin(angle)
                    x2 = center_x + outer_radius * math.cos(angle)
                    y2 = center_y + outer_radius * math.sin(angle)
                    draw.line([x1, y1, x2, y2], fill='#E74C3C', width=3)
                    draw.text((x1 - 20, y1 - 10), "Asc", fill='#E74C3C', font=font)
                    continue

                degree = pos_data['longitude']
                angle = math.radians(degree)

                # Place a circular marker for the planet.
                marker_radius = inner_radius - 40
                x = center_x + marker_radius * math.cos(angle)
                y = center_y + marker_radius * math.sin(angle)

                planet_color = EnhancedAstrologicalData.PLANET_COLORS.get(planet_name, '#000000')
                draw.ellipse([x-12, y-12, x+12, y+12], fill=planet_color, outline='white', width=2)

                # Add the planet's two-letter label.
                label = planet_name[:2]
                draw.text((x-7, y-8), label, fill='white', font=planet_font)

        return img

#===================================================================================================
# ENHANCED THEME MANAGER
#===================================================================================================
class EnhancedThemeManager:
    # ... (This entire class remains unchanged) ...
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
        This method dynamically configures colors for all standard ttk widgets and
        manually sets colors for non-ttk widgets to ensure a consistent look.
        It intelligently handles light vs. dark themes for text and background contrast.

        Args:
            app (AstroVighatiElite): The main application instance.
            theme_name (str): The name of the theme to apply.
        """
        # Get the color palette for the selected theme.
        theme = EnhancedThemeManager.THEMES.get(theme_name, EnhancedThemeManager.THEMES["Cosmic Dark"])
        app.current_theme_data = theme

        style = ttk.Style()
        style.theme_use('clam') # Use a modern, configurable theme base.

        # --- Define Core Colors ---
        bg_dark = theme["bg_dark"]
        bg_light = theme["bg_light"]
        accent = theme["accent"]
        neutral = theme["neutral"]

        # --- IMPROVEMENT: Determine theme type for contrast ---
        # This flag helps decide whether text should be light (on dark bg) or dark (on light bg).
        is_light_theme = theme_name == "Classic Light"

        # Define primary foreground and background colors based on theme type.
        fg_color = bg_light if not is_light_theme else bg_dark
        main_bg_color = bg_dark if not is_light_theme else bg_light
        widget_bg_color = neutral if not is_light_theme else bg_dark # Input field background
        select_fg_color = bg_dark if not is_light_theme else bg_light

        # --- Configure Root and General Styles ---
        app.root.configure(bg=main_bg_color)
        style.configure('.', background=main_bg_color, foreground=fg_color, font=('Segoe UI', 10))
        style.configure('TFrame', background=main_bg_color)
        style.configure('TLabel', background=main_bg_color, foreground=fg_color)
        style.configure('Heading.TLabel', font=('Segoe UI', 12, 'bold'), foreground=accent)
        style.configure('Title.TLabel', font=('Segoe UI', 16, 'bold'), foreground=accent)

        # --- Configure Notebook (Tabs) ---
        style.configure('TNotebook', background=main_bg_color, borderwidth=0)
        style.configure('TNotebook.Tab', background=neutral, foreground=fg_color, padding=[15, 8], font=('Segoe UI', 10, 'bold'))
        style.map('TNotebook.Tab',
                    background=[('selected', accent)],
                    foreground=[('selected', select_fg_color)])

        # --- Configure LabelFrame ---
        style.configure('TLabelframe', background=main_bg_color, bordercolor=accent, relief='groove')
        style.configure('TLabelframe.Label', background=main_bg_color, foreground=accent, font=('Segoe UI', 11, 'bold'))

        # --- Configure Buttons ---
        style.configure('TButton', background=neutral, foreground=fg_color, font=('Segoe UI', 10, 'bold'), borderwidth=1, relief='flat', padding=10)
        style.map('TButton',
                    background=[('active', accent)],
                    foreground=[('active', select_fg_color)])
        style.configure('Accent.TButton', background=accent, foreground=select_fg_color, font=('Segoe UI', 12, 'bold'), padding=12)
        style.map('Accent.TButton',
                    background=[('active', bg_light)],
                    foreground=[('active', bg_dark)])

        # --- IMPROVEMENT: Configure Entry, Spinbox, and Combobox with proper contrast ---
        style.configure('TEntry', fieldbackground=widget_bg_color, foreground=fg_color, insertcolor=fg_color, bordercolor=accent)
        style.map('TEntry', foreground=[('focus', fg_color)], fieldbackground=[('focus', widget_bg_color)])
        style.configure('TSpinbox', fieldbackground=widget_bg_color, foreground=fg_color, insertcolor=fg_color, arrowcolor=fg_color, bordercolor=accent)
        style.map('TSpinbox', background=[('active', neutral)])

        style.configure('TCombobox', fieldbackground=widget_bg_color, foreground=fg_color, selectbackground=accent, selectforeground=select_fg_color, arrowcolor=fg_color)
        style.map('TCombobox',
                    fieldbackground=[('readonly', widget_bg_color)],
                    selectbackground=[('readonly', accent)],
                    foreground=[('readonly', fg_color)])

        # Configure the dropdown list of the Combobox.
        app.root.option_add('*TCombobox*Listbox.background', widget_bg_color)
        app.root.option_add('*TCombobox*Listbox.foreground', fg_color)
        app.root.option_add('*TCombobox*Listbox.selectBackground', accent)
        app.root.option_add('*TCombobox*Listbox.selectForeground', select_fg_color)

        # --- Configure Other Widgets ---
        style.configure('TScale', background=main_bg_color, troughcolor=neutral)
        style.configure('TProgressbar', background=accent, troughcolor=neutral)
        style.configure('Treeview', background=widget_bg_color, foreground=fg_color, fieldbackground=widget_bg_color, rowheight=30)
        style.configure('Treeview.Heading', background=neutral, foreground=accent, font=('Segoe UI', 11, 'bold'))
        style.map('Treeview',
                    background=[('selected', accent)],
                    foreground=[('selected', select_fg_color)])
        style.configure('Vertical.TScrollbar', background=neutral, troughcolor=main_bg_color, arrowcolor=fg_color)
        style.map('Vertical.TScrollbar', background=[('active', accent)])

        # --- IMPROVEMENT: Manually configure non-ttk widgets for better theme adherence ---
        # This block now correctly handles both light and dark themes.
        try:
            # Define colors for Text, ScrolledText, and Listbox widgets.
            text_bg = widget_bg_color
            text_fg = fg_color

            # List of all tab instances to iterate through.
            all_tabs = [
                app.kundli_tab, app.vighati_tab, app.transit_tab,
                app.dasha_tab, app.nakshatra_tab, app.planet_tab,
                app.rashi_tab, app.yoga_tab
            ]

            # Iterate through each tab and style its specific non-ttk widgets.
            for tab in all_tabs:
                # Find and style any scrolledtext/text widgets within the tab.
                for widget_name in ['results_text', 'details_text', 'analysis_text', 'info_text', 'transit_text', 'prediction_text', 'dasha_text', 'planet_text', 'rashi_text', 'rajyoga_text', 'dosha_text', 'mahapurusha_text']:
                    if hasattr(tab, widget_name):
                        widget = getattr(tab, widget_name)
                        widget.config(background=text_bg, foreground=text_fg, insertbackground=accent, selectbackground=accent, selectforeground=select_fg_color)

                # Find and style any listbox widgets.
                for widget_name in ['nak_listbox', 'rashi_listbox', 'planet_listbox']:
                    if hasattr(tab, widget_name):
                        widget = getattr(tab, widget_name)
                        widget.config(background=text_bg, foreground=text_fg, selectbackground=accent, selectforeground=select_fg_color)

        except Exception as e:
            # This catch helps prevent a crash if a widget doesn't exist when the theme is first applied.
            print(f"Warning: Could not apply theme to a specific non-ttk widget. Error: {e}")

#===================================================================================================
# MAIN ELITE APPLICATION
#===================================================================================================
class AstroVighatiElite:
    """
    The main application class. It orchestrates the entire GUI, including the main window,
    menu bar, status bar, and the notebook containing all the feature tabs. It holds
    instances of the calculator and data classes and passes them to the tabs that need them.
    """

    def __init__(self, root):
        """
        Initializes the main application window and its components.

        Args:
            root (tk.Tk): The root Tkinter window.
        """
        self.root = root
        self.root.title("AstroVighati Pro Elite - Advanced Vedic Astrology Suite")
        self.root.geometry("1800x1000") # Set a large initial size
        self.root.minsize(1400, 800) # Set a minimum size to prevent UI cramping

        # Instantiate core components
        self.astro_data = EnhancedAstrologicalData()
        self.calculator = AstronomicalCalculator() # Instantiating the new, accurate D1 calculator
        self.varga_calculator = VargaCalculator() # *** INTEGRATION: Instantiating the Varga calculator
        self.planet_images = {} # A cache for generated planet icons

        # --- Theme Management ---
        self.current_theme = tk.StringVar(value="Cosmic Dark")
        self.current_theme_data = {} # To store the current theme's color palette

        # --- UI Initialization ---
        self.create_status_bar()
        self.create_main_notebook()
        self.create_tabs()
        self.create_menu()

        # Apply the default theme at startup.
        EnhancedThemeManager.apply_theme(self, self.current_theme.get())

        # Pre-load planet images if Pillow is available for faster display.
        if PIL_AVAILABLE:
            self.load_planet_images()

    def create_status_bar(self):
        """Creates the status bar at the bottom of the window."""
        self.status_var = tk.StringVar(value="Ready - Elite Edition | Sidereal Engine Active")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief='sunken', anchor='w', padding=5)
        status_bar.pack(side='bottom', fill='x')

    def create_main_notebook(self):
        """Creates the main ttk.Notebook widget that will hold all the tabs."""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=(10, 0))

    def create_tabs(self):
        """
        Instantiates and adds all the functional tabs to the main notebook.
        Each tab is an instance of its own dedicated class.
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
        # ... (This entire method remains unchanged) ...
        """Creates the main application menu bar (File, Theme, Tools, Help)."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # --- File Menu ---
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Chart", command=self.new_chart)
        file_menu.add_command(label="Save Chart", command=self.save_chart)
        file_menu.add_command(label="Load Chart", command=self.load_chart)
        file_menu.add_separator()
        file_menu.add_command(label="Export to PDF", command=self.export_pdf)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # --- Theme Menu ---
        theme_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Theme", menu=theme_menu)
        # Dynamically create a radio button for each available theme.
        for theme_name in EnhancedThemeManager.THEMES.keys():
            theme_menu.add_radiobutton(
                label=theme_name,
                variable=self.current_theme,
                command=lambda t=theme_name: self.change_theme(t)
            )

        # --- Tools Menu ---
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Panchang", command=self.show_panchang)
        tools_menu.add_command(label="Muhurta Finder", command=self.show_muhurta)
        tools_menu.add_command(label="Compatibility Check", command=self.show_compatibility)
        tools_menu.add_separator()
        tools_menu.add_command(label="Download Ephemeris Data", command=self.download_ephemeris)

        # --- Help Menu ---
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="User Guide", command=self.show_help)
        help_menu.add_command(label="Video Tutorials", command=self.show_tutorials)
        help_menu.add_separator()
        help_menu.add_command(label="About", command=self.show_about)

    def load_planet_images(self):
        # ... (This entire method remains unchanged) ...
        """Pre-generates and caches planet icons to avoid lag when they are first displayed."""
        for planet in self.astro_data.get_all_planets():
            name = planet['name']
            img = PlanetImageGenerator.create_planet_icon(name, 80)
            if img:
                self.planet_images[name] = ImageTk.PhotoImage(img)

    def change_theme(self, theme_name):
        # ... (This entire method remains unchanged) ...
        """Callback function to change the application's theme."""
        EnhancedThemeManager.apply_theme(self, theme_name)
        self.status_var.set(f"Theme changed to {theme_name}")

    def new_chart(self):
        # ... (This entire method remains unchanged) ...
        """Clears the chart and switches to the Kundli tab."""
        self.notebook.select(self.kundli_tab)
        messagebox.showinfo("New Chart", "Ready for new birth details.")

    def save_chart(self):
        # ... (This entire method remains unchanged) ...
        """Saves the current chart data to a file."""
        messagebox.showinfo("Save Chart", "Chart saving functionality - Coming soon!")

    def load_chart(self):
        # ... (This entire method remains unchanged) ...
        """Loads a chart from a file."""
        messagebox.showinfo("Load Chart", "Chart loading functionality - Coming soon!")

    def export_pdf(self):
        # ... (This entire method remains unchanged) ...
        """Exports the current chart and analysis to a PDF report."""
        messagebox.showinfo("Export PDF", "PDF export functionality - Coming soon!")

    def show_panchang(self):
        # ... (This entire method remains unchanged) ...
        """Shows the Panchang calculator tool."""
        messagebox.showinfo("Panchang", "Panchang calculator - Coming soon!")

    def show_muhurta(self):
        # ... (This entire method remains unchanged) ...
        """Shows the Muhurta (electional astrology) finder tool."""
        messagebox.showinfo("Muhurta", "Muhurta finder - Coming soon!")

    def show_compatibility(self):
        # ... (This entire method remains unchanged) ...
        """Shows the chart compatibility (synastry) checker."""
        messagebox.showinfo("Compatibility", "Compatibility checker - Coming soon!")

    def download_ephemeris(self):
        # ... (This entire method remains unchanged) ...
        """Informs the user about the status of the Swiss Ephemeris data."""
        if SWISSEPH_AVAILABLE:
            messagebox.showinfo("Ephemeris", "Swiss Ephemeris (pyswisseph) is installed and active!")
        else:
            messagebox.showinfo("Ephemeris", "Please install pyswisseph for full accuracy:\npip install pyswisseph")

    def show_help(self):
        # ... (This method is updated to include Vargas) ...
        """Displays a user guide in a message box."""
        help_text = """
        AstroVighati Pro Elite - User Guide

        KUNDLI & VARGAS:
        - Enter birth details (date, time, location, and timezone offset from UTC).
        - Click 'Generate Kundli' to calculate accurate Sidereal planetary positions.
        - View the interactive D1 chart wheel and analysis.
        - Go to the 'Divisional Charts (Vargas)' tab, select a Varga from the dropdown
          to see the corresponding divisional chart positions.

        VIGHATI RECTIFIER:
        - Use for birth time rectification when the exact time is unknown.
        - Enter the approximate birth time, sunrise time, and the native's known Nakshatra.
        - The system will find precise times within the search range that match the Nakshatra.

        TRANSITS, DASHA, EXPLORER TABS:
        - These tabs function as before, providing tools for transits, Dasha periods,
          and exploring detailed astrological data.
        """
        messagebox.showinfo("User Guide", help_text)

    def show_tutorials(self):
        # ... (This entire method remains unchanged) ...
        """Provides a link to video tutorials."""
        messagebox.showinfo("Tutorials", "Video tutorials are planned and will be available at our website.")

    def show_about(self):
        # ... (This method is updated for the new version) ...
        """Displays the 'About' dialog with application information."""
        about_text = """
        AstroVighati Pro Elite v4.3

        Advanced Vedic Astrology Suite
        with Integrated Sidereal Engine (Lahiri Ayanamsa)

        Features:
        • Real-time D1 & Varga calculations via Swiss Ephemeris
        • Beautiful, programmatically generated chart visualizations
        • Comprehensive Kundli analysis
        • Transit predictions & Dasha timeline
        • Yoga & Dosha informational guide
        • Vighati birth time rectification tool

        © 2024 - Elite Edition
        """
        messagebox.showinfo("About", about_text)

#===================================================================================================
# TAB 1: KUNDLI GENERATOR (& VARGAS)
#===================================================================================================
class KundliGeneratorTab(ttk.Frame):
    # ... (Docstring updated) ...
    """
    This tab provides the primary functionality of generating a Vedic birth chart (Kundli)
    and its associated Divisional Charts (Vargas). It features input fields for birth data,
    a large canvas to display the visual chart, and a results area with tabs for planetary
    positions, detailed analysis, and Varga calculations.
    """

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.chart_image = None # To hold a reference to the PhotoImage object
        self.planet_positions = {}
        
        # *** INTEGRATION: Data for Varga dropdown ***
        self.varga_map = {"D2 - Hora": 2, "D3 - Drekkana": 3, "D9 - Navamsa": 9, "D60 - Shashtyamsa": 60}


        # Use a PanedWindow to allow the user to resize the input and output panels.
        paned = ttk.PanedWindow(self, orient='horizontal')
        paned.pack(expand=True, fill='both', padx=10, pady=10)

        # Left panel for user inputs.
        left_panel = ttk.Frame(paned, padding=10)
        paned.add(left_panel, weight=1)

        # Right panel for displaying the chart and results.
        right_panel = ttk.Frame(paned, padding=10)
        paned.add(right_panel, weight=2)

        # Build the UI components for each panel.
        self.create_input_panel(left_panel)
        self.create_chart_panel(right_panel)

    def create_input_panel(self, parent):
        # ... (This entire method remains unchanged) ...
        """Creates the input form for birth name, date, time, and location."""
        # --- Birth Details Frame ---
        birth_frame = ttk.LabelFrame(parent, text="Birth Details", padding=15)
        birth_frame.pack(fill='x', pady=(0, 10), expand=True)
        birth_frame.grid_columnconfigure(1, weight=1) # Make entry column expandable

        # Name input
        ttk.Label(birth_frame, text="Name:").grid(row=0, column=0, sticky='w', pady=5, padx=5)
        self.name_var = tk.StringVar()
        ttk.Entry(birth_frame, textvariable=self.name_var).grid(row=0, column=1, sticky='ew', pady=5, padx=5)

        # Date of Birth input using Spinboxes
        ttk.Label(birth_frame, text="Date (DD/MM/YYYY):").grid(row=1, column=0, sticky='w', pady=5, padx=5)
        date_frame = ttk.Frame(birth_frame)
        date_frame.grid(row=1, column=1, sticky='ew', pady=5, padx=5)
        self.day_var = tk.StringVar(value="14")
        self.month_var = tk.StringVar(value="11")
        self.year_var = tk.StringVar(value="2003")
        ttk.Spinbox(date_frame, from_=1, to=31, textvariable=self.day_var, width=5).pack(side='left', fill='x', expand=True)
        ttk.Spinbox(date_frame, from_=1, to=12, textvariable=self.month_var, width=5).pack(side='left', fill='x', expand=True)
        ttk.Spinbox(date_frame, from_=1900, to=2100, textvariable=self.year_var, width=8).pack(side='left', fill='x', expand=True)

        # Time of Birth input using Spinboxes
        ttk.Label(birth_frame, text="Time (24h format):").grid(row=2, column=0, sticky='w', pady=5, padx=5)
        time_frame = ttk.Frame(birth_frame)
        time_frame.grid(row=2, column=1, sticky='ew', pady=5, padx=5)
        self.hour_var = tk.StringVar(value="19")
        self.minute_var = tk.StringVar(value="41")
        self.second_var = tk.StringVar(value="46")
        ttk.Spinbox(time_frame, from_=0, to=23, textvariable=self.hour_var, width=5, format="%02.0f").pack(side='left', fill='x', expand=True)
        ttk.Spinbox(time_frame, from_=0, to=59, textvariable=self.minute_var, width=5, format="%02.0f").pack(side='left', fill='x', expand=True)
        ttk.Spinbox(time_frame, from_=0, to=59, textvariable=self.second_var, width=5, format="%02.0f").pack(side='left', fill='x', expand=True)

        # --- Location Frame ---
        location_frame = ttk.LabelFrame(parent, text="Location", padding=15)
        location_frame.pack(fill='x', pady=(0, 10), expand=True)
        location_frame.grid_columnconfigure(1, weight=1)

        # Latitude/Longitude inputs
        ttk.Label(location_frame, text="Latitude:").grid(row=0, column=0, sticky='w', pady=5, padx=5)
        self.lat_var = tk.StringVar(value="28.8344")
        ttk.Entry(location_frame, textvariable=self.lat_var).grid(row=0, column=1, sticky='ew', pady=5, padx=5)

        ttk.Label(location_frame, text="Longitude:").grid(row=1, column=0, sticky='w', pady=5, padx=5)
        self.lon_var = tk.StringVar(value="77.5699")
        ttk.Entry(location_frame, textvariable=self.lon_var).grid(row=1, column=1, sticky='ew', pady=5, padx=5)

        ttk.Label(location_frame, text="City:").grid(row=2, column=0, sticky='w', pady=5, padx=5)
        self.city_var = tk.StringVar(value="Ghaziabad")
        ttk.Entry(location_frame, textvariable=self.city_var).grid(row=2, column=1, sticky='ew', pady=5, padx=5)

        # *** INTEGRATION CRITICAL CHANGE: Added Timezone Input ***
        ttk.Label(location_frame, text="Timezone Offset (UTC):").grid(row=3, column=0, sticky='w', pady=5, padx=5)
        self.tz_var = tk.StringVar(value="5.5") # Default for India
        ttk.Entry(location_frame, textvariable=self.tz_var).grid(row=3, column=1, sticky='ew', pady=5, padx=5)

        # --- Action Button ---
        ttk.Button(parent, text="🎯 Generate Kundli", command=self.generate_kundli, style='Accent.TButton').pack(fill='x', pady=20, ipady=10)

        # --- Quick Info Display ---
        info_frame = ttk.LabelFrame(parent, text="Quick Info", padding=10)
        info_frame.pack(fill='both', expand=True)
        self.info_text = tk.Text(info_frame, height=10, wrap='word', font=('Segoe UI', 9))
        self.info_text.pack(fill='both', expand=True)
        self.info_text.insert('1.0', "Generate a chart to see quick information...")
        self.info_text.config(state='disabled')

    def create_chart_panel(self, parent):
        """Creates the panel for the visual chart and detailed results tabs."""
        # Top section for the chart image.
        chart_frame = ttk.LabelFrame(parent, text="Birth Chart (Kundli / कुंडली)", padding=10)
        chart_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        # A Canvas widget to draw the chart image on.
        self.chart_canvas = tk.Canvas(chart_frame, bg='white', highlightthickness=0)
        self.chart_canvas.pack(expand=True, fill='both')
        self.chart_canvas.bind("<Configure>", self.on_resize_chart) # Re-draw chart on resize

        # Bottom section using a Notebook for tabulated results.
        analysis_notebook = ttk.Notebook(parent)
        analysis_notebook.pack(fill='both', expand=True)

        # Tab 1: Planetary Positions Table
        positions_frame = ttk.Frame(analysis_notebook)
        analysis_notebook.add(positions_frame, text="Planetary Positions (D1)")
        # Use a Treeview widget for a clean, sortable table.
        columns = ('planet', 'rashi', 'dms', 'nakshatra', 'lord')
        self.positions_tree = ttk.Treeview(positions_frame, columns=columns, show='headings', height=10)
        self.positions_tree.heading('planet', text='Planet (Graha)')
        self.positions_tree.heading('rashi', text='Rashi')
        self.positions_tree.heading('dms', text='Longitude (DMS)')
        self.positions_tree.heading('nakshatra', text='Nakshatra')
        self.positions_tree.heading('lord', text='Nakshatra Lord')
        # Set column widths
        for col, width in [('planet', 150), ('rashi', 150), ('dms', 120), ('nakshatra', 200), ('lord', 100)]:
            self.positions_tree.column(col, width=width, anchor='center')
        
        # Add a scrollbar to the table.
        scrollbar = ttk.Scrollbar(positions_frame, orient='vertical', command=self.positions_tree.yview)
        self.positions_tree.configure(yscrollcommand=scrollbar.set)
        self.positions_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Tab 2: Detailed Text Analysis
        analysis_frame = ttk.Frame(analysis_notebook)
        analysis_notebook.add(analysis_frame, text="Detailed Analysis")
        self.analysis_text = scrolledtext.ScrolledText(analysis_frame, wrap='word', font=('Segoe UI', 10))
        self.analysis_text.pack(fill='both', expand=True)

        # *** INTEGRATION: Add new tab for Divisional Charts ***
        varga_frame = ttk.Frame(analysis_notebook, padding=10)
        analysis_notebook.add(varga_frame, text="Divisional Charts (Vargas)")

        # Add controls to the varga frame
        varga_control_frame = ttk.Frame(varga_frame)
        varga_control_frame.pack(fill='x', pady=(0, 10))
        ttk.Label(varga_control_frame, text="Select Varga Chart:").pack(side='left', padx=(0, 10))
        
        self.varga_var = tk.StringVar()
        varga_combo = ttk.Combobox(varga_control_frame, textvariable=self.varga_var, 
                                   values=list(self.varga_map.keys()), state="readonly", width=20)
        varga_combo.pack(side='left')
        varga_combo.set("D9 - Navamsa")
        varga_combo.bind("<<ComboboxSelected>>", self.update_varga_display)

        # Add Treeview for varga results
        varga_columns = ('planet', 'varga_rashi', 'varga_dms', 'details')
        self.varga_tree = ttk.Treeview(varga_frame, columns=varga_columns, show='headings')
        self.varga_tree.heading('planet', text='Planet')
        self.varga_tree.heading('varga_rashi', text='Varga Rashi')
        self.varga_tree.heading('varga_dms', text='Varga Longitude')
        self.varga_tree.heading('details', text='Details')
        self.varga_tree.pack(fill='both', expand=True, pady=(10,0))
        
    # ... (on_resize_chart method remains unchanged) ...
    def on_resize_chart(self, event):
        """Redraw the chart image when the canvas is resized to keep it centered and scaled."""
        if self.chart_image:
            self.chart_canvas.delete('all')
            # Calculate new center coordinates
            canvas_width = event.width
            canvas_height = event.height
            # Re-create the zodiac wheel at the new size
            new_size = min(canvas_width, canvas_height)
            if new_size > 50: # Avoid drawing if too small
                chart_img = PlanetImageGenerator.create_zodiac_wheel(new_size, self.planet_positions)
                if chart_img:
                    self.chart_image = ImageTk.PhotoImage(chart_img)
                    self.chart_canvas.create_image(canvas_width / 2, canvas_height / 2, image=self.chart_image)


    def generate_kundli(self):
        # ... (This method is updated to trigger a Varga calculation) ...
        """
        The main logic function for this tab. It gathers user input, calls the
        calculation engine, populates all the output widgets with D1 results,
        and then automatically triggers an update for the selected Varga chart.
        """
        try:
            # --- 1. Gather and Validate Inputs ---
            name = self.name_var.get()
            day, month, year = int(self.day_var.get()), int(self.month_var.get()), int(self.year_var.get())
            hour, minute, second = int(self.hour_var.get()), int(self.minute_var.get()), int(self.second_var.get())
            lat, lon = float(self.lat_var.get()), float(self.lon_var.get())
            tz_offset = float(self.tz_var.get()) # *** INTEGRATION: Get timezone offset
            city = self.city_var.get()
            birth_dt_local = datetime(year, month, day, hour, minute, second)

            # --- 2. Perform Calculations using the new Integrated Engine ---
            self.app.status_var.set("Calculating Sidereal positions (Lahiri)...")
            # *** INTEGRATION: Pass all required arguments to the new calculator ***
            self.planet_positions = self.app.calculator.calculate_planet_positions(birth_dt_local, lat, lon, tz_offset)

            if not self.planet_positions: # Handle calculation failure
                self.app.status_var.set("Calculation failed. Please check inputs and console.")
                return

            # --- 3. Update UI with Results ---
            self.update_positions_tree() # Populate the D1 table
            self.app.status_var.set("Generating chart visualization...")
            self.generate_chart_image() # Draw the D1 chart
            self.app.status_var.set("Generating analysis...")
            self.generate_analysis(name, birth_dt_local, city) # Generate text report
            self.update_quick_info() # Update the quick info panel

            # *** INTEGRATION: Automatically update the Varga display ***
            self.update_varga_display()

            self.app.status_var.set("Kundli generated successfully!")
            messagebox.showinfo("Success", "Kundli generated successfully using the Sidereal (Lahiri) Engine!")

        except ValueError:
            messagebox.showerror("Input Error", "Please ensure all fields have valid numbers.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate Kundli:\n{str(e)}")
            self.app.status_var.set("Error generating Kundli")

    # ... (update_positions_tree, generate_chart_image, generate_analysis, etc. remain unchanged) ...
    def update_positions_tree(self):
        """Clears and repopulates the planetary positions Treeview widget."""
        self.positions_tree.delete(*self.positions_tree.get_children()) # Clear old data

        # Define a consistent order for displaying planets
        planet_order = ["Ascendant", "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]

        for planet_name in planet_order:
            if planet_name in self.planet_positions:
                pos_data = self.planet_positions[planet_name]
                rashi = pos_data.get('rashi', 'N/A')
                dms = pos_data.get('dms', 'N/A')
                nakshatra_eng = pos_data.get('nakshatra', 'N/A')

                # Find full data for names
                planet_info = next((p for p in self.app.astro_data.get_all_planets() if p['name'] == planet_name), {})
                rashi_info = next((r for r in self.app.astro_data.get_all_rashis() if r['name'] == rashi), {})
                nakshatra_info = next((n for n in self.app.astro_data.get_all_nakshatras() if n['name'] == nakshatra_eng), {})

                # Format names with Sanskrit/Devanagari
                planet_display = f"{planet_name} ({planet_info.get('devanagari', '')})" if planet_info else planet_name
                rashi_display = f"{rashi} ({rashi_info.get('devanagari', '')})"
                nakshatra_display = f"{nakshatra_eng} ({nakshatra_info.get('devanagari', '')})"

                # Get the lord of the nakshatra the planet is in.
                lord = nakshatra_info.get('lord', 'N/A')

                self.positions_tree.insert('', 'end', values=(planet_display, rashi_display, dms, nakshatra_display, lord))

    def generate_chart_image(self):
        """Generates the zodiac wheel image and displays it on the canvas."""
        if not PIL_AVAILABLE:
            self.chart_canvas.delete('all')
            self.chart_canvas.create_text(
                self.chart_canvas.winfo_width() / 2, self.chart_canvas.winfo_height() / 2,
                text="Chart visualization requires Pillow.\nPlease install: pip install pillow",
                font=('Segoe UI', 14), fill='gray'
            )
            return

        # Get current canvas size to draw a perfectly fitting chart.
        canvas_size = min(self.chart_canvas.winfo_width(), self.chart_canvas.winfo_height()) - 10 # Add padding
        chart_img = PlanetImageGenerator.create_zodiac_wheel(canvas_size, self.planet_positions)
        if chart_img:
            self.chart_image = ImageTk.PhotoImage(chart_img)
            self.chart_canvas.delete('all')
            # Place the image in the center of the canvas.
            self.chart_canvas.create_image(
                self.chart_canvas.winfo_width() / 2,
                self.chart_canvas.winfo_height() / 2,
                image=self.chart_image
            )

    def generate_analysis(self, name, birth_dt, city):
        """Generates a formatted string of basic chart analysis and displays it."""
        self.analysis_text.config(state='normal')
        self.analysis_text.delete('1.0', tk.END)

        # --- Build the analysis string ---
        analysis = f"""
╔═══════════════════════════════════════════════════════════════════════════════════╗
║                               VEDIC BIRTH CHART ANALYSIS                          ║
╚═══════════════════════════════════════════════════════════════════════════════════╝

Name: {name}
Birth Date: {birth_dt.strftime('%d %B %Y')}
Birth Time: {birth_dt.strftime('%H:%M:%S')}
Birth Place: {city}

═══════════════════════════════════════════════════════════════════════════════════

ASCENDANT (LAGNA / लग्न) ANALYSIS:
"""
        if 'Ascendant' in self.planet_positions:
            asc_data = self.planet_positions['Ascendant']
            asc_rashi_info = next((r for r in self.app.astro_data.get_all_rashis() if r['name'] == asc_data['rashi']), {})
            asc_nak_info = next((n for n in self.app.astro_data.get_all_nakshatras() if n['name'] == asc_data['nakshatra']), {})

            analysis += f"""
Ascendant Sign: {asc_rashi_info.get('name')} ({asc_rashi_info.get('devanagari')})
Ascendant Nakshatra: {asc_nak_info.get('name')} ({asc_nak_info.get('devanagari')})
Ascendant Degree: {asc_data['degree_in_rashi']:.2f}°

The Ascendant represents your physical body, personality, and approach to life.
With a rising sign of {asc_rashi_info.get('name')}, your core personality is likely to be {self.get_rashi_trait(asc_rashi_info.get('name'))}.
"""
        analysis += """
═══════════════════════════════════════════════════════════════════════════════════

MOON SIGN (CHANDRA RASHI / चंद्र राशि) ANALYSIS:
"""
        if 'Moon' in self.planet_positions:
            moon_data = self.planet_positions['Moon']
            moon_rashi_info = next((r for r in self.app.astro_data.get_all_rashis() if r['name'] == moon_data['rashi']), {})
            moon_nak_info = next((n for n in self.app.astro_data.get_all_nakshatras() if n['name'] == moon_data['nakshatra']), {})

            analysis += f"""
Moon Sign (Chandra Rashi): {moon_rashi_info.get('name')} ({moon_rashi_info.get('devanagari')})
Moon Nakshatra (Janma Nakshatra): {moon_nak_info.get('name')} ({moon_nak_info.get('devanagari')})
Moon Degree: {moon_data['degree_in_rashi']:.2f}°

The Moon represents your mind, emotions, and inner self. Your Moon in {moon_rashi_info.get('name')}
indicates an emotional nature that is {self.get_rashi_trait(moon_rashi_info.get('name'))}.
Your birth Nakshatra, {moon_nak_info.get('name')}, is crucial for calculating Dasha periods and understanding
your deeper psychological patterns.
"""
        analysis += """
═══════════════════════════════════════════════════════════════════════════════════

PLANETARY STRENGTH & DIGNITY:
"""
        # Analyze the dignity of each planet.
        for planet_name, pos_data in self.planet_positions.items():
            if planet_name == 'Ascendant': continue
            rashi = pos_data['rashi']
            degree = pos_data['degree_in_rashi']
            planet_info = next((p for p in self.app.astro_data.get_all_planets() if p['name'] == planet_name), None)
            if planet_info:
                dignity = self.check_dignity(planet_info, rashi, degree)
                analysis += f"\n{planet_name:<10}: Placed in {rashi:<12} - {dignity}"

        analysis += "\n\n" + "═" * 75 + "\n"
        self.analysis_text.insert('1.0', analysis)
        self.analysis_text.config(state='disabled')

    def get_rashi_trait(self, rashi_name):
        """Helper function to get a one-line trait for a given Rashi."""
        rashi_info = next((r for r in self.app.astro_data.get_all_rashis() if r['name'] == rashi_name), None)
        return rashi_info['description'].split('.')[0].lower().replace("represents", "").strip() if rashi_info else "unique"

    def check_dignity(self, planet_info, rashi, degree):
        """
        Checks the dignity of a planet (exalted, debilitated, own sign, etc.).
        This is a key part of determining a planet's strength.
        """
        dignities = planet_info.get('dignities', {})
        if rashi in dignities.get('Exaltation', ''): return "EXALTED ⭐ (Very Strong)"
        if rashi in dignities.get('Debilitation', ''): return "DEBILITATED (Weak)"
        if rashi in dignities.get('Own Sign', ''): return "OWN SIGN (Strong)"
        if rashi in dignities.get('Moolatrikona', ''): return "MOOLATRIKONA (Very Good)"

        # Check friendship status with the lord of the sign it's in.
        rashi_data = next((r for r in self.app.astro_data.get_all_rashis() if r['name'] == rashi), None)
        if rashi_data:
            lord = rashi_data['lord']
            if lord in planet_info.get('friendly', []): return "Friend's Sign (Good)"
            if lord in planet_info.get('enemy', []): return "Enemy's Sign (Challenging)"

        return "Neutral Position"

    def update_quick_info(self):
        """Updates the small quick info panel with the most important chart details."""
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
        if 'Sun' in self.planet_positions:
            sun_info = next((r for r in self.app.astro_data.get_all_rashis() if r['name'] == self.planet_positions['Sun']['rashi']), {})
            info += f"☀️ Sun Sign: {sun_info.get('name')} ({sun_info.get('devanagari')})\n"
        self.info_text.insert('1.0', info)
        self.info_text.config(state='disabled')

    # *** INTEGRATION: New method to calculate and display Varga charts ***
    def update_varga_display(self, event=None):
        """
        Calculates and displays the selected divisional chart in the Varga tab.
        This function is triggered when a D1 chart is generated or when the
        user selects a new Varga from the dropdown.
        """
        self.varga_tree.delete(*self.varga_tree.get_children()) # Clear old results

        if not self.planet_positions:
            self.varga_tree.insert('', 'end', values=("Please generate a D1 chart first.", "", "", ""))
            return

        selected_varga_key = self.varga_var.get()
        if not selected_varga_key:
            return

        varga_num = self.varga_map[selected_varga_key]
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
# TAB 2: ENHANCED VIGHATI RECTIFIER
#===================================================================================================
class EnhancedVighatiTab(ttk.Frame):
    # ... (This entire class and all subsequent Tab classes remain unchanged) ...
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
        """
        Performs the Vighati calculation and searches for matching birth times.
        The core logic involves converting time from sunrise into 'Vighatis' and
        then applying a formula to find a 'remainder' that corresponds to the
        Nakshatra lord sequence.
        """
        self.results_text.delete('1.0', tk.END)
        self.results_text.insert('1.0', "Calculating...\n")

        # --- 1. Get and Convert Inputs ---
        hour, minute, second = int(self.hour_var.get()), int(self.minute_var.get()), int(self.second_var.get())
        sunrise_h, sunrise_m = int(self.sunrise_hour.get()), int(self.sunrise_min.get())
        target_nak_full = self.nak_var.get()
        target_nak_eng = target_nak_full.split(' (')[0] # Parse the English name
        search_range = self.range_var.get()

        target_nak_data = next((n for n in self.nakshatras if n['name'] == target_nak_eng), None)
        if not target_nak_data:
            messagebox.showerror("Error", "Invalid Nakshatra selected")
            return
        target_remainder = int(target_nak_data['remainder'])

        # Convert all times to seconds from midnight for easy calculation.
        birth_seconds = hour * 3600 + minute * 60 + second
        sunrise_seconds = sunrise_h * 3600 + sunrise_m * 60

        # --- 2. Perform Initial Calculation ---
        time_diff = birth_seconds - sunrise_seconds
        if time_diff < 0: time_diff += 86400  # Handle post-midnight births

        vighati_value = time_diff / 24.0 # 1 Vighati = 24 seconds
        vighati_rounded = round(vighati_value)
        computed_remainder = int((vighati_rounded * 4) / 9) % 9
        is_match = (computed_remainder == target_remainder)

        # --- 3. Build and Display Results Header ---
        results = f"""
╔════════════════════════════════════════════════════════════════════════════════════════╗
║                               VIGHATI RECTIFICATION RESULTS                            ║
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

        # --- 4. Search for Matching Times within Range ---
        matches_found = 0
        if is_match:
            results += "\n🎉 PERFECT MATCH! The given birth time already matches the target Nakshatra.\n"
        else:
            results += "SEARCHING FOR MATCHING TIMES:\n\n"
            results += f"{'Time':<12} | {'Offset':<12} | {'Vighati':<10} | {'Rem':<5} | {'Status':<8}\n"
            results += "-" * 75 + "\n"
            search_seconds = search_range * 60

            # Iterate second-by-second through the search window.
            for offset in range(-search_seconds, search_seconds + 1):
                test_seconds = birth_seconds + offset
                # Handle day boundaries.
                if test_seconds < 0: test_seconds += 86400
                elif test_seconds >= 86400: test_seconds -= 86400

                # Recalculate Vighati for the new test time.
                new_diff = test_seconds - sunrise_seconds
                if new_diff < 0: new_diff += 86400
                new_vighati_rounded = round(new_diff / 24.0)
                new_remainder = int((new_vighati_rounded * 4) / 9) % 9

                # If a match is found, add it to the results table.
                if new_remainder == target_remainder:
                    matches_found += 1
                    test_h, test_m, test_s = test_seconds // 3600, (test_seconds % 3600) // 60, test_seconds % 60
                    offset_sign, offset_m, offset_s = "+" if offset >= 0 else "-", abs(offset) // 60, abs(offset) % 60
                    offset_str = f"{offset_sign}{offset_m:02d}m{offset_s:02d}s"
                    results += f"{test_h:02d}:{test_m:02d}:{test_s:02d} | {offset_str:<11} | {new_vighati_rounded:>8} | {new_remainder:>3} | ✓ MATCH\n"
                    if matches_found >= 15: # Limit results to prevent flooding the UI.
                        results += "\n... (showing first 15 matches only)\n"
                        break
            results += "-" * 75 + "\n"
            results += f"\n📊 SUMMARY: Found {matches_found} matching time(s) within ±{search_range} minutes.\n"

        # --- 5. Add Explanation and Finalize ---
        results += """
════════════════════════════════════════════════════════════════════════════════════════

VIGHATI SYSTEM EXPLANATION:
The Vighati system divides the time from sunrise into 3600 Vighatis (each 24 seconds).
The birth Nakshatra is determined by the formula: Remainder = (Vighati × 4 ÷ 9) mod 9.
This remainder (0-8) corresponds to the repeating sequence of Nakshatra lords.
"""
        self.results_text.insert('1.0', results)
        self.app.status_var.set(f"Vighati calculation complete - Found {matches_found} matches.")

# ... (The remaining Tab classes: TransitCalculatorTab, DashaTimelineTab, EnhancedNakshatraTab, 
#      EnhancedPlanetTab, EnhancedRashiTab, YogasDoshasTab, and the main execution block
#      are IDENTICAL to the previous correct response and are included here for completeness.) ...

#===================================================================================================
# TAB 3: TRANSIT CALCULATOR
#===================================================================================================
class TransitCalculatorTab(ttk.Frame):
    """
    This tab displays the current real-time positions of the planets (transits).
    It also provides general interpretations of major upcoming planetary movements,
    serving as a quick reference for current astrological weather.
    """

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.create_ui()

    def create_ui(self):
        """Creates the UI for the Transit Calculator."""
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(expand=True, fill='both')

        ttk.Label(main_frame, text="🌍 TRANSIT CALCULATOR & PREDICTIONS", style='Title.TLabel').pack(pady=(0, 20))

        # --- Control Panel ---
        control_frame = ttk.LabelFrame(main_frame, text="Transit Date", padding=15)
        control_frame.pack(fill='x', pady=(0, 15))
        ttk.Button(control_frame, text="📅 Show Current Transits", command=self.show_current_transits, style='Accent.TButton').pack(side='left', padx=5, ipady=8)
        ttk.Button(control_frame, text="🔮 Show General Predictions", command=self.show_predictions).pack(side='left', padx=5, ipady=8)

        # --- Results Notebook ---
        results_notebook = ttk.Notebook(main_frame)
        results_notebook.pack(fill='both', expand=True)

        # Current Positions Tab
        transit_frame = ttk.Frame(results_notebook)
        results_notebook.add(transit_frame, text="Current Positions")
        self.transit_text = scrolledtext.ScrolledText(transit_frame, font=('Courier New', 10), wrap='word')
        self.transit_text.pack(fill='both', expand=True)

        # Predictions Tab
        pred_frame = ttk.Frame(results_notebook)
        results_notebook.add(pred_frame, text="Predictions")
        self.prediction_text = scrolledtext.ScrolledText(pred_frame, font=('Segoe UI', 10), wrap='word')
        self.prediction_text.pack(fill='both', expand=True)

        self.transit_text.insert('1.0', "Click 'Show Current Transits' to see real-time planetary positions...")
        self.prediction_text.insert('1.0', "Click 'Show General Predictions' for insights on major transits...")


    def show_current_transits(self):
        """Calculates planetary positions for the current time and displays them."""
        now_utc = datetime.utcnow()
        now_local = datetime.now()

        # Use a default location (e.g., New Delhi) for transit calculations.
        # Note: Timezone is 0 for UTC calculations.
        positions = self.app.calculator.calculate_planet_positions(now_utc, 28.6139, 77.2090, 0)

        text = f"""
╔══════════════════════════════════════════════════════════════════╗
║                       CURRENT PLANETARY TRANSITS                 ║
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
        """Displays static, general information about interpreting transits."""
        pred_text = """
╔══════════════════════════════════════════════════════════════════╗
║                   TRANSIT PREDICTIONS (GENERAL)                  ║
╚══════════════════════════════════════════════════════════════════╝

IMPORTANT UPCOMING TRANSITS:

🌟 JUPITER (गुरु) TRANSIT:
   Jupiter's transit generally brings expansion, optimism, and growth. When it
   transits through key houses in your natal chart (relative to your ascendant
   or moon), expect opportunities for advancement and wisdom.

♄ SATURN (शनि) TRANSIT:
   Saturn's transit demands discipline, hard work, and patience. It tests your
   foundations and brings important life lessons for long-term growth and stability.
   The Sade Sati (साढ़े साती) period (Saturn transiting the 12th, 1st, and 2nd from natal Moon)
   is a particularly significant phase of karmic reckoning and restructuring.

☊ RAHU-KETU (राहु-केतु) AXIS:
   The nodal axis creates significant karmic shifts and life-altering events.
   Pay attention to the houses they are transiting in your natal chart, as Rahu
   creates worldly ambition and Ketu brings detachment and spiritual insight.

═══════════════════════════════════════════════════════════════════

GENERAL GUIDANCE:
• Monitor transits of slow-moving planets (Saturn, Jupiter, Rahu, Ketu) as they
  have a more profound and long-lasting impact.
• Fast-moving planets (Sun, Moon, Mercury, Venus, Mars) create daily or weekly
  effects, influencing mood and short-term events.
• Pay special attention when any planet transits your natal Moon sign (Janma Rashi),
  as this directly impacts your mind and emotions.

NOTE: These are general predictions. For personalized results, transits must be
analyzed in the context of your unique birth chart and current Dasha periods.
"""
        self.prediction_text.delete('1.0', tk.END)
        self.prediction_text.insert('1.0', pred_text)

#===================================================================================================
# TAB 4: DASHA TIMELINE
#===================================================================================================
class DashaTimelineTab(ttk.Frame):
    """
    This tab calculates and displays the Vimshottari Dasha sequence, a fundamental
    timing system in Vedic astrology. It shows the major planetary periods (Mahadashas)
    and provides a brief interpretation for each.
    """

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.create_ui()

    def create_ui(self):
        """Creates the UI for the Dasha Timeline calculator."""
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(expand=True, fill='both')

        ttk.Label(main_frame, text="📊 VIMSHOTTARI DASHA TIMELINE", style='Title.TLabel').pack(pady=(0, 20))

        # --- Input Frame ---
        input_frame = ttk.LabelFrame(main_frame, text="Birth Details", padding=15)
        input_frame.pack(fill='x', pady=(0, 15))
        input_frame.grid_columnconfigure(1, weight=1)

        ttk.Label(input_frame, text="Birth Date (for age ref):").grid(row=0, column=0, sticky='w', pady=5)
        self.birth_date_var = tk.StringVar(value="08/10/2003")
        ttk.Entry(input_frame, textvariable=self.birth_date_var, width=20).grid(row=0, column=1, sticky='ew', padx=10)

        ttk.Label(input_frame, text="Moon Nakshatra:").grid(row=1, column=0, sticky='w', pady=5)
        self.moon_nak_var = tk.StringVar()
        nak_values = [f"{n['name']} ({n['devanagari']})" for n in self.app.astro_data.get_all_nakshatras()]
        nak_combo = ttk.Combobox(input_frame, textvariable=self.moon_nak_var,
                                 values=nak_values,
                                 state='readonly', width=25)
        nak_combo.grid(row=1, column=1, sticky='ew', padx=10)
        nak_combo.set(nak_values[0])

        # *** NEW FEATURE: Button to auto-fill from Kundli Tab ***
        ttk.Button(input_frame, text="Auto-Fill from Kundli Tab", command=self.autofill_from_kundli).grid(row=2, column=0, columnspan=1, pady=10, padx=5, sticky='w')

        ttk.Button(input_frame, text="Calculate Dasha Timeline", command=self.calculate_dasha, style='Accent.TButton').grid(row=2, column=1, columnspan=1, pady=15, ipady=8, sticky='e')

        # --- Results Display ---
        self.dasha_text = scrolledtext.ScrolledText(main_frame, font=('Courier New', 10), wrap='word')
        self.dasha_text.pack(fill='both', expand=True)
        self.dasha_text.insert('1.0', "Enter birth Nakshatra and click 'Calculate' to see the Dasha timeline...")

    def autofill_from_kundli(self):
        """
        A new helper function to automatically populate the input fields of this tab
        using the data calculated in the Kundli Generator tab. This greatly improves
        user workflow.
        """
        kundli_tab = self.app.kundli_tab
        if not kundli_tab.planet_positions:
            messagebox.showwarning("No Data", "Please generate a chart in the 'Kundli Generator' tab first.")
            return

        try:
            # Auto-fill birth date
            day = kundli_tab.day_var.get()
            month = kundli_tab.month_var.get()
            year = kundli_tab.year_var.get()
            self.birth_date_var.set(f"{day}/{month}/{year}")

            # Auto-fill Moon Nakshatra
            moon_data = kundli_tab.planet_positions.get("Moon")
            if moon_data:
                moon_nak_eng = moon_data['nakshatra']
                moon_nak_info = next((n for n in self.app.astro_data.get_all_nakshatras() if n['name'] == moon_nak_eng), None)
                if moon_nak_info:
                    moon_nak_full = f"{moon_nak_info['name']} ({moon_nak_info['devanagari']})"
                    self.moon_nak_var.set(moon_nak_full)
                    self.app.status_var.set("Dasha details auto-filled from Kundli tab.")
            else:
                 messagebox.showerror("Error", "Moon position data not found in the generated chart.")

        except Exception as e:
            messagebox.showerror("Auto-Fill Error", f"Could not auto-fill data: {e}")


    def calculate_dasha(self):
        """Calculates the Vimshottari Dasha sequence based on the birth Nakshatra."""
        try:
            # --- 1. Get Dasha Data and Inputs ---
            dasha_periods = {
                "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
                "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17
            }
            planet_order = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]

            nak_name_full = self.moon_nak_var.get()
            nak_name_eng = nak_name_full.split(' (')[0]
            birth_date_str = self.birth_date_var.get()
            birth_date = datetime.strptime(birth_date_str, "%d/%m/%Y")

            nak_data = next((n for n in self.app.astro_data.get_all_nakshatras() if n['name'] == nak_name_eng), None)
            if not nak_data: return

            # --- 2. Generate Timeline ---
            starting_lord = nak_data['lord']
            start_idx = planet_order.index(starting_lord)

            # Build the results string.
            text = f"""
╔══════════════════════════════════════════════════════════════════╗
║                       VIMSHOTTARI DASHA TIMELINE                 ║
╚══════════════════════════════════════════════════════════════════╝

Birth Nakshatra: {nak_name_full}
Starting Mahadasha: {starting_lord}

════════════════════════════════════════════════════════════════════

MAHADASHA SEQUENCE (Major Periods):

"""
            # Iterate through the 120-year cycle.
            current_date = birth_date
            for i in range(len(planet_order)):
                planet_eng = planet_order[(start_idx + i) % len(planet_order)]
                years = dasha_periods[planet_eng]

                planet_info = next((p for p in self.app.astro_data.get_all_planets() if p['name'] == planet_eng), {})
                planet_display = f"{planet_eng} ({planet_info.get('devanagari')})"

                start_date_str = current_date.strftime('%d-%b-%Y')
                end_date = current_date + timedelta(days=years * 365.25)
                end_date_str = end_date.strftime('%d-%b-%Y')

                text += f"{i+1}. {planet_display:<20} Mahadasha ({years} years): {start_date_str} to {end_date_str}\n"
                text += f"   └─ This period emphasizes themes of {self.get_dasha_interpretation(planet_eng)}.\n\n"

                current_date = end_date

            text += "═"*68 + "\nNOTE: This is a simplified timeline. Precise start dates depend on the Moon's exact degree at birth.\n"

            # --- 3. Display Results ---
            self.dasha_text.delete('1.0', tk.END)
            self.dasha_text.insert('1.0', text)
            self.app.status_var.set("Dasha timeline calculated.")

        except ValueError:
            messagebox.showerror("Input Error", "Please enter the date in DD/MM/YYYY format.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not calculate Dasha: {e}")

    def get_dasha_interpretation(self, planet):
        """Returns a brief keyword summary for a planet's Dasha period."""
        interpretations = {
            "Sun": "authority, career, self-expression, and father",
            "Moon": "emotions, home life, nurturing, and mother",
            "Mars": "energy, action, conflicts, courage, and property",
            "Mercury": "learning, communication, business, and intellect",
            "Jupiter": "wisdom, expansion, wealth, children, and spiritual growth",
            "Venus": "love, relationships, luxury, arts, and comfort",
            "Saturn": "discipline, hard work, responsibility, and karmic lessons",
            "Rahu": "material desires, foreign connections, ambition, and illusion",
            "Ketu": "spirituality, detachment, intuition, and past karma resolution"
        }
        return interpretations.get(planet, "transformation")

#===================================================================================================
# TAB 5: ENHANCED NAKSHATRA EXPLORER
#===================================================================================================
class EnhancedNakshatraTab(ttk.Frame):
    """
    An interactive explorer for the 27 Nakshatras. It features a searchable list
    on the left and a detailed information panel on the right that updates on selection.
    """

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.create_ui()

    def create_ui(self):
        """Creates the dual-panel UI for the Nakshatra explorer."""
        paned = ttk.PanedWindow(self, orient='horizontal')
        paned.pack(expand=True, fill='both', padx=10, pady=10)

        # Left panel: Searchable list of Nakshatras.
        left_panel = ttk.Frame(paned, padding=10)
        paned.add(left_panel, weight=1)
        ttk.Label(left_panel, text="⭐ NAKSHATRA LIST", style='Heading.TLabel').pack(pady=(0, 10))

        # Search entry
        self.search_var = tk.StringVar()
        self.search_var.trace_add('write', self.filter_nakshatras)
        ttk.Entry(left_panel, textvariable=self.search_var).pack(fill='x', pady=(0, 10))

        # Listbox to display Nakshatras
        self.nak_listbox = tk.Listbox(left_panel, font=('Segoe UI', 11), exportselection=False)
        self.nak_listbox.pack(fill='both', expand=True)
        self.nak_listbox.bind('<<ListboxSelect>>', self.on_select)

        self.populate_list()

        # Right panel: Detailed information display.
        right_panel = ttk.Frame(paned, padding=10)
        paned.add(right_panel, weight=2)
        self.details_text = scrolledtext.ScrolledText(right_panel, font=('Segoe UI', 11), wrap='word')
        self.details_text.pack(fill='both', expand=True)

        # Automatically select the first item on startup.
        self.nak_listbox.selection_set(0)
        self.on_select(None)

    def populate_list(self):
        """Fills the listbox with all Nakshatra names."""
        self.nak_listbox.delete(0, tk.END)
        for nak in self.app.astro_data.get_all_nakshatras():
            self.nak_listbox.insert(tk.END, f"{nak['name']} ({nak['devanagari']})")

    def filter_nakshatras(self, *args):
        """Filters the Nakshatra list based on the user's search query."""
        search_term = self.search_var.get().lower()
        self.nak_listbox.delete(0, tk.END)
        for nak in self.app.astro_data.get_all_nakshatras():
            if (search_term in nak['name'].lower() or
                search_term in nak['lord'].lower() or
                search_term in nak['sanskrit'].lower()):
                self.nak_listbox.insert(tk.END, f"{nak['name']} ({nak['devanagari']})")

    def on_select(self, event):
        """Callback function that triggers when a new Nakshatra is selected from the list."""
        selection = self.nak_listbox.curselection()
        if not selection: return
        nak_name_full = self.nak_listbox.get(selection[0])
        nak_name_eng = nak_name_full.split(' (')[0]
        nak_data = next((n for n in self.app.astro_data.get_all_nakshatras() if n['name'] == nak_name_eng), None)
        if nak_data:
            self.show_details(nak_data)

    def show_details(self, nak):
        """Displays formatted details of the selected Nakshatra in the text panel."""
        self.details_text.delete('1.0', tk.END)
        title = f"{nak['name'].upper()} ({nak['devanagari']})"
        details = f"""
╔══════════════════════════════════════════════════════════════════╗
║  {title.center(62)}                                              ║
╚══════════════════════════════════════════════════════════════════╝

CORE ATTRIBUTES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Ruling Lord         : {nak['lord']}
Presiding Deity     : {nak['deity']}
Symbol              : {nak.get('symbol', 'N/A')}
Animal Symbol       : {nak.get('animal', 'N/A')}
Sacred Tree         : {nak.get('tree', 'N/A')}

CLASSIFICATION:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Gana (Temperament)  : {nak['gana']}
Guna (Quality)      : {nak['guna']}
Tattva (Element)    : {nak['tattva']}
Nature              : {nak['nature']}
Motivation          : {nak['motivation']}

KEYWORDS & TRAITS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{nak['keywords']}

PADA (QUARTERS):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Each Nakshatra is divided into 4 Padas of 3°20' each.
Pada 1: {nak['padas'][0]} Navamsa
Pada 2: {nak['padas'][1]} Navamsa
Pada 3: {nak['padas'][2]} Navamsa
Pada 4: {nak['padas'][3]} Navamsa

CELESTIAL COORDINATES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Start Degree: {nak['start_degree']}° | End Degree: {nak['end_degree']}° | Span: 13°20'
"""
        self.details_text.insert('1.0', details)

#===================================================================================================
# TAB 6: ENHANCED PLANET GUIDE
#===================================================================================================
class EnhancedPlanetTab(ttk.Frame):
    """
    An interactive guide to the Navagrahas (the nine Vedic planets). It features
    a list of buttons on the left and a detailed information panel on the right.
    """

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.create_ui()

    def create_ui(self):
        """Creates the dual-panel UI for the Planet Guide."""
        paned = ttk.PanedWindow(self, orient='horizontal')
        paned.pack(expand=True, fill='both', padx=10, pady=10)

        # Left panel: A vertical list of buttons, one for each planet.
        left_panel = ttk.Frame(paned, padding=10)
        paned.add(left_panel, weight=1)
        ttk.Label(left_panel, text="🪐 NAVAGRAHA (नवग्रह)", style='Heading.TLabel').pack(pady=(0, 10))
        for planet in self.app.astro_data.get_all_planets():
            btn = ttk.Button(left_panel, text=f" {planet['symbol']} {planet['name']} ({planet['devanagari']})",
                             command=lambda p=planet: self.show_planet(p), width=20)
            btn.pack(fill='x', pady=2, ipady=4)

        # Right panel: Detailed information display.
        right_panel = ttk.Frame(paned, padding=10)
        paned.add(right_panel, weight=3)
        self.planet_text = scrolledtext.ScrolledText(right_panel, font=('Segoe UI', 10), wrap='word')
        self.planet_text.pack(fill='both', expand=True)

        # Show the Sun's details by default.
        self.show_planet(self.app.astro_data.get_all_planets()[0])

    def show_planet(self, planet):
        """Displays formatted details of the selected planet."""
        self.planet_text.delete('1.0', tk.END)
        title = f"{planet['name'].upper()} ({planet['sanskrit']} / {planet['devanagari']}) {planet['symbol']}"
        details = f"""
╔══════════════════════════════════════════════════════════════════╗
║  {title.center(62)}                                              ║
╚══════════════════════════════════════════════════════════════════╝

KARAKA (SIGNIFICATOR):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{planet['karaka']}

DIGNITIES & STRENGTH:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        for dignity, value in planet['dignities'].items():
            details += f"{dignity:<20}: {value}\n"
        details += f"""
BASIC PROPERTIES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Nature              : {planet['nature']}
Gender              : {planet['gender']}
Vimshottari Dasha   : {planet['vimshottari_dasha']}

RELATIONSHIPS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Friends             : {', '.join(planet['friendly'])}
Neutral             : {', '.join(planet.get('neutral', []))}
Enemies             : {', '.join(planet['enemy'])}

KEY SIGNIFICATIONS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{', '.join(planet.get('significations', []))}
"""
        self.planet_text.insert('1.0', details)

#===================================================================================================
# TAB 7: RASHI EXPLORER
#===================================================================================================
class EnhancedRashiTab(ttk.Frame):
    """
    An interactive explorer for the 12 Rashis (zodiac signs). Similar in structure
    to the Nakshatra tab, with a list on the left and a detail panel on the right.
    """

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.create_ui()

    def create_ui(self):
        """Creates the dual-panel UI for the Rashi explorer."""
        paned = ttk.PanedWindow(self, orient='horizontal')
        paned.pack(expand=True, fill='both', padx=10, pady=10)

        # Left panel: List of Rashis.
        left_panel = ttk.Frame(paned, padding=10)
        paned.add(left_panel, weight=1)
        ttk.Label(left_panel, text="♈ ZODIAC SIGNS (राशि)", style='Heading.TLabel').pack(pady=(0, 10))
        self.rashi_listbox = tk.Listbox(left_panel, font=('Segoe UI', 12), exportselection=False)
        self.rashi_listbox.pack(fill='both', expand=True)
        self.rashi_listbox.bind('<<ListboxSelect>>', self.on_select)
        for rashi in self.app.astro_data.get_all_rashis():
            self.rashi_listbox.insert(tk.END, f" {rashi['name']} ({rashi['devanagari']})")

        # Right panel: Detailed information display.
        right_panel = ttk.Frame(paned, padding=10)
        paned.add(right_panel, weight=2)
        self.rashi_text = scrolledtext.ScrolledText(right_panel, font=('Segoe UI', 11), wrap='word')
        self.rashi_text.pack(fill='both', expand=True)

        self.rashi_listbox.selection_set(0)
        self.on_select(None)

    def on_select(self, event):
        """Callback for when a new Rashi is selected."""
        selection = self.rashi_listbox.curselection()
        if not selection: return
        rashi_name_full = self.rashi_listbox.get(selection[0]).strip()
        rashi_name_eng = rashi_name_full.split(' (')[0]
        rashi_data = next((r for r in self.app.astro_data.get_all_rashis() if r['name'] == rashi_name_eng), None)
        if rashi_data:
            self.show_details(rashi_data)

    def show_details(self, rashi):
        """Displays formatted details of the selected Rashi."""
        self.rashi_text.delete('1.0', tk.END)
        title = f"{rashi['name'].upper()} ({rashi['sanskrit']} / {rashi['devanagari']}) - The {rashi['symbol']}"
        details = f"""
╔══════════════════════════════════════════════════════════════════╗
║  {title.center(62)}  ║
╚══════════════════════════════════════════════════════════════════╝

CORE ATTRIBUTES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Ruling Lord         : {rashi['lord']}
Element (Tattva)    : {rashi['tattva']}
Modality            : {rashi['modality']}
Polarity            : {rashi['polarity']}

DESCRIPTION:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{rashi['description']}
"""
        self.rashi_text.insert('1.0', details)

#===================================================================================================
# TAB 8: YOGAS & DOSHAS
#===================================================================================================
class YogasDoshasTab(ttk.Frame):
    """
    An informational tab that serves as a reference guide for important Yogas
    (auspicious planetary combinations) and Doshas (afflictions). It categorizes
    them into tabs for easy browsing.
    """

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.create_ui()

    def create_ui(self):
        """Creates the UI for the Yogas & Doshas reference guide."""
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(expand=True, fill='both')

        ttk.Label(main_frame, text="🔮 YOGAS & DOSHAS ANALYZER", style='Title.TLabel').pack(pady=(0, 20))
        ttk.Label(main_frame, text="A reference guide to important planetary combinations and afflictions.").pack(pady=(0, 15))

        # Use a Notebook to separate different categories of yogas/doshas.
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill='both', expand=True)

        # --- Rajyogas Tab ---
        rajyoga_frame = ttk.Frame(notebook)
        notebook.add(rajyoga_frame, text="Rajyogas (Royal Combinations)")
        self.rajyoga_text = scrolledtext.ScrolledText(rajyoga_frame, font=('Segoe UI', 10), wrap='word')
        self.rajyoga_text.pack(fill='both', expand=True, padx=5, pady=5)
        self.rajyoga_text.insert('1.0', self.get_rajyoga_info())

        # --- Doshas Tab ---
        dosha_frame = ttk.Frame(notebook)
        notebook.add(dosha_frame, text="Doshas (Afflictions)")
        self.dosha_text = scrolledtext.ScrolledText(dosha_frame, font=('Segoe UI', 10), wrap='word')
        self.dosha_text.pack(fill='both', expand=True, padx=5, pady=5)
        self.dosha_text.insert('1.0', self.get_dosha_info())

        # --- Pancha Mahapurusha Yogas Tab ---
        mahapurusha_frame = ttk.Frame(notebook)
        notebook.add(mahapurusha_frame, text="Pancha Mahapurusha Yogas")
        self.mahapurusha_text = scrolledtext.ScrolledText(mahapurusha_frame, font=('Segoe UI', 10), wrap='word')
        self.mahapurusha_text.pack(fill='both', expand=True, padx=5, pady=5)
        self.mahapurusha_text.insert('1.0', self.get_mahapurusha_info())

    def get_rajyoga_info(self):
        """Returns a formatted string of information about major Rajyogas."""
        return """
╔══════════════════════════════════════════════════════════════════╗
║             RAJYOGAS (राजयोग) - ROYAL COMBINATIONS                ║
╚══════════════════════════════════════════════════════════════════╝

Rajyogas are highly auspicious planetary combinations that can bestow power,
wealth, fame, and success upon a native, especially during their Dasha periods.

MAJOR RAJYOGAS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Gaja Kesari Yoga (गज केसरी योग): Jupiter in a Kendra (1, 4, 7, 10) from the Moon.
   Grants wisdom, wealth, fame, and intelligence.

2. Dharma-Karmadhipati Yoga: A connection between the lords of the 9th
   (Dharma) and 10th (Karma) houses. The most powerful Rajyoga for
   career success and high status.

3. Neecha Bhanga Rajyoga (नीच भंग राजयोग): Cancellation of a planet's debilitation. This
   can turn a weakness into an exceptional strength, often leading to a
   "rags to riches" story.

4. Viparita Rajyoga (विपरीत राजयोग): Formed by lords of challenging houses (6, 8, 12)
   being placed in other challenging houses. This can bring sudden gains
   and success after an initial period of struggle.

5. Pancha Mahapurusha Yogas (पंच महापुरुष योग): Five specific yogas formed by Mars, Mercury,
   Jupiter, Venus, or Saturn when strong in a Kendra house. (See next tab).
"""

    def get_dosha_info(self):
        """Returns a formatted string of information about major Doshas."""
        return """
╔══════════════════════════════════════════════════════════════════╗
║              DOSHAS (दोष) - PLANETARY AFFLICTIONS                ║
╚══════════════════════════════════════════════════════════════════╝

Doshas are challenging planetary combinations that can indicate areas of
difficulty or karmic lessons in a person's life.

MAJOR DOSHAS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Manglik Dosha (मांगलिक दोष): Mars placed in the 1st, 2nd, 4th, 7th,
   8th, or 12th house from the Ascendant, Moon, or Venus. Can cause
   challenges, delays, or discord in marriage. Its effects are often
   mitigated after the age of 28 or if the partner is also Manglik.

2. Kaal Sarpa Dosha (काल सर्प दोष): All seven planets are hemmed between the nodal axis
   of Rahu and Ketu. Can create a feeling of being fated, with sudden
   ups and downs and obstacles in life, though it can also produce
   great success after a period of struggle.

3. Pitra Dosha (पितृ दोष): Affliction to the Sun, the 9th house, or the 9th lord,
   often involving Rahu or Ketu. Indicates karmic debts related to
   ancestors and can manifest as issues with progeny, health, or family.

4. Grahan Dosha (ग्रहण दोष): The Sun or Moon is conjunct with Rahu or
   Ketu. Can create psychological complexes, confusion, and challenges
   related to the significations of the afflicted luminary.
"""

    def get_mahapurusha_info(self):
        """Returns a formatted string of info about Pancha Mahapurusha Yogas."""
        return """
╔══════════════════════════════════════════════════════════════════╗
║             PANCHA MAHAPURUSHA YOGAS (पंच महापुरुष योग)             ║
║               (Five Great Personality Combinations)              ║
╚══════════════════════════════════════════════════════════════════╝

Formed when one of the five non-luminary planets is in its own sign or
exaltation sign, AND is in a Kendra (1, 4, 7, 10) from the Ascendant.

THE FIVE YOGAS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Ruchaka Yoga (रूचक योग) - Mars: Creates a courageous, strong, and commanding
   personality. Excellent for military, sports, or leadership roles.

2. Bhadra Yoga (भद्र योग) - Mercury: Creates a highly intelligent, articulate, and
   skillful person with strong business acumen and communication skills.

3. Hamsa Yoga (हंस योग) - Jupiter: Creates a wise, spiritual, respected, and
   knowledgeable person. Indicates a noble character and good fortune.

4. Malavya Yoga (मालव्य योग) - Venus: Creates a beautiful, charming, artistic, and
   refined person who enjoys luxury, comfort, and harmonious relationships.

5. Sasa Yoga (शश योग) - Saturn: Creates a disciplined, patient, and influential
   leader, often in politics or service to the masses. Can grant longevity
   and power, especially in later life.
"""
#===================================================================================================
# MAIN EXECUTION BLOCK
#===================================================================================================
if __name__ == "__main__":
    try:
        # Create the main Tkinter window.
        root = tk.Tk()

        # Instantiate and run the main application class.
        app = AstroVighatiElite(root)

        # Welcome message printed to the console at startup.
        welcome_msg = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                      🌟 ASTROVIGHATI PRO ELITE v4.3 🌟                       ║
║                      Advanced Vedic Astrology Suite                          ║
║            (Featuring the Integrated Sidereal Calculation Engine)            ║
║                                                                              ║
║    Welcome! The application is now running. Please use the GUI window.       ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
        print(welcome_msg)

        # Start the Tkinter event loop. This keeps the window open and responsive.
        root.mainloop()

    except Exception as e:
        # A top-level exception handler to catch any critical startup errors.
        import traceback
        error_details = traceback.format_exc()

        print(f"\n{'='*70}")
        print("                         A CRITICAL APPLICATION ERROR OCCURRED")
        print(f"{'='*70}")
        print(f"\nAn unexpected error prevented the application from running:\n")
        print(error_details)
        print(f"\n{'='*70}")

        # Try to show the error in a GUI message box as a last resort.
        try:
            error_root = tk.Tk()
            error_root.withdraw()
            messagebox.showerror(
                "Critical Application Error",
                f"A fatal error occurred and the application must close.\n\n"
                f"Error: {str(e)}\n\n"
                "Please check the console for the full traceback."
            )
        except:
            pass