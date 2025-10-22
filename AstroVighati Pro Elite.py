# GUI Version - 6.0 (Nakshatra Syllables)

""" AstroVighati Pro Elite: Advanced Vedic Astrology Suite
Version: 6.0 with Integrated Knowledge Base and Advanced Varga Analysis

Description:
This script creates a comprehensive desktop application for Vedic astrology
using Python's Tkinter library. It features a modular, tab-based interface
and a high-precision, Sidereal (Lahiri Ayanamsa) calculation engine.

This version (v6.0) introduces a new feature based on authentic Vedic
sources (Avakahada Chakra) in the 'Nakshatra Explorer' tab:
- Adds a new "🗣️ Name Syllables" sub-tab for a quick reference of all 27
  Nakshatra padas and their corresponding name syllables.
- Enhances the "Details" view for each Nakshatra to include its specific
  name syllables.
- Rectifies a dependency-checking error (PIL vs. Pillow).

This version retains all features from v6.0, including:
- Python type hinting across the entire codebase.
- A resizable, paned layout in the Vighati Rectifier tab.
- Support for seconds-level precision in the Vighati sunrise time input.
- Uncapped results for the Vighati time search.
- Centralized constants for astrological rules (e.g., combustion orbs).

Core Architecture:
- Main Application Class (`AstroVighatiElite`): Initializes the main window,
  manages themes, menus, and all UI tabs.
- Tab Classes (e.g., `KundliGeneratorTab`): Each tab is a self-contained
  class responsible for its UI and functionality.
- Data Class (`EnhancedAstrologicalData`): A static, read-only database
  for astrological constants.
- Calculation Engine (`AstronomicalCalculator` & `VargaCalculator`):
  High-accuracy engine using `pyswisseph` with Lahiri Ayanamsa.
- Interpretation Engine (`InterpretationEngine`): The analytical core,
  containing a rich knowledge base for dynamic interpretations.
- Theming Engine (`EnhancedThemeManager`): Manages the visual styling.
"""

# --- Standard Library Imports ---
import importlib
import subprocess
import sys
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from datetime import datetime, timedelta
import threading
import math
import json
import os
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any, Callable

# --- Dependency Management ---

# A list of required third-party Python packages for the application to run fully.
# NOTE: Use the PyPI package name (e.g., "Pillow"), not the import name (e.g., "PIL").
required_packages: List[str] = [
    "Pillow",           # For handling images (imports as PIL)
    "requests",         # For potential future online features
    "pyswisseph",       # The core astronomical calculation engine
    "geopy",            # Used for geocoding (finding lat/lon from city name)
    "timezonefinder",   # Used for finding timezone from lat/lon
    "skyfield",         # Alternative astronomical library
    "matplotlib",       # For plotting charts (future feature)
    "numpy",            # Numerical processing
    "pandas",           # Data analysis (future feature)
    "reportlab"         # For PDF report generation (future feature)
]

dependencies_missing: bool = False  # Global flag to track installations.

def install_if_missing(package: str) -> None:
    """
    Checks if a given Python package is installed.
    If missing, it attempts to install it using 'pip'.
    Handles special import names (e.g., pyswisseph -> swisseph, Pillow -> PIL).

    Args:
        package (str): The name of the package on PyPI.
    """
    global dependencies_missing
    try:
        # Handle special package names vs. import names
        if package == 'pyswisseph':
            import_name = 'swisseph'
        elif package == 'Pillow':
            import_name = 'PIL'
        else:
            import_name = package

        # Try to import the package
        importlib.import_module(import_name)
        print(f"✅ Dependency Check: '{package}' is already installed.")

    except ImportError:
        # This block runs if 'import_module' fails.
        dependencies_missing = True
        print(f"⚙️ Dependency Missing: '{package}' not found. Attempting to install...")
        try:
            # Use subprocess to call 'pip install'
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✅ Successfully installed '{package}'.")
        except Exception as e:
            # Handle cases where pip install fails
            print(f"❌ FAILED to install '{package}'. Error: {e}")
            print(f"Please try installing the package manually using: pip install {package}")
            messagebox.showerror(
                "Dependency Error",
                f"Failed to auto-install '{package}'.\n"
                f"Please close the app, open a terminal, and run:\n\n"
                f"pip install {package}\n\n"
                "Then, restart the application."
            )
            sys.exit(1) # Exit if a critical dependency fails

# --- Dependency Check Block ---
print("="*60)
print("🚀 Initializing AstroVighati Pro Elite v6.0")
print("   Checking all required dependencies...")
print("="*60)
for pkg in required_packages:
    install_if_missing(pkg)

if dependencies_missing:
    print("\n🔄 Some packages were installed or re-checked.")
    print("   If you encounter issues, please restart the application.")
    print("="*60 + "\n")
else:
    print("\n✨ All dependencies are satisfied! Launching application...\n")
    print("="*60 + "\n")


# --- Graceful Library Importing ---
# Now that we've checked/installed, we import them for the application to use.

try:
    from PIL import Image, ImageTk, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("⚠️ Warning: Pillow (PIL) not found. Advanced image features will be disabled.")

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("⚠️ Warning: Requests not found. Online features will be disabled.")

try:
    import swisseph as swe
    SWISSEPH_AVAILABLE = True
except ImportError:
    SWISSEPH_AVAILABLE = False
    print("❌ CRITICAL: Swiss Ephemeris (pyswisseph) not found. Calculations will fail.")
    messagebox.showerror("Critical Error", "The 'pyswisseph' library is missing. The application cannot perform calculations and will exit.")
    sys.exit(1)

try:
    import matplotlib
    matplotlib.use('TkAgg') # Tell matplotlib to use the Tkinter backend
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("⚠️ Warning: Matplotlib not found. Chart visualization will be disabled.")

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    print("⚠️ Warning: NumPy not found. Advanced numerical calculations will be disabled.")

#===================================================================================================
# HELPER FUNCTIONS
#===================================================================================================

def decimal_to_dms(decimal_degrees: Optional[float]) -> str:
    """
    Converts a floating-point number representing decimal degrees into a
    human-readable string format of Degrees°, Minutes', and Seconds".

    Example: 28.6692 -> "28° 40' 09""

    Args:
        decimal_degrees (Optional[float]): The longitude or latitude in decimal format.

    Returns:
        str: A formatted string "DD° MM' SS\"" or "N/A" if input is invalid.
    """
    if not isinstance(decimal_degrees, (int, float)):
        return "N/A"

    is_negative = decimal_degrees < 0
    decimal_degrees = abs(decimal_degrees)

    degrees = int(decimal_degrees)
    minutes_float = (decimal_degrees - degrees) * 60
    minutes = int(minutes_float)
    seconds = int((minutes_float - minutes) * 60)

    sign = "-" if is_negative else ""

    # Format as {sign}DD° MM' SS"
    return f"{sign}{degrees:02d}° {minutes:02d}' {seconds:02d}\""

#===================================================================================================
# DATA & INTERPRETATION STORES
#===================================================================================================
class EnhancedAstrologicalData:
    """
    This class acts as a centralized, read-only database for all the static
    astrological information used by the application.

    Using '@staticmethod' means we can call these functions
    (e.g., `EnhancedAstrologicalData.get_all_planets()`) without
    needing to create an instance of the class. It's purely a data container.
    """

    # Static (class-level) dictionaries for quick lookups
    PLANET_COLORS: Dict[str, str] = {
        "Sun": "#FDB813", "Moon": "#C0C0C0", "Mars": "#CD5C5C",
        "Mercury": "#90EE90", "Jupiter": "#FFD700", "Venus": "#FFB6C1",
        "Saturn": "#4169E1", "Rahu": "#8B4513", "Ketu": "#A9A9A9",
        "Ascendant": "#E74C3C"
    }

    SIGNS: Dict[int, str] = {
        1: "Aries", 2: "Taurus", 3: "Gemini", 4: "Cancer", 5: "Leo", 6: "Virgo",
        7: "Libra", 8: "Scorpio", 9: "Sagittarius", 10: "Capricorn", 11: "Aquarius", 12: "Pisces"
    }

    # A reverse-lookup map. Useful for converting "Aries" back to 1.
    SIGN_NAME_TO_NUM: Dict[str, int] = {v: k for k, v in SIGNS.items()}

    # A map for Varga calculations that depend on sign nature (Odd/Even)
    SIGN_NATURE: Dict[int, str] = {
        1: "Odd", 2: "Even", 3: "Odd", 4: "Even", 5: "Odd", 6: "Even",
        7: "Odd", 8: "Even", 9: "Odd", 10: "Even", 11: "Odd", 12: "Even"
    }

    @staticmethod
    def get_varga_descriptions() -> Dict[str, Dict[str, str]]:
        """
        Provides the detailed descriptions for the 'Varga Meanings' tab.
        This is a knowledge base synthesized from classical texts.

        Returns:
            dict: A dictionary where each key (e.g., "D1 - Rashi") maps to
                  another dictionary containing its "title" and "description".
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

    @staticmethod
    def get_all_planets() -> List[Dict[str, Any]]:
        """
        Returns a comprehensive list of all 9 planets (Navagrahas) used
        in Vedic astrology, including their attributes.

        Returns:
            list: A list of dictionaries, where each dictionary is a planet.
        """
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
    def get_all_nakshatras() -> List[Dict[str, Any]]:
        """
        Returns a list of all 27 Nakshatras (lunar mansions) with their
        key attributes, including lord (for Dasha), remainder (for Vighati),
        and NEW: name syllables.

        Returns:
            list: A list of dictionaries, where each dictionary is a nakshatra.
        """
        return [
            # --- DATA UPDATED WITH SYLLABLES (AVAKAHADA CHAKRA) ---
            {"name": "1. Ashwini", "sanskrit": "Ashwini", "devanagari": "अश्विनी", "lord": "Ketu", "remainder": 0, "deity": "Ashwini Kumaras", "start_degree": 0.0, "end_degree": 13.3333, "padas": ["Aries", "Taurus", "Gemini", "Cancer"], "syllables": ["चू (Chu)", "चे (Che)", "चो (Cho)", "ला (La)"]},
            {"name": "2. Bharani", "sanskrit": "Bharani", "devanagari": "भरणी", "lord": "Venus", "remainder": 1, "deity": "Yama", "start_degree": 13.3333, "end_degree": 26.6666, "padas": ["Leo", "Virgo", "Libra", "Scorpio"], "syllables": ["ली (Li)", "लू (Lu)", "ले (Le)", "लो (Lo)"]},
            {"name": "3. Krittika", "sanskrit": "Krittika", "devanagari": "कृत्तिका", "lord": "Sun", "remainder": 2, "deity": "Agni", "start_degree": 26.6666, "end_degree": 40.0, "padas": ["Sagittarius", "Capricorn", "Aquarius", "Pisces"], "syllables": ["अ (A)", "ई (I)", "उ (U)", "ए (E)"]},
            {"name": "4. Rohini", "sanskrit": "Rohini", "devanagari": "रोहिणी", "lord": "Moon", "remainder": 3, "deity": "Brahma", "start_degree": 40.0, "end_degree": 53.3333, "padas": ["Aries", "Taurus", "Gemini", "Cancer"], "syllables": ["ओ (O)", "वा (Va)", "वी (Vi)", "वू (Vu)"]},
            {"name": "5. Mrigashira", "sanskrit": "Mrigashira", "devanagari": "मृगशिरा", "lord": "Mars", "remainder": 4, "deity": "Soma", "start_degree": 53.3333, "end_degree": 66.6666, "padas": ["Leo", "Virgo", "Libra", "Scorpio"], "syllables": ["वे (Ve)", "वो (Vo)", "का (Ka)", "की (Ki)"]},
            {"name": "6. Ardra", "sanskrit": "Ardra", "devanagari": "आर्द्रा", "lord": "Rahu", "remainder": 5, "deity": "Rudra", "start_degree": 66.6666, "end_degree": 80.0, "padas": ["Sagittarius", "Capricorn", "Aquarius", "Pisces"], "syllables": ["कू (Ku)", "घ (Gha)", "ङ (Na)", "छ (Chha)"]},
            {"name": "7. Punarvasu", "sanskrit": "Punarvasu", "devanagari": "पुनर्वसु", "lord": "Jupiter", "remainder": 6, "deity": "Aditi", "start_degree": 80.0, "end_degree": 93.3333, "padas": ["Aries", "Taurus", "Gemini", "Cancer"], "syllables": ["के (Ke)", "को (Ko)", "हा (Ha)", "ही (Hi)"]},
            {"name": "8. Pushya", "sanskrit": "Pushya", "devanagari": "पुष्य", "lord": "Saturn", "remainder": 7, "deity": "Brihaspati", "start_degree": 93.3333, "end_degree": 106.6666, "padas": ["Leo", "Virgo", "Libra", "Scorpio"], "syllables": ["हू (Hu)", "हे (He)", "हो (Ho)", "डा (Da)"]},
            {"name": "9. Ashlesha", "sanskrit": "Ashlesha", "devanagari": "आश्लेषा", "lord": "Mercury", "remainder": 8, "deity": "Nagas", "start_degree": 106.6666, "end_degree": 120.0, "padas": ["Sagittarius", "Capricorn", "Aquarius", "Pisces"], "syllables": ["डी (Di)", "डू (Du)", "डे (De)", "डो (Do)"]},
            {"name": "10. Magha", "sanskrit": "Magha", "devanagari": "मघा", "lord": "Ketu", "remainder": 0, "deity": "Pitrs", "start_degree": 120.0, "end_degree": 133.3333, "padas": ["Aries", "Taurus", "Gemini", "Cancer"], "syllables": ["मा (Ma)", "मी (Mi)", "मू (Mu)", "मे (Me)"]},
            {"name": "11. Purva Phalguni", "sanskrit": "Purva Phalguni", "devanagari": "पूर्व फाल्गुनी", "lord": "Venus", "remainder": 1, "deity": "Bhaga", "start_degree": 133.3333, "end_degree": 146.6666, "padas": ["Leo", "Virgo", "Libra", "Scorpio"], "syllables": ["मो (Mo)", "टा (Ta)", "टी (Ti)", "टू (Tu)"]},
            {"name": "12. Uttara Phalguni", "sanskrit": "Uttara Phalguni", "devanagari": "उत्तर फाल्गुनी", "lord": "Sun", "remainder": 2, "deity": "Aryaman", "start_degree": 146.6666, "end_degree": 160.0, "padas": ["Sagittarius", "Capricorn", "Aquarius", "Pisces"], "syllables": ["टे (Te)", "टो (To)", "पा (Pa)", "पी (Pi)"]},
            {"name": "13. Hasta", "sanskrit": "Hasta", "devanagari": "हस्त", "lord": "Moon", "remainder": 3, "deity": "Savitar", "start_degree": 160.0, "end_degree": 173.3333, "padas": ["Aries", "Taurus", "Gemini", "Cancer"], "syllables": ["पू (Pu)", "ष (Sha)", "ण (Na)", "ठ (Tha)"]},
            {"name": "14. Chitra", "sanskrit": "Chitra", "devanagari": "चित్రా", "lord": "Mars", "remainder": 4, "deity": "Tvashtar", "start_degree": 173.3333, "end_degree": 186.6666, "padas": ["Leo", "Virgo", "Libra", "Scorpio"], "syllables": ["पे (Pe)", "पो (Po)", "रा (Ra)", "री (Ri)"]},
            {"name": "15. Swati", "sanskrit": "Swati", "devanagari": "स्वाति", "lord": "Rahu", "remainder": 5, "deity": "Vayu", "start_degree": 186.6666, "end_degree": 200.0, "padas": ["Sagittarius", "Capricorn", "Aquarius", "Pisces"], "syllables": ["रू (Ru)", "रे (Re)", "रो (Ro)", "ता (Ta)"]},
            {"name": "16. Vishakha", "sanskrit": "Vishakha", "devanagari": "विशाखा", "lord": "Jupiter", "remainder": 6, "deity": "Indra-Agni", "start_degree": 200.0, "end_degree": 213.3333, "padas": ["Aries", "Taurus", "Gemini", "Cancer"], "syllables": ["ती (Ti)", "तू (Tu)", "ते (Te)", "तो (To)"]},
            {"name": "17. Anuradha", "sanskrit": "Anuradha", "devanagari": "अनुराधा", "lord": "Saturn", "remainder": 7, "deity": "Mitra", "start_degree": 213.3333, "end_degree": 226.6666, "padas": ["Leo", "Virgo", "Libra", "Scorpio"], "syllables": ["ना (Na)", "नी (Ni)", "नू (Nu)", "ने (Ne)"]},
            {"name": "18. Jyestha", "sanskrit": "Jyestha", "devanagari": "ज्येष्ठा", "lord": "Mercury", "remainder": 8, "deity": "Indra", "start_degree": 226.6666, "end_degree": 240.0, "padas": ["Sagittarius", "Capricorn", "Aquarius", "Pisces"], "syllables": ["नो (No)", "या (Ya)", "यी (Yi)", "यू (Yu)"]},
            {"name": "19. Mula", "sanskrit": "Mula", "devanagari": "मूल", "lord": "Ketu", "remainder": 0, "deity": "Nirriti", "start_degree": 240.0, "end_degree": 253.3333, "padas": ["Aries", "Taurus", "Gemini", "Cancer"], "syllables": ["ये (Ye)", "यो (Yo)", "भा (Bha)", "भी (Bhi)"]},
            {"name": "20. Purva Ashadha", "sanskrit": "Purva Ashadha", "devanagari": "पूर्वाषाढ़ा", "lord": "Venus", "remainder": 1, "deity": "Apas", "start_degree": 253.3333, "end_degree": 266.6666, "padas": ["Leo", "Virgo", "Libra", "Scorpio"], "syllables": ["भू (Bhu)", "धा (Dha)", "फा (Pha)", "ढा (Dha)"]},
            {"name": "21. Uttara Ashadha", "sanskrit": "Uttara Ashadha", "devanagari": "उत्तराषाढ़ा", "lord": "Sun", "remainder": 2, "deity": "Vishvadevas", "start_degree": 266.6666, "end_degree": 280.0, "padas": ["Sagittarius", "Capricorn", "Aquarius", "Pisces"], "syllables": ["भे (Bhe)", "भो (Bho)", "जा (Ja)", "जी (Ji)"]},
            {"name": "22. Shravana", "sanskrit": "Shravana", "devanagari": "श्रवण", "lord": "Moon", "remainder": 3, "deity": "Vishnu", "start_degree": 280.0, "end_degree": 293.3333, "padas": ["Aries", "Taurus", "Gemini", "Cancer"], "syllables": ["खी (Khi)", "खू (Khu)", "खे (Khe)", "खो (Kho)"]},
            {"name": "23. Dhanishta", "sanskrit": "Dhanishta", "devanagari": "धनिष्ठा", "lord": "Mars", "remainder": 4, "deity": "Ashta Vasus", "start_degree": 293.3333, "end_degree": 306.6666, "padas": ["Leo", "Virgo", "Libra", "Scorpio"], "syllables": ["गा (Ga)", "गी (Gi)", "गू (Gu)", "गे (Ge)"]},
            {"name": "24. Shatabhisha", "sanskrit": "Shatabhisha", "devanagari": "शतभिषा", "lord": "Rahu", "remainder": 5, "deity": "Varuna", "start_degree": 306.6666, "end_degree": 320.0, "padas": ["Sagittarius", "Capricorn", "Aquarius", "Pisces"], "syllables": ["गो (Go)", "सा (Sa)", "सी (Si)", "सू (Su)"]},
            {"name": "25. Purva Bhadrapada", "sanskrit": "Purva Bhadrapada", "devanagari": "पूर्व भाद्रपद", "lord": "Jupiter", "remainder": 6, "deity": "Aja Ekapada", "start_degree": 320.0, "end_degree": 333.3333, "padas": ["Aries", "Taurus", "Gemini", "Cancer"], "syllables": ["से (Se)", "सो (So)", "दा (Da)", "दी (Di)"]},
            {"name": "26. Uttara Bhadrapada", "sanskrit": "Uttara Bhadrapada", "devanagari": "उत्तर भाद्रपद", "lord": "Saturn", "remainder": 7, "deity": "Ahir Budhnya", "start_degree": 333.3333, "end_degree": 346.6666, "padas": ["Leo", "Virgo", "Libra", "Scorpio"], "syllables": ["दू (Du)", "थ (Tha)", "झ (Jha)", "ञ (Na)"]},
            {"name": "27. Revati", "sanskrit": "Revati", "devanagari": "रेवती", "lord": "Mercury", "remainder": 8, "deity": "Pushan", "start_degree": 346.6666, "end_degree": 360.0, "padas": ["Sagittarius", "Capricorn", "Aquarius", "Pisces"], "syllables": ["दे (De)", "दो (Do)", "चा (Cha)", "ची (Chi)"]},
        ]

    @staticmethod
    def get_all_rashis() -> List[Dict[str, str]]:
        """
        Returns a list of all 12 Rashis (Zodiac Signs) with their
        key attributes (lord, element, modality).

        Returns:
            list: A list of dictionaries, where each dictionary is a rashi.
        """
        return [
            # ... (Full rashi data as provided in the original code) ...
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
    The analytical core of the application.

    This class holds the "brains" of the astrological analysis. It contains
    a knowledge base of interpretive text derived from classical principles.
    It generates dynamic, context-aware analysis for planets in signs,
    houses, and divisional charts.
    """

    # Class-level constants for combustion orbs (in degrees)
    DEFAULT_COMBUSTION_ORB: float = 8.5
    COMBUSTION_ORBS_SPECIAL: Dict[str, float] = {
        "Venus": 8.0,
        "Mercury_Direct": 14.0,
        "Mercury_Retrograde": 12.0
    }

    def __init__(self, app_instance: 'AstroVighatiElite') -> None:
        """
        Args:
            app_instance (AstroVighatiElite): A reference to the main app.
        """
        self.app = app_instance

    def get_planet_in_house_analysis(self, planet_name: str, house_num: int, varga_num: int = 1) -> str:
        """
        Provides a contextual interpretation for a planet in a specific house,
        dynamically tailored to the Varga chart being analyzed.

        Args:
            planet_name (str): The name of the planet (e.g., "Mars").
            house_num (int): The house number (1-12).
            varga_num (int): The varga number (1 for D1, 9 for D9, etc.).

        Returns:
            str: A formatted string analyzing this specific placement.
        """
        # 1. Get the name of the Varga chart (e.g., "D9 - Navamsa Chart")
        varga_key = f"D{varga_num}"
        varga_info = EnhancedAstrologicalData.get_varga_descriptions().get(varga_key, {})
        # Fallback for keys that are formatted like "D1 - Rashi"
        if not varga_info:
            # Search for keys starting with the varga_key
            for key, info in EnhancedAstrologicalData.get_varga_descriptions().items():
                if key.startswith(varga_key):
                    varga_info = info
                    break
                    
        varga_context = varga_info.get("title", f"D{varga_num} chart")


        # 2. Get the general meaning of the house
        house_significations: Dict[int, str] = {
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

        # 3. Get the specific domain of the Varga
        varga_domain: Dict[int, str] = {
            1: "life in general", 2: "matters of wealth", 3: "siblings and courage", 4: "property and comfort",
            5: "fame and authority", 6: "health and conflicts", 7: "children and creativity", 9: "dharma and marriage",
            10: "career and actions", 12: "parents and lineage", 16: "vehicles and pleasures", 20: "spiritual pursuits",
            24: "education and learning", 30: "misfortunes and character", 40: "maternal karma", 45: "paternal karma", 60: "past karma"
        }

        # 4. Get the core nature of the planet
        planet_nature: Dict[str, str] = {
            "Sun": "authority, soul, and leadership", "Moon": "emotions, mind, and nurturing",
            "Mars": "energy, action, and conflict", "Mercury": "intellect, communication, and analysis",
            "Jupiter": "wisdom, expansion, and fortune", "Venus": "love, harmony, and luxury",
            "Saturn": "discipline, structure, and karma", "Rahu": "obsession, ambition, and foreign influences",
            "Ketu": "detachment, spirituality, and intuition"
        }

        # 5. Build the final interpretation string
        domain_text = varga_domain.get(varga_num, "this area of life")
        house_text = house_significations.get(house_num, "an unknown area")
        planet_text = planet_nature.get(planet_name, "its inherent energy")

        # Get correct suffix (1st, 2nd, 3rd, 4th...)
        house_suffix = "th"
        if house_num in [1, 21, 31]: house_suffix = "st"
        elif house_num in [2, 22]: house_suffix = "nd"
        elif house_num in [3, 23]: house_suffix = "rd"

        return (f"In {varga_context}, the placement of **{planet_name}** in the "
                f"**{house_num}{house_suffix} house** influences '{house_text}' "
                f"within the domain of **{domain_text}**. This indicates that the "
                f"native's {planet_text} will strongly manifest in these specific matters.")

    def get_planet_in_sign_analysis(self, planet_name: str, sign_name: str) -> str:
        """
        Provides a basic interpretation for a planet in a specific sign
        by comparing their elemental natures.

        Args:
            planet_name (str): The name of the planet (e.g., "Sun").
            sign_name (str): The name of the sign (e.g., "Aries").

        Returns:
            str: A formatted string analyzing this placement.
        """
        planet_data = next((p for p in EnhancedAstrologicalData.get_all_planets() if p['name'] == planet_name), None)
        sign_data = next((r for r in EnhancedAstrologicalData.get_all_rashis() if r['name'] == sign_name), None)

        if not planet_data or not sign_data:
            return "Analysis not available."

        planet_element = planet_data.get("element")
        sign_element = sign_data.get("tattva")
        modality = sign_data.get("modality")

        # Compare elements to find harmony or tension
        harmony = "harmoniously"
        if planet_element is None: # For nodes Rahu/Ketu
            harmony = "uniquely"
        elif planet_element != sign_element:
            harmony = "with some tension, requiring adaptation"

        # Safely access significations, providing a fallback
        significations = planet_data.get('significations', [])
        sig1 = significations[0].lower() if significations else "its primary function"
        sig2 = significations[1].lower() if len(significations) > 1 else "its secondary function"


        return (f"**{planet_name}** in **{sign_name}**: The {planet_element} nature of "
                f"{planet_name} interacts with the {sign_element}, {modality} "
                f"nature of {sign_name}. This placement suggests that the "
                f"planet's energies will express themselves {harmony}. The native will "
                f"approach {sig1} and "
                f"{sig2} with the qualities of "
                f"{sign_data.get('description', '').lower().replace('represents', '').strip()}")

    def get_special_state_analysis(self, planet_name: str, speed: float, sun_longitude: float, planet_longitude: float) -> str:
        """
        Checks for and interprets special planetary states like
        Retrograde (Vakri) and Combust (Asta).

        Args:
            planet_name (str): The name of the planet.
            speed (float): The planet's speed (negative if retrograde).
            sun_longitude (float): The D1 longitude of the Sun.
            planet_longitude (float): The D1 longitude of the planet.

        Returns:
            str: A formatted string describing any special states, or "" if none.
        """
        analysis: List[str] = []

        # 1. Retrograde Check
        if speed < 0:
            analysis.append(f"**{planet_name} is Retrograde (Vakri)**: This indicates that the planet's energies are turned inward. It may cause delays, introspection, or an unconventional approach to the planet's significations. It often brings karmic matters to the forefront for resolution.")

        # 2. Combustion Check
        if planet_name not in ["Sun", "Rahu", "Ketu"]:
            # Set the 'orb' or distance for combustion, which varies by planet
            combustion_orb = self.DEFAULT_COMBUSTION_ORB
            if planet_name == "Venus":
                combustion_orb = self.COMBUSTION_ORBS_SPECIAL["Venus"]
            elif planet_name == "Mercury":
                combustion_orb = self.COMBUSTION_ORBS_SPECIAL["Mercury_Direct"] if speed > 0 else self.COMBUSTION_ORBS_SPECIAL["Mercury_Retrograde"]

            # Find the absolute distance between the planet and the Sun
            separation = abs(planet_longitude - sun_longitude)
            # Handle the 360-degree wrap-around
            if separation > 180:
                separation = 360 - separation

            if separation <= combustion_orb:
                analysis.append(f"**{planet_name} is Combust (Asta)**: Being very close to the Sun, its significations are 'burnt' or overpowered by the Sun's ego and authority. This can weaken the planet's ability to give independent results, making its expression dependent on the Sun's agenda.")

        return "\n".join(analysis) if analysis else ""

    def get_conjunction_analysis(self, planets_in_house: List[Dict[str, Any]]) -> str:
        """
        Provides interpretation for planetary conjunctions (yogas)
        when two or more planets are in the same house.

        Args:
            planets_in_house (list): A list of planet data dictionaries.

        Returns:
            str: A formatted string analyzing the conjunction, or "" if none.
        """
        if len(planets_in_house) < 2:
            return ""

        planet_names = sorted([p['name'] for p in planets_in_house])

        # A simple knowledge base for common conjunctions
        conjunction_kb: Dict[Tuple[str, ...], str] = {
            # This is a "tuple" (immutable list) used as a dictionary key.
            # Order matters, so we use the sorted 'planet_names' list.
            ('Mercury', 'Sun'): "This forms **Budha-Aditya Yoga**, a combination for sharp intellect, communication skills, and success in academic or commercial fields. The person is often learned and respected.",
            ('Mars', 'Saturn'): "A challenging conjunction of two powerful malefics. It can give immense discipline and drive for technical fields but may also bring frustration, accidents, or conflict. It requires careful channeling of energy.",
            ('Jupiter', 'Venus'): "A conjunction of the two Gurus (teachers). It can give great knowledge, wealth, and refinement. However, as they are natural enemies, it can sometimes lead to conflicts in ideology or relationships.",
            ('Moon', 'Saturn'): "This forms **Punarphoo Dosha** or **Vish Yoga** (Poison Yoga). It can cause moodiness, depression, delays, and obstacles. It is a karmic combination that teaches patience and detachment through emotional hardship."
            # More combinations can be (and should be) added here
        }

        analysis = [f"**Conjunction in this house:** The presence of {', '.join(planet_names)} together creates a powerful fusion of energies."]

        # Check all possible pairs in the conjunction
        for i in range(len(planet_names)):
            for j in range(i + 1, len(planet_names)):
                pair = (planet_names[i], planet_names[j])
                if pair in conjunction_kb:
                    analysis.append(conjunction_kb[pair])

        return "\n".join(analysis)

#===================================================================================================
# ASTRONOMICAL & VARGA CALCULATORS
#===================================================================================================
class AstronomicalCalculator:
    """
    Handles all core astronomical calculations using the Swiss Ephemeris.

    This is the "engine" of the application. It takes a date, time, and
    location, and calculates the precise, accurate Sidereal (Lahiri)
    positions of all planets and the Ascendant.
    """
    def __init__(self, ayanamsa: str = 'LAHIRI') -> None:
        """
        Args:
            ayanamsa (str, optional): The Ayanamsa (zodiacal correction) to use.
                Defaults to 'LAHIRI'.
        """
        if SWISSEPH_AVAILABLE:
            try:
                # `swe.set_ephe_path(None)` tells Swiss Ephemeris to use its
                # built-in ephemeris files.
                swe.set_ephe_path(None)

                # Get the internal code for the chosen Ayanamsa
                ayanamsa_code = getattr(swe, f'SIDM_{ayanamsa}')

                # Set the Ayanamsa mode for all future calculations
                swe.set_sid_mode(ayanamsa_code)
                print(f"✅ AstronomicalCalculator initialized with {ayanamsa} Ayanamsa.")
            except Exception as e:
                print(f"⚠️ Error initializing Swiss Ephemeris: {e}")
                messagebox.showerror("Initialization Error", f"Could not set Swiss Ephemeris Ayanamsa mode: {e}")

    def calculate_planet_positions(self, dt_local: datetime, lat: float, lon: float, timezone_offset: float) -> Optional[Dict[str, Dict[str, Any]]]:
        """
        Calculates the Sidereal (Lahiri) positions for all planets and the Ascendant.

        Args:
            dt_local (datetime): The user's local birth date and time.
            lat (float): Latitude of the birth location.
            lon (float): Longitude of the birth location.
            timezone_offset (float): The UTC offset (e.g., 5.5 for India).

        Returns:
            Optional[Dict[str, Dict[str, Any]]]: A dictionary where keys are
            planet names ("Sun", "Moon", etc.) and values are dictionaries
            of their positional data. Returns None if calculation fails.
        """
        if not SWISSEPH_AVAILABLE:
            messagebox.showerror("Dependency Missing", "The 'pyswisseph' library is required for accurate calculations.")
            return None
        try:
            # 1. Convert local time to UTC, which is required by swisseph
            dt_utc = dt_local - timedelta(hours=timezone_offset)

            # 2. Convert UTC datetime to Julian Day number
            #    The '1' means Gregorian calendar.
            jd_utc = swe.utc_to_jd(dt_utc.year, dt_utc.month, dt_utc.day, dt_utc.hour, dt_utc.minute, dt_utc.second, 1)[1]

            # 3. Define the planets we need to calculate
            planet_codes: Dict[str, int] = {
                "Sun": swe.SUN, "Moon": swe.MOON, "Mercury": swe.MERCURY,
                "Venus": swe.VENUS, "Mars": swe.MARS, "Jupiter": swe.JUPITER,
                "Saturn": swe.SATURN, "Rahu": swe.MEAN_NODE, # Rahu is the "Mean Node"
            }
            positions: Dict[str, Dict[str, Any]] = {}

            # 4. Calculate the Ascendant (Lagna)
            #    'b'P'' specifies the Placidus house system (standard for Ascendant).
            _, ascmc = swe.houses(jd_utc, lat, lon, b'P')
            asc_longitude = ascmc[0] # The first value returned is the Ascendant
            positions['Ascendant'] = self._process_longitude(asc_longitude)
            positions['Ascendant']['speed'] = 0.0 # Ascendant doesn't have speed

            # 5. Calculate positions for all other planets
            for name, code in planet_codes.items():
                # `swe.calc_ut` calculates for a specific Julian Day in UTC.
                # `swe.FLG_SWIEPH | swe.FLG_SIDEREAL` are flags that tell it
                # to use high-precision ephemeris and the Sidereal mode we set.
                planet_pos_data = swe.calc_ut(jd_utc, code, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)[0]

                planet_longitude = planet_pos_data[0]
                planet_speed = planet_pos_data[3]

                # Process the raw longitude into a useful data dictionary
                positions[name] = self._process_longitude(planet_longitude)
                positions[name]['speed'] = planet_speed

            # 6. Calculate Ketu (South Node)
            #    Ketu is always exactly 180 degrees opposite Rahu.
            rahu_longitude = positions['Rahu']['longitude']
            ketu_longitude = (rahu_longitude + 180) % 360 # % 360 handles wrap-around
            positions['Ketu'] = self._process_longitude(ketu_longitude)
            # Ketu's speed is the same as Rahu's, but in the opposite direction
            positions['Ketu']['speed'] = positions['Rahu'].get('speed', 0) * -1

            return positions

        except swe.Error as e:
            messagebox.showerror("Swiss Ephemeris Error", f"A calculation error occurred:\n\n{e}")
            return None
        except Exception as e:
            messagebox.showerror("Calculation Error", f"An unexpected error occurred during calculation:\n\n{e}")
            return None

    def _process_longitude(self, longitude: float) -> Dict[str, Any]:
        """
        A private helper function to convert a raw 360-degree longitude
        into a meaningful dictionary of astrological data (Rashi, Nakshatra, etc.).

        Args:
            longitude (float): A longitude from 0.0 to 359.99...

        Returns:
            dict: A dictionary containing Rashi, degree, Nakshatra, etc.
        """
        # 1. Find Rashi
        #    Each Rashi is 30 degrees. 0-30 = Aries, 30-60 = Taurus, etc.
        rashi_index = int(longitude / 30)
        rashi_num = rashi_index + 1 # Astrologers use 1-12, not 0-11
        rashi_name = EnhancedAstrologicalData.SIGNS[rashi_num]

        # 2. Find Degree within Rashi
        #    The modulo operator `%` gives the remainder.
        degree_in_rashi = longitude % 30

        # 3. Find Nakshatra
        nakshatra_name = "Unknown"
        nakshatra_lord = "N/A"
        for nak in EnhancedAstrologicalData.get_all_nakshatras():
            start_deg = nak['start_degree']
            end_deg = nak['end_degree']

            # This logic handles the 360/0 degree wrap-around
            # (e.g., for Revati, which starts at 346.66 and ends at 360/0)
            if start_deg > end_deg: # This is the wrap-around case
                if longitude >= start_deg or longitude < end_deg:
                    nakshatra_name = nak['name']
                    nakshatra_lord = nak['lord']
                    break
            else: # This is the normal case
                if start_deg <= longitude < end_deg:
                    nakshatra_name = nak['name']
                    nakshatra_lord = nak['lord']
                    break

        # 4. Format for display
        dms_str = decimal_to_dms(degree_in_rashi)

        return {
            'longitude': longitude,        # e.g., 45.0
            'rashi': rashi_name,           # e.g., "Taurus"
            'rashi_num': rashi_num,        # e.g., 2
            'degree_in_rashi': degree_in_rashi, # e.g., 15.0
            'nakshatra': nakshatra_name,   # e.g., "Rohini"
            'nakshatra_lord': nakshatra_lord, # e.g., "Moon"
            'dms': dms_str                 # e.g., "15° 00' 00""
        }

class VargaCalculator:
    """
    Calculates all Divisional (Varga) charts based on mathematical
    rules from classical Vedic astrology (Parashari system).

    This class takes a D1 (Rashi) position and a Varga number (e.g., 9 for D9)
    and computes the planet's corresponding position in that Varga chart.
    """
    def __init__(self) -> None:
        # A static list of the 60 deities for the D60 chart calculation
        self.D60_DEITIES: Tuple[str, ...] = (
            "Ghora","Rakshasa","Deva","Kubera","Yaksha","Kinnara","Bhrashta","Kulaghna",
            "Garala","Vahni","Maya","Puriihaka","Apampathi","Marutwana","Kaala","Sarpa",
            "Amrita","Indu","Mridu","Komala","Heramba","Brahma","Vishnu","Maheshwara",
            "Deva","Ardra","Kalinasa","Kshiteesa","Kamalakara","Gulika","Mrityu","Kaala",
            "Davagni","Ghora","Yama","Kantaka","Sudha","Amrita","Poorna","VishaDagdha",
            "Kulanasa","Vamshakshya","Utpata","Kaala","Saumya","Komala","Seetala",
            "Karaladamshtra","Chandramukhi","Praveena","Kaalpavaka","Dandayudha","Nirmala",
            "Saumya","Kroora","Atisheetala","Amrita","Payodhi","Bhramana","Chandrarekha"
        )

    def calculate_varga_position(self, varga_num: int, d1_longitude_in_sign: float, d1_sign_num: int) -> Tuple[int, float, str]:
        """
        Main dispatcher function for Varga calculations.

        Args:
            varga_num (int): The D-chart number (e.g., 1, 2, 9, 10).
            d1_longitude_in_sign (float): The degree *within* the sign (0-30).
            d1_sign_num (int): The Rashi number (1-12).

        Returns:
            tuple: (new_sign_num, new_longitude_in_sign, details_string)
        """
        lon_in_sign = d1_longitude_in_sign
        sign = d1_sign_num
        new_sign: int = 1
        new_lon: float = 0.0

        if varga_num == 1:
            # D1 is just the Rashi chart, so no change.
            return sign, lon_in_sign, ""

        elif varga_num == 2: # D2 Hora (Wealth)
            division_size = 15  # Each sign (30°) is split into 2 Horas of 15°
            amsa = math.floor(lon_in_sign / division_size) # 0 or 1
            new_lon = (lon_in_sign % division_size) * 2 # Stretch 15° back to 30°
            # Odd signs (1, 3, 5...): 1st Hora is Sun (Leo), 2nd is Moon (Cancer)
            # Even signs (2, 4, 6...): 1st Hora is Moon (Cancer), 2nd is Sun (Leo)
            if (EnhancedAstrologicalData.SIGN_NATURE[sign] == 'Odd' and amsa == 0) or \
               (EnhancedAstrologicalData.SIGN_NATURE[sign] == 'Even' and amsa == 1):
                return 5, new_lon, "Sun's Hora" # Leo
            else:
                return 4, new_lon, "Moon's Hora" # Cancer

        elif varga_num == 3: # D3 Drekkana (Siblings)
            division_size = 10 # 3 divisions of 10°
            amsa = math.floor(lon_in_sign / division_size) # 0, 1, or 2
            new_lon = (lon_in_sign % division_size) * 3 # Stretch 10° back to 30°
            # 1st Drekkana (0-10°): Stays in the same sign
            # 2nd Drekkana (10-20°): Goes to the 5th sign from it
            # 3rd Drekkana (20-30°): Goes to the 9th sign from it
            offset = [0, 4, 8][amsa] # 0 = 1st, 4 = 5th, 8 = 9th
            new_sign = (sign + offset - 1) % 12 + 1
            return new_sign, new_lon, ""

        elif varga_num == 4: # D4 Chaturthamsa (Property)
            division_size = 7.5 # 4 divisions of 7.5°
            amsa = math.floor(lon_in_sign / division_size) # 0, 1, 2, or 3
            new_lon = (lon_in_sign % division_size) * 4 # Stretch 7.5° back to 30°
            # Signs are 1st, 4th, 7th, 10th from the original
            offset = [0, 3, 6, 9][amsa]
            new_sign = (sign + offset - 1) % 12 + 1
            return new_sign, new_lon, ""

        elif varga_num == 7: # D7 Saptamsa (Children)
            division_size = 30 / 7 # 7 divisions
            amsa = math.floor(lon_in_sign / division_size) # 0-6
            new_lon = (lon_in_sign % division_size) * 7
            # Odd signs: Counting starts from the sign itself
            if EnhancedAstrologicalData.SIGN_NATURE[sign] == 'Odd':
                new_sign = (sign + amsa - 1) % 12 + 1
            # Even signs: Counting starts from the 7th sign from it
            else:
                new_sign = (sign + 6 + amsa - 1) % 12 + 1
            return new_sign, new_lon, ""

        elif varga_num == 9: # D9 Navamsa (Spouse, Dharma)
            division_size = 30 / 9 # 9 divisions of 3° 20'
            amsa = math.floor(lon_in_sign / division_size) # 0-8
            new_lon = (lon_in_sign % division_size) * 9
            # Fiery signs (1, 5, 9): Start counting from Aries (1)
            # Earthy signs (2, 6, 10): Start counting from Capricorn (10)
            # Airy signs (3, 7, 11): Start counting from Libra (7)
            # Watery signs (4, 8, 12): Start counting from Cancer (4)
            rashi_type = (sign - 1) % 4  # 0:Fiery, 1:Earthy, 2:Airy, 3:Watery
            start_sign = [1, 10, 7, 4][rashi_type]
            new_sign = (start_sign + amsa - 1) % 12 + 1
            return new_sign, new_lon, ""

        elif varga_num == 10: # D10 Dasamsa (Career)
            division_size = 3 # 10 divisions of 3°
            amsa = math.floor(lon_in_sign / division_size) # 0-9
            new_lon = (lon_in_sign % division_size) * 10
            # Odd signs: Counting starts from the sign itself
            if EnhancedAstrologicalData.SIGN_NATURE[sign] == 'Odd':
                new_sign = (sign + amsa - 1) % 12 + 1
            # Even signs: Counting starts from the 9th sign from it
            else:
                new_sign = (sign + 8 + amsa - 1) % 12 + 1
            return new_sign, new_lon, ""

        elif varga_num == 12: # D12 Dwadasamsa (Parents)
            division_size = 2.5 # 12 divisions of 2.5°
            amsa = math.floor(lon_in_sign / division_size) # 0-11
            new_lon = (lon_in_sign % division_size) * 12
            # Counting always starts from the sign itself
            new_sign = (sign + amsa - 1) % 12 + 1
            return new_sign, new_lon, ""

        elif varga_num == 16: # D16 Shodasamsa (Vehicles)
            division_size = 30 / 16
            amsa = math.floor(lon_in_sign / division_size) # 0-15
            new_lon = (lon_in_sign % division_size) * 16
            # Movable signs (1, 4, 7, 10): Start from Aries
            # Fixed signs (2, 5, 8, 11): Start from Leo
            # Dual signs (3, 6, 9, 12): Start from Sagittarius
            modality_type = (sign - 1) % 3 # 0:Movable, 1:Fixed, 2:Dual
            start_sign = [1, 5, 9][modality_type]
            new_sign = (start_sign + amsa - 1) % 12 + 1
            return new_sign, new_lon, ""

        elif varga_num == 20: # D20 Vimsamsa (Spiritual)
            division_size = 1.5
            amsa = math.floor(lon_in_sign / division_size) # 0-19
            new_lon = (lon_in_sign % division_size) * 20
            # Movable signs: Start from Aries
            # Fixed signs: Start from Sagittarius
            # Dual signs: Start from Leo
            modality_type = (sign - 1) % 3
            start_sign = [1, 9, 5][modality_type]
            new_sign = (start_sign + amsa - 1) % 12 + 1
            return new_sign, new_lon, ""

        elif varga_num == 24: # D24 Siddhamsa (Education)
            division_size = 1.25
            amsa = math.floor(lon_in_sign / division_size) # 0-23
            new_lon = (lon_in_sign % division_size) * 24
            # Odd signs: Start from Leo
            # Even signs: Start from Cancer
            start_sign = 5 if EnhancedAstrologicalData.SIGN_NATURE[sign] == 'Odd' else 4
            new_sign = (start_sign + amsa - 1) % 12 + 1
            return new_sign, new_lon, ""

        elif varga_num == 30: # D30 Trimsamsa (Misfortunes)
            # This varga has irregular, pre-defined divisions
            if EnhancedAstrologicalData.SIGN_NATURE[sign] == 'Odd':
                if 0 <= lon_in_sign < 5: new_sign = 1   # Aries (Mars)
                elif 5 <= lon_in_sign < 10: new_sign = 11 # Aquarius (Saturn)
                elif 10 <= lon_in_sign < 18: new_sign = 9 # Sagittarius (Jupiter)
                elif 18 <= lon_in_sign < 25: new_sign = 3 # Gemini (Mercury)
                else: new_sign = 7 # Libra (Venus)
            else: # Even signs
                if 0 <= lon_in_sign < 5: new_sign = 2 # Taurus (Venus)
                elif 5 <= lon_in_sign < 12: new_sign = 6 # Virgo (Mercury)
                elif 12 <= lon_in_sign < 20: new_sign = 12 # Pisces (Jupiter)
                elif 20 <= lon_in_sign < 25: new_sign = 10 # Capricorn (Saturn)
                else: new_sign = 8 # Scorpio (Mars)
            # Longitude in Trimsamsa is symbolic; only the sign matters.
            return new_sign, 0.0, ""

        elif varga_num == 60: # D60 Shashtyamsa (Past Karma)
            # This is a very sensitive chart.
            # 60 divisions of 0.5° (30') each
            amsa_index = math.floor(d1_longitude_in_sign * 2) # 0-59
            if amsa_index >= 60: amsa_index = 59
            new_lon = (d1_longitude_in_sign * 2 % 1) * 30 # Stretch 0.5° back to 30°
            # The sign progresses: 1st amsa is in the D1 sign, 2nd is in the next, etc.
            new_sign = ((sign -1 + amsa_index) % 12) + 1
            details = self.D60_DEITIES[amsa_index] # Get the deity name
            return new_sign, new_lon, details

        else: # Fallback for other Vargas (e.g., D5, D6, D40, D45)
            # This is a generic "Parashara" rule
            division_size = 30 / varga_num
            amsa = math.floor(lon_in_sign / division_size)
            new_lon = (lon_in_sign % division_size) * varga_num
            # Counting always starts from the sign itself
            new_sign = (sign + amsa - 1) % 12 + 1
            return new_sign, new_lon, ""


#===================================================================================================
# THEME MANAGER
#===================================================================================================
class EnhancedThemeManager:
    """
    Manages the visual styling (themes) of the entire application.

    This class holds a dictionary of color themes and a static method
    `apply_theme` that can re-style all GUI widgets on the fly.
    """

    # A dictionary of all available themes
    THEMES: Dict[str, Dict[str, str]] = {
        "Cosmic Dark": {
            "bg_dark": "#0D1B2A", "bg_light": "#E0E1DD", "accent": "#FF6B35",
            "neutral": "#1B263B", "success": "#06FFA5", "chart_bg": "#1B263B"
        },
        "Crimson Mystique": {
            "bg_dark": "#2c3e50", "bg_light": "#ecf0f1", "accent": "#e74c3c",
            "neutral": "#34495e", "success": "#27ae60", "chart_bg": "#34495e"
        },
        # ... (All other theme dictionaries remain unchanged) ...
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
    def apply_theme(app: 'AstroVighatiElite', theme_name: str) -> None:
        """
        Applies a full visual theme to the application.

        Args:
            app (AstroVighatiElite): The main application instance.
            theme_name (str): The name of the theme to apply (e.g., "Cosmic Dark").
        """
        theme = EnhancedThemeManager.THEMES.get(theme_name, EnhancedThemeManager.THEMES["Cosmic Dark"])
        app.current_theme_data = theme

        style = ttk.Style()
        style.theme_use('clam') # 'clam' is a good, modern-looking base theme

        # --- Extract theme colors ---
        bg_dark = theme["bg_dark"]
        bg_light = theme["bg_light"]
        accent = theme["accent"]
        neutral = theme["neutral"]

        # --- Logic for Light vs. Dark themes ---
        is_light_theme = theme_name == "Classic Light"
        fg_color = bg_light if not is_light_theme else bg_dark
        main_bg_color = bg_dark if not is_light_theme else bg_light
        widget_bg_color = neutral if not is_light_theme else "#FFFFFF"
        select_fg_color = bg_dark if not is_light_theme else bg_light # Text color on a selected item

        # --- Apply styles to all widget types ---

        # Root window and default for all widgets
        app.root.configure(bg=main_bg_color)
        style.configure('.', background=main_bg_color, foreground=fg_color, font=('Segoe UI', 10))

        # Frames and Labels
        style.configure('TFrame', background=main_bg_color)
        style.configure('TLabel', background=main_bg_color, foreground=fg_color)
        style.configure('Heading.TLabel', font=('Segoe UI', 12, 'bold'), foreground=accent)
        style.configure('Title.TLabel', font=('Segoe UI', 16, 'bold'), foreground=accent)

        # Notebook (Tabs)
        style.configure('TNotebook', background=main_bg_color, borderwidth=0)
        style.configure('TNotebook.Tab', background=neutral, foreground=fg_color, padding=[15, 8], font=('Segoe UI', 10, 'bold'))
        style.map('TNotebook.Tab', background=[('selected', accent)], foreground=[('selected', select_fg_color)])

        # PanedWindow (Dividers)
        # Define base style for TPanedWindow, it applies to both orientations
        style.configure('TPanedwindow', background=main_bg_color)
        # You can optionally define specific styles, but the base is usually enough
        # style.configure('Vertical.TPanedwindow', background=main_bg_color)
        # style.configure('Horizontal.TPanedwindow', background=main_bg_color)


        # Labelframes (the containers with titles)
        style.configure('TLabelframe', background=main_bg_color, bordercolor=accent, relief='groove')
        style.configure('TLabelframe.Label', background=main_bg_color, foreground=accent, font=('Segoe UI', 11, 'bold'))

        # Buttons
        style.configure('TButton', background=neutral, foreground=fg_color, font=('Segoe UI', 10, 'bold'), borderwidth=1, relief='flat', padding=10)
        style.map('TButton', background=[('active', accent)], foreground=[('active', select_fg_color)])
        style.configure('Accent.TButton', background=accent, foreground=select_fg_color, font=('Segoe UI', 12, 'bold'), padding=12)
        style.map('Accent.TButton', background=[('active', bg_light)], foreground=[('active', bg_dark)])

        # Entry and Spinbox
        style.configure('TEntry', fieldbackground=widget_bg_color, foreground=fg_color, insertcolor=fg_color, bordercolor=accent)
        style.map('TEntry', foreground=[('focus', fg_color)], fieldbackground=[('focus', widget_bg_color)])
        style.configure('TSpinbox', fieldbackground=widget_bg_color, foreground=fg_color, insertcolor=fg_color, arrowcolor=fg_color, bordercolor=accent)
        style.map('TSpinbox', background=[('active', neutral)])

        # Combobox (Dropdown)
        style.configure('TCombobox', fieldbackground=widget_bg_color, foreground=fg_color, selectbackground=accent, selectforeground=select_fg_color, arrowcolor=fg_color)
        style.map('TCombobox', fieldbackground=[('readonly', widget_bg_color)], selectbackground=[('readonly', accent)], foreground=[('readonly', fg_color)])
        # Style the dropdown list itself
        app.root.option_add('*TCombobox*Listbox.background', widget_bg_color)
        app.root.option_add('*TCombobox*Listbox.foreground', fg_color)
        app.root.option_add('*TCombobox*Listbox.selectBackground', accent)
        app.root.option_add('*TCombobox*Listbox.selectForeground', select_fg_color)

        # Treeview (Data tables)
        style.configure('Treeview', background=widget_bg_color, foreground=fg_color, fieldbackground=widget_bg_color, rowheight=30)
        style.configure('Treeview.Heading', background=neutral, foreground=accent, font=('Segoe UI', 11, 'bold'))
        style.map('Treeview', background=[('selected', accent)], foreground=[('selected', select_fg_color)])

        # Scrollbars
        style.configure('Vertical.TScrollbar', background=neutral, troughcolor=main_bg_color, arrowcolor=fg_color)
        style.map('Vertical.TScrollbar', background=[('active', accent)])

        # --- Apply to non-ttk widgets (ScrolledText, Listbox) ---
        # These widgets don't use ttk styles, so they must be configured manually.
        try:
            text_bg = widget_bg_color
            text_fg = fg_color
            all_tabs: List[Optional[ttk.Frame]] = [
                app.kundli_tab, app.vighati_tab, app.transit_tab,
                app.dasha_tab, app.nakshatra_tab, app.planet_tab,
                app.rashi_tab, app.yoga_tab
            ]
            for tab in all_tabs:
                if tab is None: continue # Skip tabs not yet initialized

                # Apply to all ScrolledText widgets
                for widget_name in [
                    'results_text', 'details_text', 'analysis_text', 'info_text',
                    'transit_text', 'prediction_text', 'dasha_text', 'planet_text',
                    'rashi_text', 'rajyoga_text', 'dosha_text', 'mahapurusha_text',
                    'varga_desc_text', 'syllables_text' # Added new syllables_text
                ]:
                    if hasattr(tab, widget_name):
                        widget = getattr(tab, widget_name)
                        widget.config(
                            background=text_bg, foreground=text_fg,
                            insertbackground=accent, selectbackground=accent,
                            selectforeground=select_fg_color
                        )

                # Apply to all Listbox widgets
                for widget_name in ['nak_listbox', 'rashi_listbox', 'planet_listbox']:
                    if hasattr(tab, widget_name):
                        widget = getattr(tab, widget_name)
                        widget.config(
                            background=text_bg, foreground=text_fg,
                            selectbackground=accent, selectforeground=select_fg_color
                        )
        except Exception as e:
            # This try/except is important because tabs might not be initialized
            # when the theme is first applied.
            print(f"Warning: Could not apply theme to a specific non-ttk widget. Error: {e}")

#===================================================================================================
# MAIN ELITE APPLICATION
#===================================================================================================
class AstroVighatiElite:
    """
    The main application class.

    This class is the "orchestrator" of the entire application. It:
    - Creates the main Tkinter window (`root`).
    - Initializes all core components (calculators, data, interpreters).
    - Creates the main menu, status bar, and the tabbed notebook.
    - Instantiates all the individual Tab classes.
    - Holds the central data state (`self.chart_data`) for the loaded chart.
    """

    __VERSION__ = "6.0 (Nakshatra Syllables)" # <-- VERSION BUMPED

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(f"AstroVighati Pro Elite v{self.__VERSION__} - Advanced Vedic Astrology Suite")
        self.root.geometry("1800x1000") # Set default size
        self.root.minsize(1400, 800) # Set minimum allowed size

        # --- 1. Instantiate Core Components ---
        self.astro_data = EnhancedAstrologicalData()
        self.calculator = AstronomicalCalculator()
        self.varga_calculator = VargaCalculator()
        self.interpreter = InterpretationEngine(self)

        # --- 2. Central Data State ---
        # This dictionary is the "single source of truth" for the currently
        # open chart. All other tabs (Dasha, Vighati) read from this.
        self.chart_data: Dict[str, Any] = {}

        # --- 3. Theme Management ---
        self.current_theme = tk.StringVar(value="Cosmic Dark")
        self.current_theme_data: Dict[str, str] = {}

        # --- 4. Null-initialize tabs ---
        # This is a failsafe for the theme manager, which runs *after*
        # this __init__ but *before* create_tabs() is fully done.
        self.kundli_tab: Optional[KundliGeneratorTab] = None
        self.vighati_tab: Optional[EnhancedVighatiTab] = None
        self.transit_tab: Optional[TransitCalculatorTab] = None
        self.dasha_tab: Optional[DashaTimelineTab] = None
        self.nakshatra_tab: Optional[EnhancedNakshatraTab] = None
        self.planet_tab: Optional[EnhancedPlanetTab] = None
        self.rashi_tab: Optional[EnhancedRashiTab] = None
        self.yoga_tab: Optional[YogasDoshasTab] = None

        # --- 5. UI Initialization ---
        self.create_status_bar()
        self.create_main_notebook()
        self.create_tabs()  # This will populate all the self.xxx_tab variables
        self.create_menu()

        # --- 6. Apply Initial Theme ---
        EnhancedThemeManager.apply_theme(self, self.current_theme.get())

    def create_status_bar(self) -> None:
        """Creates the status bar at the bottom of the window."""
        self.status_var = tk.StringVar(value=f"Ready - Elite Edition v{self.__VERSION__} | Sidereal Engine Active")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief='sunken', anchor='w', padding=5)
        status_bar.pack(side='bottom', fill='x')

    def create_main_notebook(self) -> None:
        """Creates the main ttk.Notebook widget that will hold all the tabs."""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill='both', padx=10, pady=(10, 0))

    def create_tabs(self) -> None:
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

    def create_menu(self) -> None:
        """Creates the main application menu bar (File, Theme, Tools, Help)."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # --- File Menu ---
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Chart", command=self.new_chart, accelerator="Ctrl+N")
        file_menu.add_command(label="Open Chart...", command=self.load_chart, accelerator="Ctrl+O")
        file_menu.add_command(label="Save Chart As...", command=self.save_chart, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # --- Theme Menu ---
        theme_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Theme", menu=theme_menu)
        for theme_name in EnhancedThemeManager.THEMES.keys():
            theme_menu.add_radiobutton(
                label=theme_name,
                variable=self.current_theme,
                command=lambda t=theme_name: self.change_theme(t)
            )

        # --- Help Menu ---
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="User Guide", command=self.show_help)
        help_menu.add_separator()
        help_menu.add_command(label="About", command=self.show_about)

        # --- Bind keyboard shortcuts ---
        # Using lambda ensures the event object is ignored
        self.root.bind("<Control-n>", lambda event: self.new_chart())
        self.root.bind("<Control-o>", lambda event: self.load_chart())
        self.root.bind("<Control-s>", lambda event: self.save_chart())


    def change_theme(self, theme_name: str) -> None:
        """Callback function to change the application's theme."""
        EnhancedThemeManager.apply_theme(self, theme_name)
        self.status_var.set(f"Theme changed to {theme_name}")

    def new_chart(self, event: Any = None) -> None:
        """Clears the current chart data and input fields."""
        # 1. Clear the central data state
        self.chart_data = {}
        # 2. Tell the Kundli tab to clear its inputs and outputs
        if self.kundli_tab:
            self.kundli_tab.clear_inputs_and_outputs()
        # 3. Switch focus to the Kundli tab
        if self.kundli_tab:
            self.notebook.select(self.kundli_tab)
        # 4. Update status bar and inform user
        self.status_var.set("Ready for new birth details.")
        messagebox.showinfo("New Chart", "All fields cleared. Ready for new birth details.")

    def save_chart(self, event: Any = None) -> None:
        """Saves the current chart data (from self.chart_data) to a JSON file."""
        if not self.chart_data:
            messagebox.showwarning("No Data", "Please generate a chart before saving.")
            return

        # Create a serializable copy of the chart data
        chart_data_to_save = self.chart_data.copy()
        if 'birth_dt_local' in chart_data_to_save and isinstance(chart_data_to_save['birth_dt_local'], datetime):
            chart_data_to_save['birth_dt_local_str'] = chart_data_to_save['birth_dt_local'].isoformat()
            del chart_data_to_save['birth_dt_local'] # Remove non-serializable datetime object

        # Ask user for save location
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("AstroVighati Chart", "*.json"), ("All Files", "*.*")],
            title="Save Chart As"
        )
        if not filepath:
            return # User cancelled

        # Write data to JSON file
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(chart_data_to_save, f, indent=4, ensure_ascii=False)
            self.status_var.set(f"Chart saved to {os.path.basename(filepath)}")
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save chart file:\n{e}")

    def load_chart(self, event: Any = None) -> None:
        """Loads chart data from a JSON file into self.chart_data."""
        filepath = filedialog.askopenfilename(
            filetypes=[("AstroVighati Chart", "*.json"), ("All Files", "*.*")],
            title="Open Chart"
        )
        if not filepath:
            return # User cancelled

        try:
            # Read JSON data from file
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Restore the datetime object
            if 'birth_dt_local_str' in data:
                data['birth_dt_local'] = datetime.fromisoformat(data['birth_dt_local_str'])

            # Update central chart data
            self.app.chart_data = data

            if not self.kundli_tab:
                raise Exception("Kundli tab is not initialized.")

            # Populate input fields on the Kundli tab
            inputs = self.chart_data.get('inputs', {})
            self.kundli_tab.name_var.set(inputs.get('name', ''))
            self.kundli_tab.day_var.set(str(inputs.get('day', '1')))
            self.kundli_tab.month_var.set(str(inputs.get('month', '1')))
            self.kundli_tab.year_var.set(str(inputs.get('year', '2000')))
            self.kundli_tab.hour_var.set(str(inputs.get('hour', '12')))
            self.kundli_tab.minute_var.set(str(inputs.get('minute', '0')))
            self.kundli_tab.second_var.set(str(inputs.get('second', '0')))
            self.kundli_tab.city_var.set(inputs.get('city', ''))
            self.kundli_tab.lat_var.set(str(inputs.get('lat', '0.0')))
            self.kundli_tab.lon_var.set(str(inputs.get('lon', '0.0')))
            self.kundli_tab.tz_var.set(str(inputs.get('tz_offset', '0.0')))

            # Refresh displays and switch tab
            self.kundli_tab.update_all_displays()
            self.notebook.select(self.kundli_tab)
            self.status_var.set(f"Successfully loaded chart for {inputs.get('name', 'N/A')}")

        except json.JSONDecodeError as e:
             messagebox.showerror("Load Error", f"Failed to parse chart file (invalid JSON):\n{e}")
             self.chart_data = {} # Clear data on fail
        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load or process chart file:\n{e}")
            self.chart_data = {} # Clear data on fail


    def show_help(self) -> None:
        """Displays the user guide in a message box."""
        help_text = f"""
        AstroVighati Pro Elite v{self.__VERSION__} - User Guide

        Welcome! This guide explains the core features.

        ================================
        TAB 1: KUNDLI & VARGAS
        ================================
        This is your main workspace.
        1.  Enter all birth details (Name, Date, Time, Location, Timezone).
        2.  Click 'Generate Kundli' to calculate the chart.
        3.  The 'D1 Positions' tab will show the main Rashi chart.
        4.  Use the 'Divisional Chart Controls' dropdown to select a Varga
            (e.g., D9 - Navamsa).
        5.  The 'Varga Positions' and 'Detailed Analysis' tabs will
            instantly update to show data for the selected chart.
        6.  'Varga Meanings' provides a built-in encyclopedia.

        ================================
        FILE MENU (SAVE & LOAD)
        ================================
        -   **Save Chart As... (Ctrl+S)**: Saves the currently generated
            chart (inputs and all calculations) to a `.json` file.
        -   **Open Chart... (Ctrl+O)**: Loads a `.json` chart file you
            previously saved.
        -   **New Chart (Ctrl+N)**: Clears all inputs and results.

        ================================
        TAB 2: VIGHATI RECTIFIER
        ================================
        This tool helps fine-tune a birth time.
        1.  First, generate a chart in the 'Kundli & Vargas' tab.
        2.  Go to this tab ('Vighati Rectifier').
        3.  Click **'Auto-Fill from Kundli'**.
        4.  **YOU MUST MANUALLY ENTER THE SUNRISE TIME** for the
            birth date and location (now including seconds).
        5.  Click 'Calculate & Rectify' to find matching times.
        6.  You can drag the divider between 'Inputs' and 'Results'
            to resize the results area.
            
        ================================
        TAB 5: NAKSHATRA EXPLORER
        ================================
        This is your encyclopedia for Nakshatras.
        1.  Select a Nakshatra from the list on the left to see its
            detailed properties.
        2.  Click the '🗣️ Name Syllables' sub-tab on the right to see
            a complete list of all syllables for all 27 Nakshatras.
        """
        messagebox.showinfo("User Guide", help_text)

    def show_about(self) -> None:
        """Displays the 'About' dialog with application information."""
        about_text = f"""
        AstroVighati Pro Elite v{self.__VERSION__}
        (Nakshatra Syllables Edition)

        An Advanced Vedic Astrology Suite
        with Integrated Knowledge Base & Sidereal Engine (Lahiri Ayanamsa)

        ================================
        FEATURES:
        • Real-time D1 & Varga calculations via Swiss Ephemeris
        • Dynamic, context-aware analysis for D1 and Varga charts
        • Vighati birth time rectification tool (with resizable panel)
        • Vimshottari Dasha timeline
        • Nakshatra name syllable (Avakahada) database
        • Save and Load chart files (.json)
        • Fully themeable user interface

        © 2024-2025 - Elite Edition
        """
        messagebox.showinfo("About", about_text)


#===================================================================================================
# TAB 1: KUNDLI GENERATOR (& VARGAS)
#===================================================================================================
class KundliGeneratorTab(ttk.Frame):
    """
    This class defines the entire "Kundli & Vargas" tab.

    This is the most important tab. It contains:
    1.  Input fields for all birth data.
    2.  The "Generate Kundli" button.
    3.  A results area with multiple sub-tabs for displaying D1 positions,
        Varga positions, detailed analysis, and Varga meanings.
    """

    def __init__(self, parent: ttk.Notebook, app: 'AstroVighatiElite') -> None:
        super().__init__(parent)
        self.app = app

        # This map defines which Vargas are shown in the dropdown.
        self.varga_map: Dict[str, int] = {
            "D1 - Rashi": 1, "D2 - Hora": 2, "D3 - Drekkana": 3, "D4 - Chaturthamsa": 4,
            "D7 - Saptamsa": 7, "D9 - Navamsa": 9, "D10 - Dasamsa": 10, "D12 - Dwadasamsa": 12,
            "D16 - Shodasamsa": 16, "D20 - Vimsamsa": 20, "D24 - Siddhamsa": 24,
            "D30 - Trimsamsa": 30, "D60 - Shashtyamsa": 60
        }

        # This map includes *all* Vargas we want to pre-calculate.
        self.full_varga_map: Dict[str, int] = self.varga_map.copy()
        self.full_varga_map.update({
             "D5 - Panchamsa": 5, "D6 - Shashthamsa": 6,
             "D40 - Khavedamsa": 40, "D45 - Akshavedamsa": 45
        })


        # --- Main Layout ---
        # A PanedWindow creates a draggable divider between two frames.
        # FIX: Removed explicit style='...'
        main_paned = ttk.PanedWindow(self, orient='horizontal')
        main_paned.pack(expand=True, fill='both', padx=10, pady=10)

        # Left panel for user inputs.
        left_panel = ttk.Frame(main_paned, padding=10)
        main_paned.add(left_panel, weight=1) # weight=1 gives it 1/4 of the space

        # Right panel for displaying results.
        right_panel = ttk.Frame(main_paned, padding=(10, 10, 0, 10))
        main_paned.add(right_panel, weight=3) # weight=3 gives it 3/4 of the space

        # Build the UI components for each panel.
        self.create_input_panel(left_panel)
        self.create_results_panel(right_panel)

    def create_input_panel(self, parent: ttk.Frame) -> None:
        """Creates the input form for birth name, date, time, and location."""

        # --- Birth Details Frame ---
        birth_frame = ttk.LabelFrame(parent, text="Birth Details", padding=15)
        birth_frame.pack(fill='x', pady=(0, 10))
        # This makes the 2nd column (widgets) expand to fill space
        birth_frame.grid_columnconfigure(1, weight=1)

        ttk.Label(birth_frame, text="Name:").grid(row=0, column=0, sticky='w', pady=5, padx=5)
        self.name_var = tk.StringVar(value="Shashank")
        ttk.Entry(birth_frame, textvariable=self.name_var).grid(row=0, column=1, sticky='ew', pady=5, padx=5)

        ttk.Label(birth_frame, text="Date (DD/MM/YYYY):").grid(row=1, column=0, sticky='w', pady=5, padx=5)
        date_frame = ttk.Frame(birth_frame)
        date_frame.grid(row=1, column=1, sticky='ew', pady=5, padx=5)
        date_frame.grid_columnconfigure((0, 1, 2), weight=1)
        self.day_var = tk.StringVar(value="14")
        self.month_var = tk.StringVar(value="11")
        self.year_var = tk.StringVar(value="2003")
        ttk.Spinbox(date_frame, from_=1, to=31, textvariable=self.day_var, width=5).grid(row=0, column=0, sticky='ew', padx=(0, 2))
        ttk.Spinbox(date_frame, from_=1, to=12, textvariable=self.month_var, width=5).grid(row=0, column=1, sticky='ew', padx=2)
        ttk.Spinbox(date_frame, from_=1900, to=2100, textvariable=self.year_var, width=8).grid(row=0, column=2, sticky='ew', padx=(2, 0))

        ttk.Label(birth_frame, text="Time (24h format):").grid(row=2, column=0, sticky='w', pady=5, padx=5)
        time_frame = ttk.Frame(birth_frame)
        time_frame.grid(row=2, column=1, sticky='ew', pady=5, padx=5)
        time_frame.grid_columnconfigure((0, 1, 2), weight=1)
        self.hour_var = tk.StringVar(value="19")
        self.minute_var = tk.StringVar(value="41")
        self.second_var = tk.StringVar(value="46")
        ttk.Spinbox(time_frame, from_=0, to=23, textvariable=self.hour_var, width=5, format="%02.0f").grid(row=0, column=0, sticky='ew', padx=(0, 2))
        ttk.Spinbox(time_frame, from_=0, to=59, textvariable=self.minute_var, width=5, format="%02.0f").grid(row=0, column=1, sticky='ew', padx=2)
        ttk.Spinbox(time_frame, from_=0, to=59, textvariable=self.second_var, width=5, format="%02.0f").grid(row=0, column=2, sticky='ew', padx=(2, 0))

        # --- Location Frame ---
        location_frame = ttk.LabelFrame(parent, text="Location", padding=15)
        location_frame.pack(fill='x', pady=(10, 10))
        location_frame.grid_columnconfigure(1, weight=1)

        ttk.Label(location_frame, text="City:").grid(row=0, column=0, sticky='w', pady=5, padx=5)
        self.city_var = tk.StringVar(value="Modinagar")
        ttk.Entry(location_frame, textvariable=self.city_var).grid(row=0, column=1, sticky='ew', pady=5, padx=5)

        ttk.Label(location_frame, text="Latitude:").grid(row=1, column=0, sticky='w', pady=5, padx=5)
        self.lat_var = tk.StringVar(value="28.8344")
        ttk.Entry(location_frame, textvariable=self.lat_var).grid(row=1, column=1, sticky='ew', pady=5, padx=5)

        ttk.Label(location_frame, text="Longitude:").grid(row=2, column=0, sticky='w', pady=5, padx=5)
        self.lon_var = tk.StringVar(value="77.5699")
        ttk.Entry(location_frame, textvariable=self.lon_var).grid(row=2, column=1, sticky='ew', pady=5, padx=5)

        ttk.Label(location_frame, text="Timezone Offset (UTC):").grid(row=3, column=0, sticky='w', pady=5, padx=5)
        self.tz_var = tk.StringVar(value="5.5")
        ttk.Entry(location_frame, textvariable=self.tz_var).grid(row=3, column=1, sticky='ew', pady=5, padx=5)

        # --- Generate Button ---
        ttk.Button(parent, text="🎯 Generate Kundli", command=self.generate_kundli, style='Accent.TButton').pack(fill='x', pady=20, ipady=10)

    def create_results_panel(self, parent: ttk.Frame) -> None:
        """Creates the results panel with quick info, varga controls, and analysis notebook."""

        # --- Top Section (Quick Info & Varga Control) ---
        top_frame = ttk.Frame(parent)
        top_frame.pack(fill='x', pady=(0, 10))

        # Quick Info Display
        info_frame = ttk.LabelFrame(top_frame, text="Quick Info", padding=10)
        info_frame.pack(side='left', fill='x', expand=True, padx=(0, 10))
        self.info_text = tk.Text(info_frame, height=5, width=40, wrap='word', font=('Segoe UI', 9))
        self.info_text.pack(fill='both', expand=True)
        self.info_text.insert('1.0', "Generate a chart to see quick information...")
        self.info_text.config(state='disabled') # Make it read-only

        # Varga Controls
        varga_control_frame = ttk.LabelFrame(top_frame, text="Divisional Chart Controls", padding=10)
        varga_control_frame.pack(side='left', fill='x', expand=True)
        ttk.Label(varga_control_frame, text="Select Chart:").pack(pady=(0, 5))
        self.varga_var = tk.StringVar()
        varga_combo = ttk.Combobox(varga_control_frame, textvariable=self.varga_var,
                                  values=list(self.varga_map.keys()), state="readonly",
                                  width=30)
        varga_combo.pack(pady=(0,5), fill='x')
        varga_combo.set("D1 - Rashi") # Default value
        # Bind the 'change' event to our handler function
        varga_combo.bind("<<ComboboxSelected>>", self.on_varga_select)

        # --- Main Analysis Notebook (with sub-tabs) ---
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
        self.positions_tree.heading('state', text='State (R/C)')
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
        self.varga_tree.heading('details', text='Details (e.g., D60 Deity)')
        self.varga_tree.pack(fill='both', expand=True)

        # Tab 3: Detailed Analysis
        analysis_frame = ttk.Frame(self.analysis_notebook, padding=5)
        self.analysis_notebook.add(analysis_frame, text="💡 Detailed Analysis")
        self.analysis_text = scrolledtext.ScrolledText(analysis_frame, wrap='word', font=('Segoe UI', 11))
        self.analysis_text.pack(fill='both', expand=True)
        self.analysis_text.config(state='disabled') # Read-only

        # Tab 4: Varga Meanings (Encyclopedia)
        varga_desc_frame = ttk.Frame(self.analysis_notebook, padding=5)
        self.analysis_notebook.add(varga_desc_frame, text="📖 Varga Meanings")
        self.varga_desc_text = scrolledtext.ScrolledText(varga_desc_frame, wrap='word', font=('Segoe UI', 11))
        self.varga_desc_text.pack(fill='both', expand=True)
        self.populate_varga_descriptions() # Fill this on startup
        self.varga_desc_text.config(state='disabled') # Read-only

    def clear_inputs_and_outputs(self) -> None:
        """Clears all input fields and output widgets. Called by 'New Chart'."""
        # 1. Clear input variables
        self.name_var.set("")
        self.day_var.set("1")
        self.month_var.set("1")
        self.year_var.set("2000")
        self.hour_var.set("12")
        self.minute_var.set("0")
        self.second_var.set("0")
        self.city_var.set("")
        self.lat_var.set("0.0")
        self.lon_var.set("0.0")
        self.tz_var.set("0.0")

        # 2. Clear output widgets
        self.info_text.config(state='normal') # Must be 'normal' to edit
        self.info_text.delete('1.0', tk.END)
        self.info_text.insert('1.0', "Generate a chart to see quick information...")
        self.info_text.config(state='disabled')

        # Delete all rows from the tables
        self.positions_tree.delete(*self.positions_tree.get_children())
        self.varga_tree.delete(*self.varga_tree.get_children())

        self.analysis_text.config(state='normal')
        self.analysis_text.delete('1.0', tk.END)
        self.analysis_text.config(state='disabled')

        # 3. Reset dropdown
        self.varga_var.set("D1 - Rashi")

    def generate_kundli(self) -> None:
        """
        Main logic function: This is the core workflow when the user
        clicks "Generate Kundli".
        """
        try:
            # --- 1. Gather All Inputs ---
            inputs = {
                "name": self.name_var.get(),
                "day": self.day_var.get(),
                "month": self.month_var.get(),
                "year": self.year_var.get(),
                "hour": self.hour_var.get(),
                "minute": self.minute_var.get(),
                "second": self.second_var.get(),
                "city": self.city_var.get(),
                "lat": self.lat_var.get(),
                "lon": self.lon_var.get(),
                "tz_offset": self.tz_var.get()
            }
            # Convert to a datetime object (will raise ValueError if invalid)
            birth_dt_local = datetime(
                int(inputs['year']), int(inputs['month']), int(inputs['day']),
                int(inputs['hour']), int(inputs['minute']), int(inputs['second'])
            )
            lat, lon, tz_offset = float(inputs['lat']), float(inputs['lon']), float(inputs['tz_offset'])

            # --- 2. Calculate D1 Positions ---
            self.app.status_var.set("Calculating Sidereal positions (Lahiri)...")
            d1_positions = self.app.calculator.calculate_planet_positions(birth_dt_local, lat, lon, tz_offset)
            if not d1_positions:
                self.app.status_var.set("Calculation failed. Please check inputs and console.")
                return

            # --- 3. Pre-calculate ALL Varga Positions (for performance) ---
            self.app.status_var.set("Caching all 17 divisional charts...")
            varga_cache = self.calculate_all_varga_positions(d1_positions)
            self.app.status_var.set("All Varga charts cached.")

            # --- 4. Store in Central State ---
            # This makes the data available to all other tabs (Dasha, Vighati)
            self.app.chart_data = {
                'inputs': inputs,
                'birth_dt_local': birth_dt_local,
                'positions': d1_positions,  # This is the D1 chart
                'varga_cache': varga_cache  # This holds all other D-charts
            }

            # --- 5. Update all displays in this tab ---
            self.update_all_displays()
            self.app.status_var.set("Kundli generated successfully!")
            messagebox.showinfo("Success", "Kundli generated successfully using the Sidereal (Lahiri) Engine!")

        except ValueError:
            messagebox.showerror("Input Error", "Please ensure all fields have valid numbers (e.g., Date, Time, Lat, Lon).")
            self.app.chart_data = {} # Clear data on fail
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred:\n{str(e)}")
            self.app.chart_data = {} # Clear data on fail
            self.app.status_var.set("Error generating Kundli")

    def calculate_all_varga_positions(self, d1_positions: Dict[str, Dict[str, Any]]) -> Dict[int, Dict[str, Dict[str, Any]]]:
        """
        OPTIMIZATION: This helper function pre-calculates all 17 Varga
        charts at once and stores them in a dictionary (cache).

        This makes switching between Vargas in the dropdown list
        INSTANTANEOUS.

        Args:
            d1_positions (dict): The D1 positions from AstronomicalCalculator.

        Returns:
            dict: A cache, e.g., {1: {...D1 data...}, 9: {...D9 data...}, ...}
        """
        cache: Dict[int, Dict[str, Dict[str, Any]]] = {}
        # Use the *full* map to calculate all charts, even hidden ones
        for varga_name, varga_num in self.full_varga_map.items():
            varga_pos_dict: Dict[str, Dict[str, Any]] = {}
            for planet_name, d1_data in d1_positions.items():
                # Call the VargaCalculator for each planet
                varga_sign_num, varga_lon_dec, details = self.app.varga_calculator.calculate_varga_position(
                    varga_num, d1_data['degree_in_rashi'], d1_data['rashi_num']
                )
                if varga_sign_num is not None:
                    # Store the results
                    varga_pos_dict[planet_name] = {
                        'sign_num': varga_sign_num,
                        'sign_name': EnhancedAstrologicalData.SIGNS[varga_sign_num],
                        'longitude_dec': varga_lon_dec,
                        'dms': decimal_to_dms(varga_lon_dec),
                        'details': details
                    }
            cache[varga_num] = varga_pos_dict
        return cache

    def on_varga_select(self, event: Any = None) -> None:
        """
        Callback for when the varga combobox is changed.
        Refreshes only the varga-dependent displays (Varga table and Analysis).
        """
        if not self.app.chart_data: # Do nothing if no chart is loaded
            return
        self.update_varga_positions_display()
        self.update_detailed_analysis()

    def update_all_displays(self, event: Any = None) -> None:
        """A single function to refresh all display widgets in this tab."""
        if not self.app.chart_data:
            return

        self.update_positions_tree()
        self.update_quick_info()
        self.update_varga_positions_display()
        self.update_detailed_analysis()

    def update_positions_tree(self) -> None:
        """Populates the D1 planetary positions table."""
        self.positions_tree.delete(*self.positions_tree.get_children())
        planet_order = ["Ascendant", "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]

        d1_positions = self.app.chart_data['positions']
        sun_longitude = d1_positions.get('Sun', {}).get('longitude', 0)

        for planet_name in planet_order:
            if planet_name in d1_positions:
                pos_data = d1_positions[planet_name]

                # Check for special states (Retrograde, Combust)
                state_list: List[str] = []
                speed = pos_data.get('speed', 0.0)
                if speed < 0:
                    state_list.append("R") # Retrograde

                # Use the InterpretationEngine to check for combustion
                if self.app.interpreter.get_special_state_analysis(planet_name, speed, sun_longitude, pos_data['longitude']).count("Combust"):
                    state_list.append("C") # Combust

                state_str = " ".join(state_list)

                # Insert the data as a new row in the table
                self.positions_tree.insert('', 'end', values=(
                    planet_name, pos_data['rashi'], pos_data['dms'],
                    pos_data['nakshatra'], pos_data.get('nakshatra_lord', 'N/A'), state_str
                ))

    def update_quick_info(self) -> None:
        """Updates the quick info panel with core chart details."""
        self.info_text.config(state='normal')
        self.info_text.delete('1.0', tk.END)
        info = "═══ QUICK REFERENCE ═══\n\n"

        d1_positions = self.app.chart_data['positions']

        if 'Ascendant' in d1_positions:
            asc_info = d1_positions['Ascendant']
            info += f"🔸 Ascendant: {asc_info['rashi']} ({asc_info['dms']})\n"
        if 'Moon' in d1_positions:
            moon_info = d1_positions['Moon']
            info += f"🌙 Moon Sign: {moon_info['rashi']}\n"
            info += f"⭐ Birth Star: {moon_info['nakshatra']}\n"
        if 'Sun' in d1_positions:
            sun_info = d1_positions['Sun']
            info += f"☀️ Sun Sign: {sun_info['rashi']}\n"

        self.info_text.insert('1.0', info)
        self.info_text.config(state='disabled')

    def update_varga_positions_display(self) -> None:
        """
        Updates the 'Varga Positions' table based on the dropdown selection.
        This function READS from the pre-calculated cache.
        """
        self.varga_tree.delete(*self.varga_tree.get_children())
        selected_varga_key = self.varga_var.get()
        varga_num = self.varga_map[selected_varga_key]

        if varga_num == 1:
             # D1 is special, its data is in the other tab
             self.varga_tree.insert('', 'end', values=("This is the D1 chart.", "See 'D1 Positions' tab.", "", ""))
             return

        # Get the pre-calculated data from the cache
        varga_data = self.app.chart_data['varga_cache'][varga_num]
        planet_order = ["Ascendant", "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]

        for planet_name in planet_order:
            if planet_name in varga_data:
                data = varga_data[planet_name]
                # Insert the row into the Varga table
                self.varga_tree.insert('', 'end', values=(
                    planet_name, data['sign_name'], data['dms'], data['details']
                ))

    def update_detailed_analysis(self) -> None:
        """
        Generates and displays the dynamic, multi-layered analysis
        for the currently selected Varga chart.
        """
        self.analysis_text.config(state='normal')
        self.analysis_text.delete('1.0', tk.END)

        selected_varga_key = self.varga_var.get()
        varga_num = self.varga_map[selected_varga_key]

        analysis_str = f"╔═══════ DETAILED ANALYSIS FOR {selected_varga_key.upper()} ═══════╗\n\n"

        # --- 1. Get pre-calculated Varga positions from cache ---
        varga_positions = self.app.chart_data['varga_cache'][varga_num]

        # --- 2. Get D1 data (for Retro/Combust states) ---
        d1_positions = self.app.chart_data['positions']
        sun_d1_longitude = d1_positions.get('Sun', {}).get('longitude', 0)

        # --- 3. Find the Varga Ascendant's sign number ---
        if 'Ascendant' not in varga_positions:
            analysis_str += "Ascendant data not available for this Varga."
            self.analysis_text.insert('1.0', analysis_str)
            self.analysis_text.config(state='disabled')
            return

        varga_asc_sign_num = varga_positions['Ascendant']['sign_num']

        # --- 4. Group all other planets by their Varga house ---
        houses: Dict[int, List[Dict[str, Any]]] = {i: [] for i in range(1, 13)} # Create 12 empty lists
        for planet_name, data in varga_positions.items():
            if planet_name == 'Ascendant':
                continue # Skip the Ascendant itself

            # This is the correct, robust way to calculate the house number
            # (Sign Number - Ascendant Sign Number) + 1, with wrap-around
            house_num = (data['sign_num'] - varga_asc_sign_num + 12) % 12 + 1

            # Add the planet's name to its data dict (needed for the interpreter)
            data['name'] = planet_name
            houses[house_num].append(data)


        # --- 5. Generate analysis for each house (1 through 12) ---
        for house_num in range(1, 13):
            planets_in_house = houses[house_num]

            if planets_in_house: # Only print if the house is not empty
                analysis_str += f"═══ HOUSE {house_num} ═══\n"

                # A. Conjunction analysis first
                conjunction_analysis = self.app.interpreter.get_conjunction_analysis(planets_in_house)
                if conjunction_analysis:
                    analysis_str += conjunction_analysis + "\n\n"

                # B. Individual planet analysis
                for planet_data in planets_in_house:
                    planet_name = planet_data['name']

                    # Call the interpreter for Planet-in-House
                    analysis_str += self.app.interpreter.get_planet_in_house_analysis(
                        planet_name, house_num, varga_num
                    ) + "\n"

                    # Call the interpreter for Planet-in-Sign
                    analysis_str += self.app.interpreter.get_planet_in_sign_analysis(
                        planet_name, planet_data['sign_name']
                    ) + "\n"

                    # Call the interpreter for Special States (R/C)
                    # Note: Special states are *always* taken from the D1 chart!
                    d1_planet_data = d1_positions[planet_name]
                    special_states = self.app.interpreter.get_special_state_analysis(
                        planet_name, d1_planet_data.get('speed', 0),
                        sun_d1_longitude,
                        d1_planet_data['longitude']
                    )
                    if special_states:
                        analysis_str += special_states + "\n"

                    analysis_str += "─" * 20 + "\n" # Separator
                analysis_str += "\n" # Blank line after the house

        # --- 6. Write the final string to the text box ---
        self.analysis_text.insert('1.0', analysis_str)
        self.analysis_text.config(state='disabled')

    def populate_varga_descriptions(self) -> None:
        """
        Fills the 'Varga Meanings' tab with information from the
        data class. This runs once on startup.
        """
        self.varga_desc_text.config(state='normal')
        self.varga_desc_text.delete('1.0', tk.END)

        all_descs = EnhancedAstrologicalData.get_varga_descriptions()
        full_text = ""

        # Loop through the *display* map to get the correct order
        for key in self.varga_map.keys():
            if key in all_descs:
                desc_data = all_descs[key]
                full_text += f"╔═══════ {desc_data['title'].upper()} ═══════╗\n\n"
                full_text += f"{desc_data['description']}\n\n\n"

        self.varga_desc_text.insert('1.0', full_text)
        self.varga_desc_text.config(state='disabled')

#===================================================================================================
# TAB 2-8: OTHER TABS
#===================================================================================================
class EnhancedVighatiTab(ttk.Frame):
    """
    This class defines the "Vighati Rectifier" tab.

    Implements the Vighati system of birth time rectification.
    NEW (v6.0): Uses a PanedWindow for resizable results and
    includes seconds in the sunrise time.
    """
    def __init__(self, parent: ttk.Notebook, app: 'AstroVighatiElite') -> None:
        super().__init__(parent)
        self.app = app
        self.nakshatras = self.app.astro_data.get_all_nakshatras()
        self.create_ui()

    def create_ui(self) -> None:
        """Creates the user interface for the Vighati Rectifier."""
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(expand=True, fill='both')

        ttk.Label(main_frame, text="⚡ VIGHATI BIRTH TIME RECTIFIER", style='Title.TLabel').pack(pady=(0, 20))

        # --- NEW: PanedWindow for resizable sections ---
        # FIX: Removed explicit style='...'
        main_paned = ttk.PanedWindow(main_frame, orient='vertical')
        main_paned.pack(expand=True, fill='both')

        # --- Input Frame (Top Pane) ---
        input_frame = ttk.LabelFrame(main_paned, text="Input Parameters", padding=20)
        main_paned.add(input_frame, weight=1) # Give inputs 1/3 of space
        input_frame.grid_columnconfigure(1, weight=1)

        # Birth Time
        ttk.Label(input_frame, text="Approximate Birth Time:", style='Heading.TLabel').grid(row=0, column=0, sticky='w', pady=10)
        time_frame = ttk.Frame(input_frame)
        time_frame.grid(row=0, column=1, sticky='ew', padx=20)
        time_frame.grid_columnconfigure((0, 1, 2), weight=1)
        self.hour_var = tk.StringVar(value="12")
        self.minute_var = tk.StringVar(value="0")
        self.second_var = tk.StringVar(value="0")
        ttk.Spinbox(time_frame, from_=0, to=23, textvariable=self.hour_var, width=5, format="%02.0f").grid(row=0, column=0, sticky='ew', padx=(0, 2))
        ttk.Spinbox(time_frame, from_=0, to=59, textvariable=self.minute_var, width=5, format="%02.0f").grid(row=0, column=1, sticky='ew', padx=2)
        ttk.Spinbox(time_frame, from_=0, to=59, textvariable=self.second_var, width=5, format="%02.0f").grid(row=0, column=2, sticky='ew', padx=(2, 0))

        # --- MODIFIED: Sunrise Time with Seconds ---
        ttk.Label(input_frame, text="Sunrise Time (HH:MM:SS):", style='Heading.TLabel').grid(row=1, column=0, sticky='w', pady=10)
        sunrise_frame = ttk.Frame(input_frame)
        sunrise_frame.grid(row=1, column=1, sticky='ew', padx=20)
        sunrise_frame.grid_columnconfigure((0, 1, 2), weight=1) # Changed to 3 columns
        self.sunrise_hour = tk.StringVar(value="6")
        self.sunrise_min = tk.StringVar(value="0")
        self.sunrise_sec = tk.StringVar(value="0") # NEW
        ttk.Spinbox(sunrise_frame, from_=0, to=23, textvariable=self.sunrise_hour, width=5, format="%02.0f").grid(row=0, column=0, sticky='ew', padx=(0, 2))
        ttk.Spinbox(sunrise_frame, from_=0, to=59, textvariable=self.sunrise_min, width=5, format="%02.0f").grid(row=0, column=1, sticky='ew', padx=2)
        ttk.Spinbox(sunrise_frame, from_=0, to=59, textvariable=self.sunrise_sec, width=5, format="%02.0f").grid(row=0, column=2, sticky='ew', padx=(2, 0)) # NEW

        # Target Nakshatra
        ttk.Label(input_frame, text="Target Nakshatra:", style='Heading.TLabel').grid(row=2, column=0, sticky='w', pady=10)
        self.nak_var = tk.StringVar()
        nak_values = [f"{n['name']} ({n['devanagari']})" for n in self.nakshatras]
        nak_combo = ttk.Combobox(input_frame, textvariable=self.nak_var, values=nak_values,
                                  state='readonly', width=30)
        nak_combo.grid(row=2, column=1, sticky='ew', padx=20)
        if nak_values:
            nak_combo.set(nak_values[0])

        # Search Range
        ttk.Label(input_frame, text="Search Range (minutes):", style='Heading.TLabel').grid(row=3, column=0, sticky='w', pady=10)
        range_frame = ttk.Frame(input_frame)
        range_frame.grid(row=3, column=1, sticky='ew', padx=20)
        self.range_var = tk.IntVar(value=30)
        range_scale = ttk.Scale(range_frame, from_=5, to=120, variable=self.range_var, orient='horizontal')
        range_scale.pack(side='left', fill='x', expand=True)
        self.range_label = ttk.Label(range_frame, text="30 min")
        self.range_label.pack(side='left', padx=10)
        # This lambda function updates the label text whenever the scale is moved
        self.range_var.trace_add('write', lambda *args: self.range_label.config(text=f"{self.range_var.get()} min"))

        # --- Button Frame ---
        button_frame = ttk.Frame(input_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=20)

        ttk.Button(button_frame, text="Auto-Fill from Kundli",
                  command=self.autofill_from_kundli).pack(side='left', padx=(0, 10), ipady=8)

        ttk.Button(button_frame, text="🚀 Calculate & Rectify",
                  command=self.calculate, style='Accent.TButton').pack(side='left', ipadx=20, ipady=10)

        # --- Results Frame (Bottom Pane) ---
        results_frame = ttk.LabelFrame(main_paned, text="Results", padding=10)
        main_paned.add(results_frame, weight=2) # Give results 2/3 of space

        self.results_text = scrolledtext.ScrolledText(results_frame, font=('Courier New', 10), wrap='word')
        self.results_text.pack(fill='both', expand=True)
        self.results_text.insert('1.0', "Enter parameters and click Calculate...")

    def autofill_from_kundli(self) -> None:
        """Fills inputs from the central app.chart_data"""
        if not self.app.chart_data:
            messagebox.showwarning("No Data", "Please generate a chart in the 'Kundli & Vargas' tab first.")
            return

        try:
            # 1. Get data from central state
            inputs = self.app.chart_data['inputs']
            moon_data = self.app.chart_data['positions'].get('Moon') # Use get for safety

            if not moon_data:
                 messagebox.showerror("Error", "Moon position data not found in the current chart.")
                 return

            moon_nak_name = moon_data.get('nakshatra')
            if not moon_nak_name:
                 messagebox.showerror("Error", "Moon Nakshatra not found in the current chart.")
                 return

            # 2. Set time
            self.hour_var.set(str(inputs.get('hour', '12')))
            self.minute_var.set(str(inputs.get('minute', '0')))
            self.second_var.set(str(inputs.get('second', '0')))

            # 3. Find and set Nakshatra
            moon_nak_info = next((n for n in self.nakshatras if n['name'] == moon_nak_name), None)
            if moon_nak_info:
                self.nak_var.set(f"{moon_nak_info['name']} ({moon_nak_info['devanagari']})")
            else:
                 messagebox.showwarning("Warning", f"Could not find Nakshatra details for {moon_nak_name} in the database.")


            self.app.status_var.set("Vighati details auto-filled.")
            messagebox.showinfo("Auto-Fill Complete",
                                "Birth Time and Nakshatra have been filled.\n\n"
                                "⚠️ **Please enter the correct Sunrise Time** for the birth date and location to proceed.")

        except KeyError as e:
            messagebox.showerror("Auto-Fill Error", f"Missing expected data in the loaded chart: {e}")
        except Exception as e:
            messagebox.showerror("Auto-Fill Error", f"Could not auto-fill data: {e}")


    def calculate(self) -> None:
        """
        Performs the Vighati calculation and searches for matching birth times.
        """
        self.results_text.config(state='normal')
        self.results_text.delete('1.0', tk.END)
        self.results_text.insert('1.0', "Calculating...\n")

        try:
            # --- 1. Get all inputs ---
            hour, minute, second = int(self.hour_var.get()), int(self.minute_var.get()), int(self.second_var.get())
            # MODIFIED: Read seconds from sunrise
            sunrise_h, sunrise_m, sunrise_s = int(self.sunrise_hour.get()), int(self.sunrise_min.get()), int(self.sunrise_sec.get())
            target_nak_full = self.nak_var.get()
            target_nak_eng = target_nak_full.split(' (')[0]
            search_range = self.range_var.get()

            target_nak_data = next((n for n in self.nakshatras if n['name'] == target_nak_eng), None)
            if not target_nak_data:
                messagebox.showerror("Error", "Invalid Nakshatra selected")
                return

            target_remainder = int(target_nak_data['remainder'])

            # --- 2. Perform initial calculation ---

            # Convert times to seconds from midnight
            birth_seconds = hour * 3600 + minute * 60 + second
            # MODIFIED: Include seconds in sunrise
            sunrise_seconds = sunrise_h * 3600 + sunrise_m * 60 + sunrise_s

            # Find difference in seconds.
            time_diff = birth_seconds - sunrise_seconds
            # Handle birth after midnight but before sunrise
            if time_diff < 0:
                time_diff += 86400 # 86400 seconds in a day

            # A Vighati is 24 seconds.
            vighati_value = time_diff / 24.0
            vighati_rounded = round(vighati_value)

            # Using standard Vighati % 9 formula matching 0-8 remainders
            computed_remainder = vighati_rounded % 9
            is_match = (computed_remainder == target_remainder)

            # --- 3. Format results string (Part 1) ---
            results = f"""
╔════════════════════════════════════════════════════════════════════════════════════════╗
║                                 VIGHATI RECTIFICATION RESULTS                          ║
╚════════════════════════════════════════════════════════════════════════════════════════╝
Input Parameters:
• Birth Time: {hour:02d}:{minute:02d}:{second:02d}
• Sunrise Time: {sunrise_h:02d}:{sunrise_m:02d}:{sunrise_s:02d}
• Target Nakshatra: {target_nak_full} (Expected Remainder: {target_remainder})
• Search Range: ±{search_range} minutes
════════════════════════════════════════════════════════════════════════════════════════
INITIAL CALCULATION:
Time from Sunrise   : {time_diff // 3600:.0f}h {(time_diff % 3600) // 60:.0f}m {time_diff % 60:.0f}s
Vighati Value       : {vighati_value:.2f}
Vighati (Rounded)   : {vighati_rounded}
Computed Remainder  : {computed_remainder}  (Vighati % 9)
Match Status        : {'✓ MATCH!' if is_match else '✗ NO MATCH - Searching...'}
════════════════════════════════════════════════════════════════════════════════════════
"""

            # --- 4. Search for matching times ---
            matches_found = 0
            if is_match:
                results += "\n🎉 PERFECT MATCH! The given birth time already matches the target Nakshatra.\n"

            results += "SEARCHING FOR MATCHING TIMES:\n\n"
            results += f"{'Time':<12} | {'Offset':<12} | {'Vighati':<10} | {'Rem':<5} | {'Status':<8}\n"
            results += "-" * 75 + "\n"

            search_seconds = search_range * 60

            # Loop from -range to +range, second by second
            for offset in range(-search_seconds, search_seconds + 1):
                # We already processed offset 0 if it was a match, but
                # it's harmless to show it in the list again.

                test_seconds = birth_seconds + offset
                # Handle day wrap-around
                if test_seconds < 0: test_seconds += 86400
                elif test_seconds >= 86400: test_seconds -= 86400

                # Re-run the calculation for this new time
                new_diff = test_seconds - sunrise_seconds
                if new_diff < 0: new_diff += 86400

                new_vighati_rounded = round(new_diff / 24.0)
                new_remainder = new_vighati_rounded % 9

                # If it's a match, print it
                if new_remainder == target_remainder:
                    matches_found += 1
                    # Convert back to H:M:S
                    test_h, test_m, test_s = test_seconds // 3600, (test_seconds % 3600) // 60, test_seconds % 60
                    # Format offset string (e.g., "-05m30s")
                    offset_sign, offset_m, offset_s = "+" if offset >= 0 else "-", abs(offset) // 60, abs(offset) % 60
                    offset_str = f"{offset_sign}{offset_m:02d}m{offset_s:02d}s"

                    results += f"{f'{test_h:02d}:{test_m:02d}:{test_s:02d}':12} │ {offset_str:11} │ {new_vighati_rounded:>8} │ {new_remainder:>3} │ ✓ Match!  \n"

                    # --- REMOVED LIMIT ---

            results += "-" * 75 + "\n"
            results += f"\n📊 SUMMARY: Found {matches_found} matching time(s) within ±{search_range} minutes.\n"

            # --- 5. Add explanation and show results ---
            results += """
════════════════════════════════════════════════════════════════════════════════════════
VIGHATI SYSTEM EXPLANATION:
The Vighati system divides the time from sunrise into 3600 Vighatis (each 24 seconds).
The birth Nakshatra is determined by the formula: Remainder = (Vighati % 9).
This remainder (0-8) corresponds to the repeating sequence of Nakshatra lords
(0=Ketu, 1=Venus, 2=Sun, 3=Moon, 4=Mars, 5=Rahu, 6=Jupiter, 7=Saturn, 8=Mercury).
"""
            self.results_text.insert('1.0', results)
            self.results_text.config(state='disabled')
            self.app.status_var.set(f"Vighati calculation complete - Found {matches_found} matches.")

        except ValueError:
            messagebox.showerror("Input Error", "Please ensure all time fields are valid numbers.")
            self.results_text.config(state='disabled')
        except Exception as e:
            messagebox.showerror("Calculation Error", f"An unexpected error occurred: {e}")
            self.results_text.config(state='disabled')

class TransitCalculatorTab(ttk.Frame):
    """
    This class defines the "Transits & Predictions" tab.

    Purpose:
    Shows the current real-time positions of the planets (transits).
    It is self-contained and does not depend on the loaded chart data.
    """
    def __init__(self, parent: ttk.Notebook, app: 'AstroVighatiElite') -> None:
        super().__init__(parent)
        self.app = app
        self.create_ui()

    def create_ui(self) -> None:
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

    def show_current_transits(self) -> None:
        """Calculates and displays the planet positions for *right now*."""
        self.app.status_var.set("Calculating current transits...")

        now_utc = datetime.utcnow()
        now_local = datetime.now()

        # Using a default location (New Delhi) for Ascendant
        positions = self.app.calculator.calculate_planet_positions(now_utc, 28.6139, 77.2090, 0) # 0 UTC offset

        if not positions:
            self.app.status_var.set("Failed to calculate transits.")
            return

        text = f"""
╔══════════════════════════════════════════════════════════════════╗
║                       CURRENT PLANETARY TRANSITS                 ║
╚══════════════════════════════════════════════════════════════════╝
Date & Time: {now_local.strftime('%d %B %Y, %H:%M:%S')} (Local Time)
Calculated for: Universal Time (UTC)
Location (Asc): New Delhi (28.61° N, 77.20° E)
════════════════════════════════════════════════════════════════════
SIDEREAL POSITIONS (LAHIRI AYANAMSA):
"""
        planet_order = ["Ascendant", "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
        for planet in planet_order:
            if planet in positions:
                data = positions[planet]
                rashi_info = next((r for r in self.app.astro_data.get_all_rashis() if r['name'] == data.get('rashi')), {})
                planet_dev = next((p.get('devanagari') for p in self.app.astro_data.get_all_planets() if p['name'] == planet), '')
                planet_display = f"{planet} ({planet_dev})"
                rashi_display = f"{rashi_info.get('name')} ({rashi_info.get('devanagari')})"
                degree = data.get('degree_in_rashi', 0)

                # Use string formatting to align columns
                text += f"{planet_display:<20}: {rashi_display:<25} {degree:>6.2f}°\n"

        text += "\n" + "═"*68 + "\n"

        self.transit_text.delete('1.0', tk.END)
        self.transit_text.insert('1.0', text)
        self.app.status_var.set("Current transits calculated successfully")

    def show_predictions(self) -> None:
        """Displays static, general-purpose text about transits."""
        pred_text = """
╔══════════════════════════════════════════════════════════════════╗
║                   TRANSIT PREDICTIONS (GENERAL)                  ║
╚══════════════════════════════════════════════════════════════════╝
This text provides general information about how to interpret transits.
For personalized predictions, a transit's position must be compared
against your unique D1 (Rashi) chart and Dasha periods.

KEY TRANSITS TO WATCH:

🌟 JUPITER (गुरु) TRANSIT:
   Jupiter stays in a sign for ~1 year. Its transit generally brings
   expansion, optimism, and growth to the houses it passes through
   and aspects.

♄ SATURN (शनि) TRANSIT:
   Saturn stays in a sign for ~2.5 years. Its transit demands discipline,
   patience, and hard work. It solidifies and tests the foundations
   of the houses it transits.
   - **Sade Sati (साढ़े साती)**: The famous 7.5-year period when Saturn
     transits the 12th, 1st, and 2nd houses from your natal Moon.
     It is a period of intense karmic lessons and restructuring.

☊ RAHU-KETU (राहु-केतु) AXIS:
   The nodes stay in a sign for ~1.5 years. They always move
   retrograde and are 180° apart.
   - **Rahu** brings obsession, ambition, and focus to the house it transits.
   - **Ketu** brings detachment, spirituality, and endings to the house it transits.

═══════════════════════════════════════════════════════════════════
GENERAL GUIDANCE:
•  Pay most attention to the slow-moving planets (Saturn, Jupiter, Rahu, Ketu)
   as they define the major themes in your life.
•  Fast-moving planets (Sun, Moon, Mars, Mercury, Venus) influence
   day-to-day events, mood, and timing of short-term events.
•  Always check transits from your Ascendant (Lagna) and your
   natal Moon (Chandra Lagna).
"""
        self.prediction_text.delete('1.0', tk.END)
        self.prediction_text.insert('1.0', pred_text)

class DashaTimelineTab(ttk.Frame):
    """
    This class defines the "Dasha Timeline" tab.

    Purpose:
    Calculates a simplified Vimshottari Dasha sequence (major periods only)
    based on the birth Nakshatra of the Moon.
    """
    def __init__(self, parent: ttk.Notebook, app: 'AstroVighatiElite') -> None:
        super().__init__(parent)
        self.app = app
        self.create_ui()

    def create_ui(self) -> None:
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(expand=True, fill='both')

        ttk.Label(main_frame, text="📊 VIMSHOTTARI DASHA TIMELINE", style='Title.TLabel').pack(pady=(0, 20))

        input_frame = ttk.LabelFrame(main_frame, text="Birth Details", padding=15)
        input_frame.pack(fill='x', pady=(0, 15))
        input_frame.grid_columnconfigure(1, weight=1)

        # Birth Date
        ttk.Label(input_frame, text="Birth Date (for age ref):").grid(row=0, column=0, sticky='w', pady=5)
        self.birth_date_var = tk.StringVar(value="01/01/2000")
        ttk.Entry(input_frame, textvariable=self.birth_date_var, width=20).grid(row=0, column=1, sticky='ew', padx=10)

        # Moon Nakshatra
        ttk.Label(input_frame, text="Moon Nakshatra:").grid(row=1, column=0, sticky='w', pady=5)
        self.moon_nak_var = tk.StringVar()
        nak_values = [f"{n['name']} ({n['devanagari']})" for n in self.app.astro_data.get_all_nakshatras()]
        nak_combo = ttk.Combobox(input_frame, textvariable=self.moon_nak_var, values=nak_values,
                                  state='readonly', width=30)
        nak_combo.grid(row=1, column=1, sticky='ew', padx=10)
        if nak_values:
            nak_combo.set(nak_values[0])

        # Button Frame
        button_frame = ttk.Frame(input_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=10, sticky='w')

        ttk.Button(button_frame, text="Auto-Fill from Kundli",
                  command=self.autofill_from_kundli).pack(side='left', padx=5, ipady=8)

        ttk.Button(button_frame, text="Calculate Dasha Timeline",
                  command=self.calculate_dasha, style='Accent.TButton').pack(side='left', padx=5, ipady=8)

        # Results Text
        self.dasha_text = scrolledtext.ScrolledText(main_frame, font=('Courier New', 10), wrap='word')
        self.dasha_text.pack(fill='both', expand=True)
        self.dasha_text.insert('1.0', "Auto-fill from Kundli or enter details manually, then click 'Calculate'...")

    def autofill_from_kundli(self) -> None:
        """Reads from the central app.chart_data to fill inputs."""
        if not self.app.chart_data:
            messagebox.showwarning("No Data", "Please generate a chart in the 'Kundli & Vargas' tab first.")
            return

        try:
            # 1. Get data from central state
            inputs = self.app.chart_data['inputs']
            moon_data = self.app.chart_data['positions'].get("Moon")

            if not moon_data:
                 messagebox.showerror("Error", "Moon position data not found in the current chart.")
                 return

            moon_nak_name = moon_data.get('nakshatra')
            if not moon_nak_name:
                 messagebox.showerror("Error", "Moon Nakshatra not found in the current chart.")
                 return

            # 2. Set date
            self.birth_date_var.set(f"{inputs.get('day', '01')}/{inputs.get('month', '01')}/{inputs.get('year', '2000')}")

            # 3. Find and set Nakshatra
            moon_nak_info = next((n for n in self.app.astro_data.get_all_nakshatras() if n['name'] == moon_nak_name), None)
            if moon_nak_info:
                self.moon_nak_var.set(f"{moon_nak_info['name']} ({moon_nak_info['devanagari']})")
                self.app.status_var.set("Dasha details auto-filled.")
            else:
                 messagebox.showwarning("Warning", f"Could not find Nakshatra details for {moon_nak_name} in the database.")


        except KeyError as e:
            messagebox.showerror("Auto-Fill Error", f"Missing expected data in the loaded chart: {e}")
        except Exception as e:
            messagebox.showerror("Auto-Fill Error", f"Could not auto-fill data: {e}")


    def calculate_dasha(self) -> None:
        """Calculates and displays the Dasha sequence."""
        try:
            # 1. Define Dasha system rules
            dasha_periods: Dict[str, int] = {"Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7, "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17}
            planet_order: List[str] = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]

            # 2. Get inputs
            nak_name_full = self.moon_nak_var.get()
            nak_name_eng = nak_name_full.split(' (')[0]
            birth_date_str = self.birth_date_var.get()

            # Validate date format explicitly
            try:
                birth_date = datetime.strptime(birth_date_str, "%d/%m/%Y")
            except ValueError:
                messagebox.showerror("Input Error", "Invalid Birth Date format. Please use DD/MM/YYYY.")
                return


            nak_data = next((n for n in self.app.astro_data.get_all_nakshatras() if n['name'] == nak_name_eng), None)
            if not nak_data:
                messagebox.showerror("Error", f"Could not find data for Nakshatra: {nak_name_eng}")
                return

            # 3. Find the starting Dasha
            starting_lord = nak_data['lord']
            try:
                start_idx = planet_order.index(starting_lord)
            except ValueError:
                 messagebox.showerror("Error", f"Nakshatra lord '{starting_lord}' not found in Dasha sequence.")
                 return


            # 4. Build the results string
            text = f"""
╔══════════════════════════════════════════════════════════════════╗
║                     VIMSHOTTARI DASHA TIMELINE                   ║
╚══════════════════════════════════════════════════════════════════╝
Birth Nakshatra: {nak_name_full}
Starting Mahadasha: {starting_lord}
(Note: This is a simplified timeline starting from birth.
 A precise calculation requires the Moon's exact degree.)
════════════════════════════════════════════════════════════════════
MAHADASHA SEQUENCE (Major Periods):
"""
            current_date = birth_date

            # 5. Loop through all 9 planets in order
            for i in range(len(planet_order)):
                planet_eng = planet_order[(start_idx + i) % len(planet_order)]
                years = dasha_periods[planet_eng]

                planet_info = next((p for p in self.app.astro_data.get_all_planets() if p['name'] == planet_eng), {})
                planet_display = f"{planet_eng} ({planet_info.get('devanagari', '?')})" # Add fallback

                # Calculate start and end dates
                start_date_str = current_date.strftime('%d-%b-%Y')
                # Use 365.25 to account for leap years
                try:
                    # Adding years can be tricky with timedelta due to varying year lengths
                    # A more robust way might involve dateutil.relativedelta if available
                    # For simplicity, we stick to timedelta with approximate days
                    end_date = current_date + timedelta(days=years * 365.25)
                except OverflowError:
                    end_date_str = "Far Future" # Handle dates too far in the future
                else:
                    end_date_str = end_date.strftime('%d-%b-%Y')

                text += f"\n{i+1}. {planet_display:<20} Mahadasha ({years} years): {start_date_str} to {end_date_str}\n"
                text += f"   └─ This period emphasizes themes of {self.get_dasha_interpretation(planet_eng)}.\n"

                # Update current_date only if end_date calculation was successful
                if end_date_str != "Far Future":
                    current_date = end_date # The next Dasha starts when this one ends


            text += "\n" + "═"*68 + "\n"

            # 6. Display results
            self.dasha_text.delete('1.0', tk.END)
            self.dasha_text.insert('1.0', text)
            self.app.status_var.set("Dasha timeline calculated.")

        except Exception as e:
            messagebox.showerror("Error", f"Could not calculate Dasha.\nError: {e}")

    def get_dasha_interpretation(self, planet: str) -> str:
        """Helper function to get a one-line summary of a Dasha period."""
        interpretations: Dict[str, str] = {
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

class EnhancedNakshatraTab(ttk.Frame):
    """
    This class defines the "Nakshatra Explorer" tab.

    Purpose:
    Acts as a simple, read-only encyclopedia for all 27 Nakshatras.
    
    NEW (v6.0): Includes a new sub-tab for name syllables and adds
    syllable data to the main details view.
    """
    def __init__(self, parent: ttk.Notebook, app: 'AstroVighatiElite') -> None:
        super().__init__(parent)
        self.app = app
        self.create_ui()

    def create_ui(self) -> None:
        # A PanedWindow with a Listbox on the left and Text on the right
        # FIX: Removed explicit style='...'
        paned = ttk.PanedWindow(self, orient='horizontal')
        paned.pack(expand=True, fill='both', padx=10, pady=10)

        # Left Panel (List)
        left_panel = ttk.Frame(paned, padding=10)
        paned.add(left_panel, weight=1)

        ttk.Label(left_panel, text="⭐ NAKSHATRA LIST", style='Heading.TLabel').pack(pady=(0, 10))

        # Search Box
        self.search_var = tk.StringVar()
        # 'trace_add' calls 'filter_nakshatras' every time a key is pressed
        self.search_var.trace_add('write', self.filter_nakshatras)
        ttk.Entry(left_panel, textvariable=self.search_var, width=30).pack(fill='x', pady=(0, 10))

        # Listbox
        self.nak_listbox = tk.Listbox(left_panel, font=('Segoe UI', 11), exportselection=False)
        self.nak_listbox.pack(fill='both', expand=True)
        # Bind the 'select' event to our handler
        self.nak_listbox.bind('<<ListboxSelect>>', self.on_select)

        self.populate_list() # Fill the list on startup

        # --- MODIFIED Right Panel (Now a Notebook) ---
        right_panel = ttk.Frame(paned, padding=(10, 10, 0, 10))
        paned.add(right_panel, weight=2)
        
        self.details_notebook = ttk.Notebook(right_panel)
        self.details_notebook.pack(fill='both', expand=True)

        # Tab 1: Details
        details_frame = ttk.Frame(self.details_notebook, padding=5)
        self.details_notebook.add(details_frame, text="🌟 Details")
        self.details_text = scrolledtext.ScrolledText(details_frame, font=('Segoe UI', 11), wrap='word')
        self.details_text.pack(fill='both', expand=True)
        
        # Tab 2: Name Syllables (NEW)
        syllables_frame = ttk.Frame(self.details_notebook, padding=5)
        self.details_notebook.add(syllables_frame, text="🗣️ Name Syllables")
        self.syllables_text = scrolledtext.ScrolledText(syllables_frame, font=('Segoe UI', 10), wrap='word')
        self.syllables_text.pack(fill='both', expand=True)
        
        # Populate the new syllables tab
        self.populate_syllables_tab()
        self.syllables_text.config(state='disabled') # Read-only


        # Select the first item by default
        if self.nak_listbox.size() > 0:
            self.nak_listbox.selection_set(0)
            self.on_select(None) # Trigger display


    def populate_list(self) -> None:
        """Fills the listbox with all Nakshatra names."""
        self.nak_listbox.delete(0, tk.END)
        for nak in self.app.astro_data.get_all_nakshatras():
            self.nak_listbox.insert(tk.END, f"{nak['name']} ({nak['devanagari']})")

    def filter_nakshatras(self, *args: Any) -> None:
        """Filters the listbox based on the text in the search bar."""
        search_term = self.search_var.get().lower()
        self.nak_listbox.delete(0, tk.END)
        for nak in self.app.astro_data.get_all_nakshatras():
            # Check against name, lord, or sanskrit name
            if (search_term in nak['name'].lower() or
                search_term in nak['lord'].lower() or
                search_term in nak['sanskrit'].lower()):
                self.nak_listbox.insert(tk.END, f"{nak['name']} ({nak['devanagari']})")

    def populate_syllables_tab(self) -> None:
        """
        NEW: Fills the 'Name Syllables' tab with a summary of all nakshatras.
        This runs once on startup.
        """
        self.syllables_text.config(state='normal')
        self.syllables_text.delete('1.0', tk.END)
        
        title = "NAKSHATRA NAME SYLLABLES (AVAKAHADA CHAKRA)"
        text = f"╔{'═'*66}╗\n"
        text += f"║ {title.center(66)} ║\n"
        text += f"╚{'═'*66}╝\n\n"
        text += ("This is a quick reference for the traditional starting syllables "
                 "for a person's name based on the Moon's Nakshatra Pada (quarter) at birth.\n\n")
        
        for nak in self.app.astro_data.get_all_nakshatras():
            syllables = nak.get('syllables', ['N/A']*4)
            syllable_str = ", ".join(syllables)
            # Use f-string for easy alignment
            text += f"**{nak['name']:<20} ({nak['devanagari']})**:\n    {syllable_str}\n\n"
        
        self.syllables_text.insert('1.0', text)
        
        # --- Add simple bold tagging ---
        self.syllables_text.tag_configure("bold", font=('Segoe UI', 10, 'bold'))
        start_index = "1.0"
        while True:
            # Search for the **bold** markers
            start = self.syllables_text.search(r"\*\*", start_index, stopindex=tk.END, regexp=True)
            if not start:
                break
            end = self.syllables_text.search(r"\*\*", f"{start}+2c", stopindex=tk.END, regexp=True)
            if not end:
                break
            
            # Add the tag, then delete the markers
            self.syllables_text.tag_add("bold", start, end)
            self.syllables_text.delete(end, f"{end}+2c")
            self.syllables_text.delete(start, f"{start}+2c")
            start_index = end # Continue searching from the end of the last match

        self.syllables_text.config(state='disabled')
        
    def on_select(self, event: Optional[tk.Event]) -> None:
        """Called when a user clicks on an item in the listbox."""
        selection = self.nak_listbox.curselection()
        if not selection: return # Exit if nothing is selected

        # Get the full name from the list
        nak_name_full = self.nak_listbox.get(selection[0])
        # Get just the English part (e.g., "1. Ashwini")
        nak_name_eng = nak_name_full.split(' (')[0]

        # Find the matching data dictionary
        nak_data = next((n for n in self.app.astro_data.get_all_nakshatras() if n['name'] == nak_name_eng), None)

        if nak_data:
            self.show_details(nak_data)
            # Switch focus to the details tab
            self.details_notebook.select(0)

    def show_details(self, nak: Dict[str, Any]) -> None:
        """
        Displays the formatted details for a selected Nakshatra.
        MODIFIED: Now includes the name syllables.
        """
        self.details_text.config(state='normal')
        self.details_text.delete('1.0', tk.END)
        title = f"{nak['name'].upper()} ({nak['devanagari']})"

        # --- Get the new syllable data ---
        syllables = nak.get('syllables', ['N/A']*4)

        # Create a formatted string for display
        details = f"""
╔══════════════════════════════════════════════════════════════════╗
║  {title.center(62)}                                              ║
╚══════════════════════════════════════════════════════════════════╝

CORE ATTRIBUTES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Ruling Lord      : {nak['lord']}
Presiding Deity  : {nak.get('deity', 'N/A')}
Symbol           : {nak.get('symbol', 'N/A')}

CLASSIFICATION:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Gana (Temperament) : {nak.get('gana', 'N/A')}
Guna (Quality)     : {nak.get('guna', 'N/A')}
Tattva (Element)   : {nak.get('tattva', 'N/A')}
Motivation       : {nak.get('motivation', 'N/A')}

PADA (QUARTERS):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Pada 1: {nak.get('padas', ['?']*4)[0]}
Pada 2: {nak.get('padas', ['?']*4)[1]}
Pada 3: {nak.get('padas', ['?']*4)[2]}
Pada 4: {nak.get('padas', ['?']*4)[3]}

NAME SYLLABLES (AVAKAHADA):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Pada 1: {syllables[0]}
Pada 2: {syllables[1]}
Pada 3: {syllables[2]}
Pada 4: {syllables[3]}

(These are the traditional starting syllables for a person's name
if their Moon is in the respective quarter of this Nakshatra.)
"""
        self.details_text.insert('1.0', details)
        self.details_text.config(state='disabled')

class EnhancedPlanetTab(ttk.Frame):
    """
    This class defines the "Planetary Guide" tab.

    Purpose:
    A simple, read-only encyclopedia for the 9 planets (Navagrahas).
    """
    def __init__(self, parent: ttk.Notebook, app: 'AstroVighatiElite') -> None:
        super().__init__(parent)
        self.app = app
        self.create_ui()

    def create_ui(self) -> None:
        # FIX: Removed explicit style='...'
        paned = ttk.PanedWindow(self, orient='horizontal')
        paned.pack(expand=True, fill='both', padx=10, pady=10)

        # Left Panel (Buttons)
        left_panel = ttk.Frame(paned, padding=10)
        paned.add(left_panel, weight=1)

        ttk.Label(left_panel, text="🪐 NAVAGRAHA (नवग्रह)", style='Heading.TLabel').pack(pady=(0, 10))

        # Create one button for each planet
        for planet in self.app.astro_data.get_all_planets():
            btn = ttk.Button(
                left_panel,
                text=f" {planet['symbol']} {planet['name']} ({planet['devanagari']})",
                # Use a lambda to pass the specific planet data to the command
                command=lambda p=planet: self.show_planet(p),
                width=20
            )
            btn.pack(fill='x', pady=2, ipady=4)

        # Right Panel (Details)
        right_panel = ttk.Frame(paned, padding=10)
        paned.add(right_panel, weight=3) # Give more space to details

        self.planet_text = scrolledtext.ScrolledText(right_panel, font=('Segoe UI', 10), wrap='word')
        self.planet_text.pack(fill='both', expand=True)

        # Show the first planet (Sun) by default on startup
        if self.app.astro_data.get_all_planets():
            self.show_planet(self.app.astro_data.get_all_planets()[0])

    def show_planet(self, planet: Dict[str, Any]) -> None:
        """Displays the formatted details for a selected Planet."""
        self.planet_text.config(state='normal')
        self.planet_text.delete('1.0', tk.END)
        title = f"{planet['name'].upper()} ({planet['sanskrit']} / {planet['devanagari']}) {planet['symbol']}"

        details = f"""
╔═════════════════════════════════════════════════════════════╗
║  {title.center(62)}                                                                   ║
╚═════════════════════════════════════════════════════════════╝

 KARAKA (SIGNIFICATOR):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{planet.get('karaka','N/A')}

 DIGNITIES & STRENGTH:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        # Loop through the dignities dictionary
        dignities = planet.get('dignities', {})
        for dignity, value in dignities.items():
            details += f"{dignity:<20}: {value}\n"

        details += f"""
 BASIC PROPERTIES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 Nature               : {planet.get('nature','N/A')}
 Vimshottari Dasha    : {planet.get('vimshottari_dasha','N/A')}
 Aspects              : {planet.get('aspects', 'N/A')}
 Element              : {planet.get('element', 'N/A')}
 Day                  : {planet.get('day', 'N/A')}

RELATIONSHIPS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Friends              : {', '.join(planet.get('friendly',[]))}
Neutral              : {', '.join(planet.get('neutral', []))}
Enemies              : {', '.join(planet.get('enemy',[]))}
"""
        self.planet_text.insert('1.0', details)
        self.planet_text.config(state='disabled')

class EnhancedRashiTab(ttk.Frame):
    """
    This class defines the "Rashi Explorer" tab.

    Purpose:
    A simple, read-only encyclopedia for the 12 Rashis (Zodiac Signs).
    """
    def __init__(self, parent: ttk.Notebook, app: 'AstroVighatiElite') -> None:
        super().__init__(parent)
        self.app = app
        self.create_ui()

    def create_ui(self) -> None:
        # FIX: Removed explicit style='...'
        paned = ttk.PanedWindow(self, orient='horizontal')
        paned.pack(expand=True, fill='both', padx=10, pady=10)

        # Left Panel (List)
        left_panel = ttk.Frame(paned, padding=10)
        paned.add(left_panel, weight=1)

        ttk.Label(left_panel, text="♈ ZODIAC SIGNS (राशि)", style='Heading.TLabel').pack(pady=(0, 10))

        self.rashi_listbox = tk.Listbox(left_panel, font=('Segoe UI', 12), exportselection=False)
        self.rashi_listbox.pack(fill='both', expand=True)
        self.rashi_listbox.bind('<<ListboxSelect>>', self.on_select)

        for rashi in self.app.astro_data.get_all_rashis():
            self.rashi_listbox.insert(tk.END, f" {rashi['name']} ({rashi['devanagari']})")

        # Right Panel (Details)
        right_panel = ttk.Frame(paned, padding=10)
        paned.add(right_panel, weight=2)

        self.rashi_text = scrolledtext.ScrolledText(right_panel, font=('Segoe UI', 11), wrap='word')
        self.rashi_text.pack(fill='both', expand=True)

        # Select first item by default
        if self.rashi_listbox.size() > 0:
            self.rashi_listbox.selection_set(0)
            self.on_select(None) # Trigger display


    def on_select(self, event: Optional[tk.Event]) -> None:
        """Called when a user clicks on an item in the listbox."""
        selection = self.rashi_listbox.curselection()
        if not selection: return

        rashi_name_full = self.rashi_listbox.get(selection[0]).strip()
        rashi_name_eng = rashi_name_full.split(' (')[0]

        rashi_data = next((r for r in self.app.astro_data.get_all_rashis() if r['name'] == rashi_name_eng), None)
        if rashi_data:
            self.show_details(rashi_data)

    def show_details(self, rashi: Dict[str, str]) -> None:
        """Displays the formatted details for a selected Rashi."""
        self.rashi_text.config(state='normal')
        self.rashi_text.delete('1.0', tk.END)
        title = f"{rashi['name'].upper()} ({rashi['sanskrit']} / {rashi['devanagari']})"

        details = f"""
╔══════════════════════════════════════════════════════════════════╗
║  {title.center(62)}                                              ║
╚══════════════════════════════════════════════════════════════════╝
CORE ATTRIBUTES:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Ruling Lord      : {rashi.get('lord','N/A')}
Element (Tattva) : {rashi.get('tattva','N/A')}
Modality         : {rashi.get('modality','N/A')}
DESCRIPTION:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{rashi.get('description','N/A')}
"""
        self.rashi_text.insert('1.0', details)
        self.rashi_text.config(state='disabled')

class YogasDoshasTab(ttk.Frame):
    """
    This class defines the "Yogas & Doshas" tab.

    Purpose:
    A static, read-only encyclopedia of common Yogas (combinations)
    and Doshas (afflictions).
    """
    def __init__(self, parent: ttk.Notebook, app: 'AstroVighatiElite') -> None:
        super().__init__(parent)
        self.app = app
        self.create_ui()

    def create_ui(self) -> None:
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(expand=True, fill='both')

        ttk.Label(main_frame, text="🔮 YOGAS & DOSHAS ANALYZER", style='Title.TLabel').pack(pady=(0, 20))

        # Use a notebook to separate the categories
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill='both', expand=True)

        # Rajyogas Tab
        rajyoga_frame = ttk.Frame(notebook)
        notebook.add(rajyoga_frame, text="👑 Rajyogas")
        self.rajyoga_text = scrolledtext.ScrolledText(rajyoga_frame, font=('Segoe UI', 10), wrap='word')
        self.rajyoga_text.pack(fill='both', expand=True, padx=5, pady=5)
        self.rajyoga_text.insert('1.0', self.get_rajyoga_info())
        self.rajyoga_text.config(state='disabled') # Read-only

        # Doshas Tab
        dosha_frame = ttk.Frame(notebook)
        notebook.add(dosha_frame, text="🔥 Doshas")
        self.dosha_text = scrolledtext.ScrolledText(dosha_frame, font=('Segoe UI', 10), wrap='word')
        self.dosha_text.pack(fill='both', expand=True, padx=5, pady=5)
        self.dosha_text.insert('1.0', self.get_dosha_info())
        self.dosha_text.config(state='disabled') # Read-only

        # Mahapurusha Yogas Tab
        mahapurusha_frame = ttk.Frame(notebook)
        notebook.add(mahapurusha_frame, text="🌟 Pancha Mahapurusha Yogas")
        self.mahapurusha_text = scrolledtext.ScrolledText(mahapurusha_frame, font=('Segoe UI', 10), wrap='word')
        self.mahapurusha_text.pack(fill='both', expand=True, padx=5, pady=5)
        self.mahapurusha_text.insert('1.0', self.get_mahapurusha_info())
        self.mahapurusha_text.config(state='disabled') # Read-only


    def get_rajyoga_info(self) -> str:
        """Static text for the Rajyogas tab."""
        return """
╔══════════════════════════════════════════════════════════════════╗
║                RAJYOGAS (राजयोग) - ROYAL COMBINATIONS             ║
╚══════════════════════════════════════════════════════════════════╝
Rajyogas are combinations that promise power, status, and success.

1.  **Dharma-Karmadhipati Yoga**:
    A connection (conjunction, mutual aspect, or exchange) between the
    lord of the 9th house (Dharma, fortune) and the 10th house
    (Karma, career). This is one of the most powerful yogas for high
    achievement and a successful career.

2.  **Gaja Kesari Yoga (गज केसरी योग)**:
    Jupiter is in a Kendra (1st, 4th, 7th, 10th house) from the Moon.
    This yoga gives wisdom, fame, virtue, and lasting reputation.

3.  **Neecha Bhanga Rajyoga (नीच भंग राजयोग)**:
    "Cancellation of Debilitation". This occurs when a debilitated
    planet's condition is "fixed" by other factors (e.g., its
    dispositor is in a Kendra). It can turn an initial weakness
    into a great and sudden strength later in life.

4.  **Viparita Rajyoga (विपरीत राजयोग)**:
    "Contrary Royal Yoga". Formed when the lords of "inauspicious"
    houses (6th, 8th, 12th) are placed in one of the *other*
    inauspicious houses. This yoga can give unexpected and sudden
    gains, often after a period of struggle.
"""
    def get_dosha_info(self) -> str:
        """Static text for the Doshas tab."""
        return """
╔══════════════════════════════════════════════════════════════════╗
║                  DOSHAS (दोष) - PLANETARY AFFLICTIONS             ║
╚══════════════════════════════════════════════════════════════════╝
Doshas are afflictions that can indicate challenges or karmic obstacles.

1.  **Manglik Dosha (मांगलिक दोष)**:
    Occurs when Mars is placed in the 1st, 4th, 7th, 8th, or 12th
    house from the Ascendant (or Moon/Venus). It is said to
    cause challenges in marital life. (Note: Some traditions also
    include the 2nd house).

2.  **Kaal Sarpa Dosha (काल सर्प दोष)**:
    Occurs when all 7 planets (Sun to Saturn) are hemmed between
    Rahu and Ketu. This can indicate a life of fated events,
    sudden ups and downs, and a feeling of being constrained by destiny.

3.  **Pitra Dosha (पितृ दोष)**:
    "Ancestral Affliction". This is often seen by afflictions to the
    Sun (karaka for father) or the 9th house (house of father and
    ancestors), especially by Saturn, Rahu, or Ketu. It can
    indicate karmic debts from one's lineage.

4.  **Grahan Dosha (ग्रहण दोष)**:
    "Eclipse Affliction". Occurs when the Sun or Moon is conjunct
    with Rahu or Ketu. It can cause a lack of confidence (with Sun)
    or emotional instability (with Moon) and mental stress.
"""
    def get_mahapurusha_info(self) -> str:
        """Static text for the Pancha Mahapurusha Yogas tab."""
        return """
╔══════════════════════════════════════════════════════════════════╗
║             PANCHA MAHAPURUSHA YOGAS (पंच महापुरुष योग)             ║
╚══════════════════════════════════════════════════════════════════╝
These "Five Great Person" yogas are formed when one of the five
planets (Mars, Mercury, Jupiter, Venus, Saturn) is in its
**own sign** or **exalted**, and also in a **Kendra** (1st, 4th, 7th,
or 10th house) from the Ascendant.

1.  **Ruchaka Yoga (रूचक योग) - Mars**:
    Gives a courageous, strong, and commanding personality.
    Often found in charts of soldiers, athletes, or leaders.

2.  **Bhadra Yoga (भद्र योग) - Mercury**:
    Gives high intelligence, excellent communication, a youthful
    appearance, and success in fields of learning or commerce.

3.  **Hamsa Yoga (हंस योग) - Jupiter**:
    Gives wisdom, spirituality, knowledge, and respect.
    Often found in charts of teachers, advisors, and virtuous people.

4.  **Malavya Yoga (मालव्य योग) - Venus**:
    Gives charm, beauty, artistic talent, and a life of
    luxury, comfort, and happy relationships.

5.  **Sasa Yoga (शश योग) - Saturn**:
    Gives a disciplined, patient, and influential personality.
    Can raise a person to a high position of authority, often
    in service to the masses (e.g., politician, judge).
"""
#===================================================================================================
# MAIN EXECUTION BLOCK
#===================================================================================================
if __name__ == "__main__":
    """
    This is the entry point of the application.
    This block only runs when the script is executed directly,
    not when it's imported as a module.
    """
    try:
        # 1. Create the main application window
        root = tk.Tk()

        # 2. Create the main application class instance
        app = AstroVighatiElite(root)

        # 3. Print a welcome message to the console
        welcome_msg = f"""
{'='*70}
🌟 ASTROVIGHATI PRO ELITE v{AstroVighatiElite.__VERSION__} 🌟
   Advanced Vedic Astrology Suite
   Welcome! The application is now running. Please use the GUI window.
   Console is active for dependency checks and error logging.
{'='*70}
"""
        print(welcome_msg)

        # 4. Start the application's main event loop
        #    This line is blocking; the script will "wait" here
        #    until the user closes the GUI window.
        root.mainloop()

    except Exception as e:
        # This is a last-resort catch-all for any fatal error
        # that occurs during the application's startup.
        import traceback
        error_details = traceback.format_exc()

        # Print the full error to the console
        print(f"\n{'='*70}\nA CRITICAL APPLICATION ERROR OCCURRED\n{'='*70}\n{error_details}\n{'='*70}")

        try:
            # Try to show a GUI error as well
            # Create a temporary root window only if the main one failed before mainloop
            error_root = tk.Tk()
            error_root.withdraw() # Hide the blank root window
            messagebox.showerror(
                "Critical Application Error",
                f"A fatal error occurred and the application must close.\n\n"
                f"Error: {str(e)}\n\n"
                "Please check the console (terminal) for the full traceback."
            )
            error_root.destroy()
        except tk.TclError:
            # If Tkinter itself is failing, we can't show a messagebox
            print("Could not display GUI error message box.")
        except Exception as e_msgbox:
            print(f"An error occurred while trying to display the error messagebox: {e_msgbox}")