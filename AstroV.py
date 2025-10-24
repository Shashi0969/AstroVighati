# GUI Version - 6.0 

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
import textwrap
from dateutil.relativedelta import relativedelta # For accurate date math

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
        in Vedic astrology, including advanced attributes from BPHS and Lal Kitab.

        Returns:
            list: A list of dictionaries, where each dictionary is a planet.
        """
        return [
            {
                "name": "Sun", "sanskrit": "Surya", "devanagari": "सूर्य", "symbol": "☉",
                "karaka": "Atmakaraka (Soul), Father, King, Government, Authority, Ego, Self-Esteem, Health, Vitality, Right Eye, Heart, Bones",
                "dignities": {
                    "Exaltation": "Aries 10°", "Debilitation": "Libra 10°",
                    "Moolatrikona": "Leo 0°-20°", "Own Sign": "Leo"
                },
                "nature": "Krura (Cruel, not Papa)", "gender": "Male", "vimshottari_dasha": "6 Years",
                "aspects": "7th house (100%)", "element": "Fire (Agni)", "caste": "Kshatriya (Warrior)",
                "color": "#FDB813", "day": "Sunday", "gemstone": "Ruby (Manikya)",
                "deity": "Agni / Shiva", "metal": "Gold / Copper", "direction": "East",
                "body_part": "Bones, Right Eye, Heart", "friendly": ["Moon", "Mars", "Jupiter"],
                "neutral": ["Mercury"], "enemy": ["Venus", "Saturn", "Rahu", "Ketu"],
                "bphs_note": "The King of the Navagrahas. Represents the 'Atma' (soul) and authority. As a 'Krura' (cruel) graha, it can be separating in nature but is not inherently malefic like Saturn. Its placement indicates the soul's focus, ego, and the native's relationship with authority and father.",
                "lal_kitab_note": "Pakka Ghar (Fixed House): 1. Represents 'Sarkar' (government), father, and right side. Exalted in House 1 (Aries), Debilitated in House 7 (Libra). A well-placed Sun is the highest 'Raj Yoga'. Remedies often involve honoring the father and floating copper coins ('paisa') in running water."
            },
            {
                "name": "Moon", "sanskrit": "Chandra", "devanagari": "चंद्र", "symbol": "☽",
                "karaka": "Manakaraka (Mind), Mother, Emotions, Queen, Popularity, Fluids, Public Life, Left Eye, Blood, Breasts",
                "dignities": {
                    "Exaltation": "Taurus 3°", "Debilitation": "Scorpio 3°",
                    "Moolatrikona": "Taurus 4°-30°", "Own Sign": "Cancer"
                },
                "nature": "Benefic (Waxing), Malefic (Waning)", "gender": "Female", "vimshottari_dasha": "10 Years",
                "aspects": "7th house (100%)", "element": "Water (Jala)", "caste": "Vaishya (Merchant)",
                "color": "#C0C0C0", "day": "Monday", "gemstone": "Pearl (Moti)",
                "deity": "Varuna / Parvati", "metal": "Silver", "direction": "North-West",
                "body_part": "Blood, Left Eye, Mind, Fluids, Breasts", "friendly": ["Sun", "Mercury"],
                "neutral": ["Mars", "Jupiter", "Venus", "Saturn"], "enemy": ["Rahu", "Ketu"],
                "bphs_note": "The Queen. Represents the 'Manas' (mind) and perception. A 'Saumya' (gentle) graha. Its state (waxing/waning) is critical for its benefic or malefic nature. It is the fastest moving body, indicating fluctuations and emotional responses.",
                "lal_kitab_note": "Pakka Ghar: 4. Exalted in 2 (Taurus), Debilitated in 8 (Scorpio). Represents mother, 'khazana' (liquid cash), and horses. A 'sleeping' Moon (e.g., in H6) can be 'awakened' by remedies. Remedies involve serving the mother and using silver, rice, or milk."
            },
            {
                "name": "Mars", "sanskrit": "Mangala", "devanagari": "मंगल", "symbol": "♂",
                "karaka": "Bhratrukaraka (Siblings), Energy, Courage, Conflict, Land (Bhoomi), Logic (Tarka), Surgery, Accidents, Blood, Muscles",
                "dignities": {
                    "Exaltation": "Capricorn 28°", "Debilitation": "Cancer 28°",
                    "Moolatrikona": "Aries 0°-12°", "Own Sign": "Aries, Scorpio"
                },
                "nature": "Malefic (Papa)", "gender": "Male", "vimshottari_dasha": "7 Years",
                "aspects": "4th, 7th, 8th houses (Special Aspects)", "element": "Fire (Agni)", "caste": "Kshatriya (Warrior)",
                "color": "#CD5C5C", "day": "Tuesday", "gemstone": "Red Coral (Moonga)",
                "deity": "Kartikeya / Narasimha", "metal": "Copper", "direction": "South",
                "body_part": "Muscles, Marrow, Blood", "friendly": ["Sun", "Moon", "Jupiter"],
                "neutral": ["Venus", "Saturn"], "enemy": ["Mercury", "Rahu", "Ketu"],
                "bphs_note": "The Commander-in-Chief. A natural malefic (papa graha). Represents action, energy, and conflict. Its special 4th (domestic) and 8th (sudden) aspects are powerful and often disruptive. It is the key planet for Manglik Dosha.",
                "lal_kitab_note": "Pakka Ghar: 3 & 8. Exalted in 10 (Capricorn), Debilitated in 4 (Cancer). 'Mangal Nek' (Good Mars) gives courage. 'Mangal Bad' (Bad Mars, e.g., in H4/H8) causes problems. Remedies involve helping brothers and feeding sweet tandoori roti to dogs."
            },
            {
                "name": "Mercury", "sanskrit": "Budha", "devanagari": "बुध", "symbol": "☿",
                "karaka": "Vidyakaraka (Education), Vani (Speech), Intellect, Communication, Commerce, Friends, Skin, Nervous System, Analysis",
                "dignities": {
                    "Exaltation": "Virgo 15°", "Debilitation": "Pisces 15°",
                    "Moolatrikona": "Virgo 16°-20°", "Own Sign": "Gemini, Virgo"
                },
                "nature": "Neutral (Benefic with benefics, Malefic with malefics)", "gender": "Neutral (Eunuch)", "vimshottari_dasha": "17 Years",
                "aspects": "7th house (100%)", "element": "Earth (Prithvi)", "caste": "Vaishya (Merchant)",
                "color": "#90EE90", "day": "Wednesday", "gemstone": "Emerald (Panna)",
                "deity": "Vishnu", "metal": "Brass", "direction": "North",
                "body_part": "Skin, Nervous System, Speech", "friendly": ["Sun", "Venus", "Rahu"],
                "neutral": ["Mars", "Jupiter", "Saturn", "Ketu"], "enemy": ["Moon"],
                "bphs_note": "The Prince. A neutral (napumsaka) planet representing 'Buddhi' (intellect). Its nature is highly adaptable. It rules logic, analysis, and speech. Its combustion by the Sun is a very common and important factor to check.",
                "lal_kitab_note": "Pakka Ghar: 7. Exalted in 6 (Virgo), Debilitated in 12 (Pisces). Represents daughters, sisters, and aunts ('beti-behen-bua'). A 'sleeping' Mercury needs to be 'awakened' (e.g., by piercing the nose). Remedies often involve feeding green fodder to cows or gifting items to young girls."
            },
            {
                "name": "Jupiter", "sanskrit": "Guru", "devanagari": "गुरु", "symbol": "♃",
                "karaka": "Dhanakaraka (Wealth), Putrakaraka (Children), Gyanakaraka (Wisdom), Husband (for females), Teacher (Guru), Dharma, Liver, Fat",
                "dignities": {
                    "Exaltation": "Cancer 5°", "Debilitation": "Capricorn 5°",
                    "Moolatrikona": "Sagittarius 0°-10°", "Own Sign": "Sagittarius, Pisces"
                },
                "nature": "Most Benefic (Shubha)", "gender": "Male", "vimshottari_dasha": "16 Years",
                "aspects": "5th, 7th, 9th houses (Special Aspects)", "element": "Ether (Akasha)", "caste": "Brahmin (Priest/Teacher)",
                "color": "#FFD700", "day": "Thursday", "gemstone": "Yellow Sapphire (Pukhraj)",
                "deity": "Indra / Brahma", "metal": "Gold", "direction": "North-East",
                "body_part": "Fat, Liver, Thighs", "friendly": ["Sun", "Moon", "Mars", "Ketu"],
                "neutral": ["Saturn"], "enemy": ["Mercury", "Venus", "Rahu"],
                "bphs_note": "The Great Minister/Teacher. The most benefic planet, representing expansion, wisdom, and divine grace. Its special 5th and 9th (trinal) aspects are considered 'amrita drishti' (nectar-like blessings) that nurture and protect the houses they touch.",
                "lal_kitab_note": "Pakka Ghar: 9. Exalted in 4 (Cancer), Debilitated in 10 (Capricorn). Represents 'dada' (grandfather) and 'Brahmin'. Considered the 'Giver'. A malefic Jupiter can be remedied by applying a 'kesar' (saffron) tilak, wearing gold, or serving elders and teachers."
            },
            {
                "name": "Venus", "sanskrit": "Shukra", "devanagari": "शुक्र", "symbol": "♀",
                "karaka": "Kalatrakaraka (Spouse), Love, Beauty, Arts, Luxury, Vehicles (Vahana), Comforts, Semen, Diplomacy",
                "dignities": {
                    "Exaltation": "Pisces 27°", "Debilitation": "Virgo 27°",
                    "Moolatrikona": "Libra 0°-15°", "Own Sign": "Taurus, Libra"
                },
                "nature": "Benefic (Shubha)", "gender": "Female", "vimshottari_dasha": "20 Years",
                "aspects": "7th house (100%)", "element": "Water (Jala)", "caste": "Brahmin (Priest/Teacher)",
                "color": "#FFB6C1", "day": "Friday", "gemstone": "Diamond (Heera)",
                "deity": "Lakshmi / Indrani", "metal": "Silver", "direction": "South-East",
                "body_part": "Reproductive Organs, Face, Eyes", "friendly": ["Mercury", "Saturn", "Rahu"],
                "neutral": ["Mars", "Jupiter", "Ketu"], "enemy": ["Sun", "Moon"],
                "bphs_note": "The (Daitya) Guru. A great benefic, ruling material pleasures ('Bhoga'). Represents relationships, diplomacy, and all forms of art and luxury. It is the guru of the Asuras. Its strength is critical for marital happiness and worldly comforts.",
                "lal_kitab_note": "Pakka Ghar: 7. Exalted in 12 (Pisces), Debilitated in 6 (Virgo). Represents the wife ('stree') and wealth. A malefic Venus can be remedied by donating 'jowar' (sorghum), 'ghee', or 'curd' (yogurt), and by feeding cows (Gau Seva)."
            },
            {
                "name": "Saturn", "sanskrit": "Shani", "devanagari": "शनि", "symbol": "♄",
                "karaka": "Ayu-karaka (Longevity), Karmakaraka (Career), Duhkha (Sorrow), Discipline, Delays, Servants, Masses, Democracy, Debts, Disease",
                "dignities": {
                    "Exaltation": "Libra 20°", "Debilitation": "Aries 20°",
                    "Moolatrikona": "Aquarius 0°-20°", "Own Sign": "Capricorn, Aquarius"
                },
                "nature": "Most Malefic (Papa)", "gender": "Neutral (Eunuch)", "vimshottari_dasha": "19 Years",
                "aspects": "3rd, 7th, 10th houses (Special Aspects)", "element": "Air (Vayu)", "caste": "Shudra (Service)",
                "color": "#4169E1", "day": "Saturday", "gemstone": "Blue Sapphire (Neelam)",
                "deity": "Yama / Brahma", "metal": "Iron", "direction": "West",
                "body_part": "Legs, Knees, Nerves, Teeth, Bones", "friendly": ["Mercury", "Venus", "Rahu"],
                "neutral": ["Jupiter"], "enemy": ["Sun", "Moon", "Mars", "Ketu"],
                "bphs_note": "The Servant/Judge. The most malefic planet, representing restriction, reality, and the consequences of karma. It is slow-moving ('Manda'). Its special 3rd and 10th aspects are powerful, often bringing separation, delay, or a sense of heavy responsibility.",
                "lal_kitab_note": "Pakka Ghar: 10. Exalted in 7 (Libra), Debilitated in 1 (Aries). Represents 'chacha' or 'taya' (paternal uncle). A malefic Saturn ('Shani Bad') is very feared. Remedies include donating oil ('tel-daan'), black cloth, or 'urad dal', and feeding crows or snakes."
            },
            {
                "name": "Rahu", "sanskrit": "Rahu", "devanagari": "राहु", "symbol": "☊",
                "karaka": "Foreign things, Illusion (Maya), Obsession, Ambition, Technology, Sudden Events, Internet, Poisons, Paternal Grandfather",
                "dignities": {
                    "Exaltation": "Taurus / Gemini", "Debilitation": "Scorpio / Sagittarius",
                    "Moolatrikona": "Aquarius", "Own Sign": "Virgo"
                },
                "nature": "Malefic (like Saturn)", "gender": "N/A", "vimshottari_dasha": "18 Years",
                "aspects": "5th, 7th, 9th houses (Special Aspects)", "element": "Air (Vayu)", "caste": "Outcaste (Mleccha)",
                "color": "#8B4513", "day": "N/A", "gemstone": "Hessonite (Gomed)",
                "deity": "Durga / Varaha", "metal": "Lead", "direction": "South-West",
                "body_part": "N/A (Shadow Planet)", "friendly": ["Mercury", "Venus", "Saturn"],
                "neutral": ["Jupiter"], "enemy": ["Sun", "Moon", "Mars"],
                "bphs_note": "The North Node (Dragon's Head). A shadow planet ('Chhaya Graha'). Acts like Saturn ('Shani-vat Rahu'). It is the amplifier, representing insatiable worldly desire, obsession, sudden events, and all things foreign or unconventional.",
                "lal_kitab_note": "Pakka Ghar: 12. Exalted in 2 (Taurus) or 3 (Gemini). Represents 'haathi' (elephant) and 'sasural' (in-laws). Can give immense, sudden wealth. Remedies involve floating coal ('koyla') in water, keeping fennel ('saunf') by the bedside, or donating 'mooli' (radish)."
            },
            {
                "name": "Ketu", "sanskrit": "Ketu", "devanagari": "केतु", "symbol": "☋",
                "karaka": "Mokshakaraka (Liberation), Detachment (Vairagya), Past Karma, Intuition, Occult, Flags, Roots, Paternal Grandfather",
                "dignities": {
                    "Exaltation": "Scorpio / Sagittarius", "Debilitation": "Taurus / Gemini",
                    "Moolatrikona": "Leo", "Own Sign": "Pisces"
                },
                "nature": "Malefic (like Mars)", "gender": "N/A", "vimshottari_dasha": "7 Years",
                "aspects": "5th, 7th, 9th houses (Special Aspects)", "element": "Fire (Agni)", "caste": "Outcaste (Mleccha)",
                "color": "#A9A9A9", "day": "N/A", "gemstone": "Cat's Eye (Lehsunia)",
                "deity": "Ganesha / Brahma", "metal": "Lead", "direction": "N/A (Represents 'Dhvaja' - Flag)",
                "body_part": "N/A (Shadow Planet)", "friendly": ["Sun", "Moon", "Mars", "Jupiter"],
                "neutral": ["Venus", "Saturn", "Mercury"], "enemy": ["Rahu"],
                "bphs_note": "The South Node (Dragon's Tail). A shadow planet. Acts like Mars ('Kuja-vat Ketu'). It is the detacher, representing spirituality, intuition, sudden endings, and past life merits/demerits. It forces introspection and leads towards Moksha.",
                "lal_kitab_note": "Pakka Ghar: 6. Exalted in 8 (Scorpio) or 9 (Sagittarius). Represents 'aulad' (progeny, especially son) and 'kutta' (dog). Can give deep intuitive abilities. Remedies involve feeding dogs, wearing gold in the ear, or donating blankets to the needy."
            }
        ]
    @staticmethod
    def get_all_nakshatras() -> List[Dict[str, Any]]:
        """
        Returns a list of all 27 Nakshatras (lunar mansions) with their
        key attributes, including classical details and Lal Kitab notes.

        Returns:
            list: A list of dictionaries, where each dictionary is a nakshatra.
        """
        # Note: Some attributes like Tattva, Direction for Nakshatras vary across sources.
        # The primary classification (Gana, Yoni, Nadi, Lord, Deity) is more standard.
        return [
            {"num": 1, "name": "Ashwini", "sanskrit": "Ashwini", "devanagari": "अश्विनी", "lord": "Ketu", "remainder": 0,
            "deity": "Ashwini Kumaras (Healers)", "symbol": "Horse's Head", "start_degree": 0.0, "end_degree": 13.3333,
            "padas_rashi": ["Aries"]*4, "padas_navamsha": ["Aries", "Taurus", "Gemini", "Cancer"],
            "syllables": ["चू (Chu)", "चे (Che)", "चो (Cho)", "ला (La)"],
            "gana": "Deva (Divine)", "yoni": "Ashwa (Male Horse)", "nadi": "Adi (Vata)", "guna": "Rajasic", "tattva": "Earth",
            "motivation": "Dharma", "nature": "Laghu/Kshipra (Light/Swift)",
            "keywords": "Healing, Speed, Initiation, Beginnings, Impulsive, Energetic, Quick Action",
            "bphs_note": "Represents swift action, healing energy (like its deities). Ketu's rulership indicates beginnings rooted in past karma or intuition. A Gandanta point starts here.",
            "lal_kitab_note": "Governed by Ketu. Ketu's effect depends on House 6 ('Pakka Ghar'). If Moon is here, remedies involving dogs (Ketu) might apply. Energy influenced by Mars (Aries)."
            },
            {"num": 2, "name": "Bharani", "sanskrit": "Bharani", "devanagari": "भरणी", "lord": "Venus", "remainder": 1,
            "deity": "Yama (Lord of Death/Dharma)", "symbol": "Yoni (Female reproductive organ)", "start_degree": 13.3333, "end_degree": 26.6666,
            "padas_rashi": ["Aries"]*4, "padas_navamsha": ["Leo", "Virgo", "Libra", "Scorpio"],
            "syllables": ["ली (Li)", "लू (Lu)", "ले (Le)", "लो (Lo)"],
            "gana": "Manushya (Human)", "yoni": "Gaja (Male Elephant)", "nadi": "Madhya (Pitta)", "guna": "Rajasic", "tattva": "Earth",
            "motivation": "Artha", "nature": "Ugra/Krura (Fierce/Cruel)",
            "keywords": "Transformation, Restraint, Discipline, Judgment, Cycles of Life/Death, Creativity, Sexuality",
            "bphs_note": "Represents the process of birth and death, transformation. Deity Yama indicates discipline and judgment. Venus lordship brings creative and procreative energy.",
            "lal_kitab_note": "Governed by Venus. Venus's effect depends on House 7 ('Pakka Ghar'). Influenced by Mars (Aries). Can indicate strong desires. Remedies might involve Venus items (ghee, curd)."
            },
            {"num": 3, "name": "Krittika", "sanskrit": "Krittika", "devanagari": "कृत्तिका", "lord": "Sun", "remainder": 2,
            "deity": "Agni (God of Fire)", "symbol": "Knife, Axe, Razor, Flame", "start_degree": 26.6666, "end_degree": 40.0,
            "padas_rashi": ["Aries"] + ["Taurus"]*3, "padas_navamsha": ["Sagittarius", "Capricorn", "Aquarius", "Pisces"],
            "syllables": ["अ (A)", "ई (I)", "उ (U)", "ए (E)"],
            "gana": "Rakshasa (Demonic)", "yoni": "Mesha (Female Sheep)", "nadi": "Antya (Kapha)", "guna": "Rajasic", "tattva": "Earth",
            "motivation": "Kama", "nature": "Misra/Sadharana (Mixed)",
            "keywords": "Cutting, Purifying, Fiery, Sharp Intellect, Leadership, Criticism, Ambition, Nurturing (Taurus part)",
            "bphs_note": "Bridging Aries and Taurus. Deity Agni gives purifying fire. Symbol indicates sharpness (intellect, criticism). Sun lordship gives leadership. The Taurus portion adds stability and nurturing.",
            "lal_kitab_note": "Governed by Sun. Sun's effect depends on House 1 ('Pakka Ghar'). Spans Mars (Aries) and Venus (Taurus) Rasis. Can give sharp intelligence and authority. Remedies might involve Sun items (copper, wheat)."
            },
            {"num": 4, "name": "Rohini", "sanskrit": "Rohini", "devanagari": "रोहिणी", "lord": "Moon", "remainder": 3,
            "deity": "Brahma/Prajapati (Creator)", "symbol": "Cart, Chariot, Temple, Banyan Tree", "start_degree": 40.0, "end_degree": 53.3333,
            "padas_rashi": ["Taurus"]*4, "padas_navamsha": ["Aries", "Taurus", "Gemini", "Cancer"],
            "syllables": ["ओ (O)", "वा (Va)", "वी (Vi)", "वू (Vu)"],
            "gana": "Manushya (Human)", "yoni": "Sarpa (Male Serpent)", "nadi": "Antya (Kapha)", "guna": "Rajasic", "tattva": "Earth",
            "motivation": "Moksha", "nature": "Sthira/Dhruva (Fixed/Permanent)",
            "keywords": "Growth, Fertility, Creativity, Beauty, Materialism, Stability, Charm, Sensuality",
            "bphs_note": "Moon's favorite Nakshatra, where it is exalted. Represents growth, creation (Brahma), and material abundance. Associated with beauty and charm. Highly fertile.",
            "lal_kitab_note": "Governed by Moon. Moon's effect depends on House 4 ('Pakka Ghar'). In Venus's sign (Taurus). Excellent for wealth and beauty. Remedies involve Moon items (silver, rice)."
            },
            {"num": 5, "name": "Mrigashira", "sanskrit": "Mrigashira", "devanagari": "मृगशिरा", "lord": "Mars", "remainder": 4,
            "deity": "Soma (Moon God)", "symbol": "Deer's Head", "start_degree": 53.3333, "end_degree": 66.6666,
            "padas_rashi": ["Taurus"]*2 + ["Gemini"]*2, "padas_navamsha": ["Leo", "Virgo", "Libra", "Scorpio"],
            "syllables": ["वे (Ve)", "वो (Vo)", "का (Ka)", "की (Ki)"],
            "gana": "Deva (Divine)", "yoni": "Sarpa (Female Serpent)", "nadi": "Madhya (Pitta)", "guna": "Rajasic", "tattva": "Air",
            "motivation": "Moksha", "nature": "Mridu/Maitra (Soft/Friendly)",
            "keywords": "Searching, Seeking, Curiosity, Restlessness, Travel, Gentle, Sensitive, Collecting",
            "bphs_note": "Bridging Taurus and Gemini ('The Searching Star'). Symbol deer indicates seeking. Deity Soma brings sensitivity. Mars lordship adds drive to the search. Gemini portion adds intellect.",
            "lal_kitab_note": "Governed by Mars. Mars's effect depends on House 3/8 ('Pakka Ghar'). Spans Venus (Taurus) and Mercury (Gemini) Rasis. Can indicate searching/wandering nature. Remedies for Mars may apply."
            },
            {"num": 6, "name": "Ardra", "sanskrit": "Ardra", "devanagari": "आर्द्रा", "lord": "Rahu", "remainder": 5,
            "deity": "Rudra (Storm God/Shiva)", "symbol": "Teardrop, Diamond, Human Head", "start_degree": 66.6666, "end_degree": 80.0,
            "padas_rashi": ["Gemini"]*4, "padas_navamsha": ["Sagittarius", "Capricorn", "Aquarius", "Pisces"],
            "syllables": ["कू (Ku)", "घ (Gha)", "ङ (Na)", "छ (Chha)"],
            "gana": "Manushya (Human)", "yoni": "Shwana (Female Dog)", "nadi": "Adi (Vata)", "guna": "Tamasic", "tattva": "Air",
            "motivation": "Kama", "nature": "Tikshna/Daruna (Sharp/Dreadful)",
            "keywords": "Intensity, Storms, Transformation, Destruction for Renewal, Effort, Analysis, Emotional Outbursts",
            "bphs_note": "Represents intensity and the destructive force needed for creation (Rudra). Symbol teardrop indicates potential sorrow or release. Rahu lordship brings sudden changes and intensity.",
            "lal_kitab_note": "Governed by Rahu. Rahu's effect depends on House 12 ('Pakka Ghar'). In Mercury's sign (Gemini). Can indicate sharp intellect, sudden events, or troubles. Remedies for Rahu (coal, radish) may apply."
            },
            {"num": 7, "name": "Punarvasu", "sanskrit": "Punarvasu", "devanagari": "पुनर्वसु", "lord": "Jupiter", "remainder": 6,
            "deity": "Aditi (Mother of Gods)", "symbol": "Bow and Quiver", "start_degree": 80.0, "end_degree": 93.3333,
            "padas_rashi": ["Gemini"]*3 + ["Cancer"]*1, "padas_navamsha": ["Aries", "Taurus", "Gemini", "Cancer"],
            "syllables": ["के (Ke)", "को (Ko)", "हा (Ha)", "ही (Hi)"],
            "gana": "Deva (Divine)", "yoni": "Marjara (Female Cat)", "nadi": "Adi (Vata)", "guna": "Sattvic", "tattva": "Air",
            "motivation": "Artha", "nature": "Chara/Chala (Movable/Changing)",
            "keywords": "Return, Renewal, Repetition, Nurturing, Wisdom, Philosophy, Travel, Simplicity",
            "bphs_note": "Bridging Gemini and Cancer ('Return of the Light'). Deity Aditi brings nurturing and freedom. Jupiter lordship gives wisdom and philosophy. Symbol bow indicates readiness and focus.",
            "lal_kitab_note": "Governed by Jupiter. Jupiter's effect depends on House 9 ('Pakka Ghar'). Spans Mercury (Gemini) and Moon (Cancer) Rasis. Generally auspicious. Remedies for Jupiter (saffron, gold) enhance good effects."
            },
            {"num": 8, "name": "Pushya", "sanskrit": "Pushya", "devanagari": "पुष्य", "lord": "Saturn", "remainder": 7,
            "deity": "Brihaspati (Guru of Gods)", "symbol": "Cow's Udder, Flower, Arrow, Circle", "start_degree": 93.3333, "end_degree": 106.6666,
            "padas_rashi": ["Cancer"]*4, "padas_navamsha": ["Leo", "Virgo", "Libra", "Scorpio"],
            "syllables": ["हू (Hu)", "हे (He)", "हो (Ho)", "डा (Da)"],
            "gana": "Deva (Divine)", "yoni": "Mesha (Male Sheep)", "nadi": "Madhya (Pitta)", "guna": "Tamasic", "tattva": "Water",
            "motivation": "Dharma", "nature": "Laghu/Kshipra (Light/Swift)",
            "keywords": "Nourishment, Auspiciousness, Spirituality, Care, Wisdom, Stability, Devotion",
            "bphs_note": "Considered the most auspicious Nakshatra ('Flower'). Symbol udder signifies nourishment. Deity Brihaspati brings wisdom. Saturn lordship adds stability and service.",
            "lal_kitab_note": "Governed by Saturn. Saturn's effect depends on House 10 ('Pakka Ghar'). In Moon's sign (Cancer). Can create 'Vish Yoga' (Saturn+Moon effect). Requires careful analysis. Remedies for Saturn may be needed."
            },
            {"num": 9, "name": "Ashlesha", "sanskrit": "Ashlesha", "devanagari": "आश्लेषा", "lord": "Mercury", "remainder": 8,
            "deity": "Nagas (Serpent Deities)", "symbol": "Coiled Serpent", "start_degree": 106.6666, "end_degree": 120.0,
            "padas_rashi": ["Cancer"]*4, "padas_navamsha": ["Sagittarius", "Capricorn", "Aquarius", "Pisces"],
            "syllables": ["डी (Di)", "डू (Du)", "डे (De)", "डो (Do)"],
            "gana": "Rakshasa (Demonic)", "yoni": "Marjara (Male Cat)", "nadi": "Antya (Kapha)", "guna": "Sattvic", "tattva": "Water",
            "motivation": "Dharma", "nature": "Tikshna/Daruna (Sharp/Dreadful)",
            "keywords": "Clinging, Embracing, Intensity, Occult, Wisdom, Poison/Healing, Psychological Depth, Hypnotic",
            "bphs_note": "Represents the serpent energy ('The Clinging Star'). Deity Nagas bring occult wisdom, intensity, and potential danger (poison/healing duality). Mercury lordship gives intellect. A Gandanta point ends here.",
            "lal_kitab_note": "Governed by Mercury. Mercury's effect depends on House 7 ('Pakka Ghar'). In Moon's sign (Cancer). Can indicate sharp, possibly manipulative intellect. Remedies for Mercury may apply."
            },
            {"num": 10, "name": "Magha", "sanskrit": "Magha", "devanagari": "मघा", "lord": "Ketu", "remainder": 0,
            "deity": "Pitrs (Ancestors)", "symbol": "Throne Room, Palanquin", "start_degree": 120.0, "end_degree": 133.3333,
            "padas_rashi": ["Leo"]*4, "padas_navamsha": ["Aries", "Taurus", "Gemini", "Cancer"],
            "syllables": ["मा (Ma)", "मी (Mi)", "मू (Mu)", "मे (Me)"],
            "gana": "Rakshasa (Demonic)", "yoni": "Mushaka (Male Rat)", "nadi": "Antya (Kapha)", "guna": "Tamasic", "tattva": "Fire",
            "motivation": "Artha", "nature": "Ugra/Krura (Fierce/Cruel)",
            "keywords": "Authority, Royalty, Ancestors, Tradition, Power, Ego, Status, Past Glories",
            "bphs_note": "Represents ancestral power and tradition ('The Royal Star'). Symbol throne indicates authority. Ketu lordship connects to past lineage and karma. Falls entirely in Leo (Sun's sign).",
            "lal_kitab_note": "Governed by Ketu. Ketu's effect depends on House 6 ('Pakka Ghar'). In Sun's sign (Leo). Connects strongly to ancestors ('Pitra Rin'). Remedies for Ketu and serving ancestors crucial."
            },
            {"num": 11, "name": "Purva Phalguni", "sanskrit": "Purva Phalguni", "devanagari": "पूर्व फाल्गुनी", "lord": "Venus", "remainder": 1,
            "deity": "Bhaga (God of Fortune/Bliss)", "symbol": "Front legs of a Bed, Hammock, Fig Tree", "start_degree": 133.3333, "end_degree": 146.6666,
            "padas_rashi": ["Leo"]*4, "padas_navamsha": ["Leo", "Virgo", "Libra", "Scorpio"],
            "syllables": ["मो (Mo)", "टा (Ta)", "टी (Ti)", "टू (Tu)"],
            "gana": "Manushya (Human)", "yoni": "Mushaka (Female Rat)", "nadi": "Madhya (Pitta)", "guna": "Rajasic", "tattva": "Fire",
            "motivation": "Kama", "nature": "Ugra/Krura (Fierce/Cruel)",
            "keywords": "Relaxation, Pleasure, Romance, Creativity, Fortune, Social Charm, Leisure",
            "bphs_note": "Represents enjoyment, love, and fortune ('The Former Reddish One'). Symbol bed/hammock indicates relaxation. Venus lordship emphasizes pleasure and relationships.",
            "lal_kitab_note": "Governed by Venus. Venus's effect depends on House 7 ('Pakka Ghar'). In Sun's sign (Leo). Good for enjoyment but needs balance. Remedies for Venus (cow seva, ghee) may apply."
            },
            {"num": 12, "name": "Uttara Phalguni", "sanskrit": "Uttara Phalguni", "devanagari": "उत्तर फाल्गुनी", "lord": "Sun", "remainder": 2,
            "deity": "Aryaman (God of Patronage/Contracts)", "symbol": "Back legs of a Bed, Hammock", "start_degree": 146.6666, "end_degree": 160.0,
            "padas_rashi": ["Leo"]*1 + ["Virgo"]*3, "padas_navamsha": ["Sagittarius", "Capricorn", "Aquarius", "Pisces"],
            "syllables": ["टे (Te)", "टो (To)", "पा (Pa)", "पी (Pi)"],
            "gana": "Manushya (Human)", "yoni": "Go (Male Cow/Ox)", "nadi": "Adi (Vata)", "guna": "Sattvic", "tattva": "Fire",
            "motivation": "Moksha", "nature": "Sthira/Dhruva (Fixed/Permanent)",
            "keywords": "Partnership, Friendship, Contracts, Service, Healing, Generosity, Stability",
            "bphs_note": "Bridging Leo and Virgo ('The Latter Reddish One'). Represents commitments and unions (Aryaman). Sun lordship brings integrity. Virgo portion adds service and analysis.",
            "lal_kitab_note": "Governed by Sun. Sun's effect depends on House 1 ('Pakka Ghar'). Spans Sun (Leo) and Mercury (Virgo) Rasis. Good for commitment and service. Sun remedies may apply."
            },
            {"num": 13, "name": "Hasta", "sanskrit": "Hasta", "devanagari": "हस्त", "lord": "Moon", "remainder": 3,
            "deity": "Savitar (Sun God - Inspiration)", "symbol": "Hand", "start_degree": 160.0, "end_degree": 173.3333,
            "padas_rashi": ["Virgo"]*4, "padas_navamsha": ["Aries", "Taurus", "Gemini", "Cancer"],
            "syllables": ["पू (Pu)", "ष (Sha)", "ण (Na)", "ठ (Tha)"],
            "gana": "Deva (Divine)", "yoni": "Mahisha (Female Buffalo)", "nadi": "Adi (Vata)", "guna": "Rajasic", "tattva": "Earth",
            "motivation": "Moksha", "nature": "Laghu/Kshipra (Light/Swift)",
            "keywords": "Skill, Craftsmanship, Dexterity, Healing, Wit, Punctuality, Practicality",
            "bphs_note": "Represents skill and manifestation ('The Hand'). Deity Savitar brings inspiration. Moon lordship gives dexterity and mental agility. Falls in analytical Virgo.",
            "lal_kitab_note": "Governed by Moon. Moon's effect depends on House 4 ('Pakka Ghar'). In Mercury's sign (Virgo). Excellent for skills and crafts. Remedies for Moon (serving mother) enhance benefits."
            },
            {"num": 14, "name": "Chitra", "sanskrit": "Chitra", "devanagari": "चित्रा", "lord": "Mars", "remainder": 4, # Corrected Devanagari
            "deity": "Tvashtar/Vishwakarma (Celestial Architect)", "symbol": "Bright Jewel, Pearl", "start_degree": 173.3333, "end_degree": 186.6666,
            "padas_rashi": ["Virgo"]*2 + ["Libra"]*2, "padas_navamsha": ["Leo", "Virgo", "Libra", "Scorpio"],
            "syllables": ["पे (Pe)", "पो (Po)", "रा (Ra)", "री (Ri)"],
            "gana": "Rakshasa (Demonic)", "yoni": "Vyaghra (Female Tiger)", "nadi": "Madhya (Pitta)", "guna": "Tamasic", "tattva": "Earth",
            "motivation": "Kama", "nature": "Mridu/Maitra (Soft/Friendly)",
            "keywords": "Beauty, Artistry, Architecture, Charisma, Illusion, Design, Skill in Creation",
            "bphs_note": "Bridging Virgo and Libra ('The Star of Opportunity'). Symbol jewel represents brilliance. Deity Tvashtar brings skill in creation and maya (illusion). Mars lordship gives drive.",
            "lal_kitab_note": "Governed by Mars. Mars's effect depends on House 3/8 ('Pakka Ghar'). Spans Mercury (Virgo) and Venus (Libra) Rasis. Can give artistic talent and charisma. Mars remedies may apply."
            },
            {"num": 15, "name": "Swati", "sanskrit": "Swati", "devanagari": "स्वाति", "lord": "Rahu", "remainder": 5,
            "deity": "Vayu (Wind God)", "symbol": "Young Shoot swaying in wind, Coral, Sword", "start_degree": 186.6666, "end_degree": 200.0,
            "padas_rashi": ["Libra"]*4, "padas_navamsha": ["Sagittarius", "Capricorn", "Aquarius", "Pisces"],
            "syllables": ["रू (Ru)", "रे (Re)", "रो (Ro)", "ता (Ta)"],
            "gana": "Deva (Divine)", "yoni": "Mahisha (Male Buffalo)", "nadi": "Antya (Kapha)", "guna": "Tamasic", "tattva": "Air",
            "motivation": "Artha", "nature": "Chara/Chala (Movable/Changing)",
            "keywords": "Independence, Freedom, Wind, Movement, Diplomacy, Business Acumen, Restlessness",
            "bphs_note": "Represents independence and movement ('The Independent One'). Deity Vayu signifies wind and change. Rahu lordship brings unconventionality and ambition. Falls in Libra (Venus).",
            "lal_kitab_note": "Governed by Rahu. Rahu's effect depends on House 12 ('Pakka Ghar'). In Venus's sign (Libra). Can give success in business/diplomacy but needs grounding. Rahu remedies may apply."
            },
            {"num": 16, "name": "Vishakha", "sanskrit": "Vishakha", "devanagari": "विशाखा", "lord": "Jupiter", "remainder": 6,
            "deity": "Indra-Agni (Chief & Fire God)", "symbol": "Triumphal Archway, Potter's Wheel", "start_degree": 200.0, "end_degree": 213.3333,
            "padas_rashi": ["Libra"]*3 + ["Scorpio"]*1, "padas_navamsha": ["Aries", "Taurus", "Gemini", "Cancer"],
            "syllables": ["ती (Ti)", "तू (Tu)", "ते (Te)", "तो (To)"],
            "gana": "Rakshasa (Demonic)", "yoni": "Vyaghra (Male Tiger)", "nadi": "Antya (Kapha)", "guna": "Sattvic", "tattva": "Air",
            "motivation": "Dharma", "nature": "Misra/Sadharana (Mixed)",
            "keywords": "Purpose, Determination, Focus, Goal-Oriented, Ambition, Patience, Celebration after Victory",
            "bphs_note": "Bridging Libra and Scorpio ('The Star of Purpose'). Symbol archway signifies focus on goals. Deities Indra-Agni bring power and drive. Jupiter lordship adds wisdom to ambition.",
            "lal_kitab_note": "Governed by Jupiter. Jupiter's effect depends on House 9 ('Pakka Ghar'). Spans Venus (Libra) and Mars (Scorpio) Rasis. Can give strong ambition. Jupiter remedies enhance benefits."
            },
            {"num": 17, "name": "Anuradha", "sanskrit": "Anuradha", "devanagari": "अनुराधा", "lord": "Saturn", "remainder": 7,
            "deity": "Mitra (God of Friendship/Partnership)", "symbol": "Triumphal Archway, Lotus Flower, Staff", "start_degree": 213.3333, "end_degree": 226.6666,
            "padas_rashi": ["Scorpio"]*4, "padas_navamsha": ["Leo", "Virgo", "Libra", "Scorpio"],
            "syllables": ["ना (Na)", "नी (Ni)", "नू (Nu)", "ने (Ne)"],
            "gana": "Deva (Divine)", "yoni": "Mriga (Female Deer)", "nadi": "Madhya (Pitta)", "guna": "Tamasic", "tattva": "Water",
            "motivation": "Dharma", "nature": "Mridu/Maitra (Soft/Friendly)",
            "keywords": "Friendship, Cooperation, Devotion, Exploration, Success through Collaboration, Numbers",
            "bphs_note": "Represents friendship and success through alliances ('The Star of Success'). Deity Mitra fosters cooperation. Saturn lordship brings structure and loyalty to relationships.",
            "lal_kitab_note": "Governed by Saturn. Saturn's effect depends on House 10 ('Pakka Ghar'). In Mars's sign (Scorpio). Can make one loyal but potentially rigid. Saturn remedies may be needed."
            },
            {"num": 18, "name": "Jyestha", "sanskrit": "Jyestha", "devanagari": "ज्येष्ठा", "lord": "Mercury", "remainder": 8,
            "deity": "Indra (Chief of Gods)", "symbol": "Earring, Umbrella, Talisman", "start_degree": 226.6666, "end_degree": 240.0,
            "padas_rashi": ["Scorpio"]*4, "padas_navamsha": ["Sagittarius", "Capricorn", "Aquarius", "Pisces"],
            "syllables": ["नो (No)", "या (Ya)", "यी (Yi)", "यू (Yu)"],
            "gana": "Rakshasa (Demonic)", "yoni": "Mriga (Male Deer)", "nadi": "Adi (Vata)", "guna": "Sattvic", "tattva": "Water",
            "motivation": "Artha", "nature": "Tikshna/Daruna (Sharp/Dreadful)",
            "keywords": "Eldest, Seniority, Authority, Power Struggle, Occult, Responsibility, Protection",
            "bphs_note": "Represents seniority and authority ('The Eldest'). Deity Indra brings power but also potential conflict. Mercury lordship gives strategic intellect. A Gandanta point ends here.",
            "lal_kitab_note": "Governed by Mercury. Mercury's effect depends on House 7 ('Pakka Ghar'). In Mars's sign (Scorpio). Can indicate struggles for seniority or clever strategies. Mercury remedies may apply."
            },
            {"num": 19, "name": "Mula", "sanskrit": "Mula", "devanagari": "मूल", "lord": "Ketu", "remainder": 0,
            "deity": "Nirriti (Goddess of Destruction/Dissolution)", "symbol": "Bundle of Roots tied together, Elephant Goad", "start_degree": 240.0, "end_degree": 253.3333,
            "padas_rashi": ["Sagittarius"]*4, "padas_navamsha": ["Aries", "Taurus", "Gemini", "Cancer"],
            "syllables": ["ये (Ye)", "यो (Yo)", "भा (Bha)", "भी (Bhi)"],
            "gana": "Rakshasa (Demonic)", "yoni": "Shwana (Male Dog)", "nadi": "Adi (Vata)", "guna": "Tamasic", "tattva": "Fire",
            "motivation": "Kama", "nature": "Tikshna/Daruna (Sharp/Dreadful)",
            "keywords": "Root, Foundation, Investigation, Destruction, Transformation, Getting to the Core, Occult Research",
            "bphs_note": "Represents the root or core ('The Root'). Deity Nirriti signifies destruction of illusion to find truth. Ketu lordship connects to past lives and deep investigation. A Gandanta point starts here.",
            "lal_kitab_note": "Governed by Ketu. Ketu's effect depends on House 6 ('Pakka Ghar'). In Jupiter's sign (Sagittarius). Can indicate deep investigation or disruption. Ketu remedies (dogs) important."
            },
            {"num": 20, "name": "Purva Ashadha", "sanskrit": "Purva Ashadha", "devanagari": "पूर्वाषाढ़ा", "lord": "Venus", "remainder": 1,
            "deity": "Apas (God of Waters)", "symbol": "Elephant Tusk, Fan, Winnowing Basket", "start_degree": 253.3333, "end_degree": 266.6666,
            "padas_rashi": ["Sagittarius"]*4, "padas_navamsha": ["Leo", "Virgo", "Libra", "Scorpio"],
            "syllables": ["भू (Bhu)", "धा (Dha)", "फा (Pha)", "ढा (Dha)"], # Note: Pha/Fa are often used interchangeably
            "gana": "Manushya (Human)", "yoni": "Vanara (Male Monkey)", "nadi": "Madhya (Pitta)", "guna": "Rajasic", "tattva": "Fire",
            "motivation": "Moksha", "nature": "Ugra/Krura (Fierce/Cruel)",
            "keywords": "Invincible, Victory, Declaration, Purification, Popularity, Ambition, Optimism",
            "bphs_note": "Represents early victory or declaration ('The Invincible Star'). Deity Apas brings purification and flow. Venus lordship gives charm and popularity.",
            "lal_kitab_note": "Governed by Venus. Venus's effect depends on House 7 ('Pakka Ghar'). In Jupiter's sign (Sagittarius). Can give popularity and optimism. Venus remedies may apply."
            },
            {"num": 21, "name": "Uttara Ashadha", "sanskrit": "Uttara Ashadha", "devanagari": "उत्तराषाढ़ा", "lord": "Sun", "remainder": 2,
            "deity": "Vishvadevas (Universal Gods)", "symbol": "Elephant Tusk, Planks of a Bed", "start_degree": 266.6666, "end_degree": 280.0,
            "padas_rashi": ["Sagittarius"]*1 + ["Capricorn"]*3, "padas_navamsha": ["Sagittarius", "Capricorn", "Aquarius", "Pisces"],
            "syllables": ["भे (Bhe)", "भो (Bho)", "जा (Ja)", "जी (Ji)"],
            "gana": "Manushya (Human)", "yoni": "Nakula (Male Mongoose)", "nadi": "Antya (Kapha)", "guna": "Sattvic", "tattva": "Fire",
            "motivation": "Moksha", "nature": "Sthira/Dhruva (Fixed/Permanent)",
            "keywords": "Later Victory, Universality, Duty, Responsibility, Leadership, Structure, Integrity",
            "bphs_note": "Bridging Sagittarius and Capricorn ('The Universal Star'). Represents lasting achievement and duty. Sun lordship gives leadership. Capricorn portion adds structure and discipline.",
            "lal_kitab_note": "Governed by Sun. Sun's effect depends on House 1 ('Pakka Ghar'). Spans Jupiter (Sagittarius) and Saturn (Capricorn) Rasis. Can give leadership roles. Sun remedies may apply."
            },
            {"num": 22, "name": "Shravana", "sanskrit": "Shravana", "devanagari": "श्रवण", "lord": "Moon", "remainder": 3,
            "deity": "Vishnu (Preserver)", "symbol": "Ear, Three Footprints", "start_degree": 280.0, "end_degree": 293.3333,
            "padas_rashi": ["Capricorn"]*4, "padas_navamsha": ["Aries", "Taurus", "Gemini", "Cancer"],
            "syllables": ["खी (Khi)", "खू (Khu)", "खे (Khe)", "खो (Kho)"],
            "gana": "Deva (Divine)", "yoni": "Vanara (Female Monkey)", "nadi": "Antya (Kapha)", "guna": "Rajasic", "tattva": "Earth",
            "motivation": "Artha", "nature": "Chara/Chala (Movable/Changing)",
            "keywords": "Listening, Learning, Tradition, Knowledge, Travel, Communication, Organization",
            "bphs_note": "Represents hearing and learning ('The Star of Learning'). Symbol ear emphasizes listening. Deity Vishnu links to preservation of knowledge. Moon lordship gives receptivity.",
            "lal_kitab_note": "Governed by Moon. Moon's effect depends on House 4 ('Pakka Ghar'). In Saturn's sign (Capricorn). Can indicate learning from tradition but potential emotional dryness. Moon remedies may apply."
            },
            {"num": 23, "name": "Dhanishta", "sanskrit": "Dhanishta", "devanagari": "धनिष्ठा", "lord": "Mars", "remainder": 4,
            "deity": "Ashta Vasus (Eight Gods of Abundance)", "symbol": "Drum (Damaru), Flute", "start_degree": 293.3333, "end_degree": 306.6666,
            "padas_rashi": ["Capricorn"]*2 + ["Aquarius"]*2, "padas_navamsha": ["Leo", "Virgo", "Libra", "Scorpio"],
            "syllables": ["गा (Ga)", "गी (Gi)", "गू (Gu)", "गे (Ge)"],
            "gana": "Rakshasa (Demonic)", "yoni": "Simha (Female Lion)", "nadi": "Madhya (Pitta)", "guna": "Tamasic", "tattva": "Earth",
            "motivation": "Dharma", "nature": "Chara/Chala (Movable/Changing)",
            "keywords": "Wealth, Abundance, Rhythm, Music, Fame, Movement, Organization, Group Work",
            "bphs_note": "Bridging Capricorn and Aquarius ('The Star of Symphony'). Represents wealth and rhythm. Deities Vasus bring abundance. Mars lordship gives energy. Aquarius portion adds collective focus.",
            "lal_kitab_note": "Governed by Mars. Mars's effect depends on House 3/8 ('Pakka Ghar'). Spans Saturn's signs (Capricorn/Aquarius). Can bring wealth through effort. Mars remedies may apply."
            },
            {"num": 24, "name": "Shatabhisha", "sanskrit": "Shatabhisha", "devanagari": "शतभिषा", "lord": "Rahu", "remainder": 5,
            "deity": "Varuna (God of Cosmic Waters/Sky)", "symbol": "Empty Circle, 100 Physicians/Flowers/Stars", "start_degree": 306.6666, "end_degree": 320.0,
            "padas_rashi": ["Aquarius"]*4, "padas_navamsha": ["Sagittarius", "Capricorn", "Aquarius", "Pisces"],
            "syllables": ["गो (Go)", "सा (Sa)", "सी (Si)", "सू (Su)"],
            "gana": "Rakshasa (Demonic)", "yoni": "Ashwa (Female Horse)", "nadi": "Adi (Vata)", "guna": "Tamasic", "tattva": "Air",
            "motivation": "Dharma", "nature": "Chara/Chala (Movable/Changing)",
            "keywords": "Healing, Veiling, Secrecy, Mysticism, Technology, Large Networks, Solitude",
            "bphs_note": "Represents healing on a large scale ('The Veiling Star' or '100 Healers'). Deity Varuna brings cosmic law and mystery. Rahu lordship emphasizes secrets, technology, and unconventional approaches.",
            "lal_kitab_note": "Governed by Rahu. Rahu's effect depends on House 12 ('Pakka Ghar'). In Saturn's sign (Aquarius). Can indicate healing abilities, foreign connections, or secrets. Rahu remedies crucial."
            },
            {"num": 25, "name": "Purva Bhadrapada", "sanskrit": "Purva Bhadrapada", "devanagari": "पूर्व भाद्रपद", "lord": "Jupiter", "remainder": 6,
            "deity": "Aja Ekapada (One-footed Goat/Form of Shiva)", "symbol": "Front legs of a Funeral Cot, Man with Two Faces, Sword", "start_degree": 320.0, "end_degree": 333.3333,
            "padas_rashi": ["Aquarius"]*3 + ["Pisces"]*1, "padas_navamsha": ["Aries", "Taurus", "Gemini", "Cancer"],
            "syllables": ["से (Se)", "सो (So)", "दा (Da)", "दी (Di)"],
            "gana": "Manushya (Human)", "yoni": "Simha (Male Lion)", "nadi": "Adi (Vata)", "guna": "Sattvic", "tattva": "Air",
            "motivation": "Artha", "nature": "Ugra/Krura (Fierce/Cruel)",
            "keywords": "Fiery, Intense, Passionate, Transformation, Occult, Duality, Sacrifice, Penance",
            "bphs_note": "Bridging Aquarius and Pisces ('The Former Lucky Feet'). Represents intense, fiery energy. Deity Aja Ekapada signifies penance and transformation. Jupiter lordship adds philosophical depth.",
            "lal_kitab_note": "Governed by Jupiter. Jupiter's effect depends on House 9 ('Pakka Ghar'). Spans Saturn (Aquarius) and Jupiter (Pisces) Rasis. Can give intense nature. Jupiter remedies enhance benefits."
            },
            {"num": 26, "name": "Uttara Bhadrapada", "sanskrit": "Uttara Bhadrapada", "devanagari": "उत्तर भाद्रपद", "lord": "Saturn", "remainder": 7,
            "deity": "Ahir Budhnya (Serpent of the Deep)", "symbol": "Back legs of a Funeral Cot, Twins, Serpent in Water", "start_degree": 333.3333, "end_degree": 346.6666,
            "padas_rashi": ["Pisces"]*4, "padas_navamsha": ["Leo", "Virgo", "Libra", "Scorpio"],
            "syllables": ["दू (Du)", "थ (Tha)", "झ (Jha)", "ञ (Na)"], # Some use 'Da' or 'Nya' for last
            "gana": "Manushya (Human)", "yoni": "Go (Female Cow)", "nadi": "Madhya (Pitta)", "guna": "Tamasic", "tattva": "Water",
            "motivation": "Kama", "nature": "Sthira/Dhruva (Fixed/Permanent)",
            "keywords": "Wisdom, Discipline, Renunciation, Kundalini, Deep Knowledge, Stability, Patience, Protection",
            "bphs_note": "Represents deep wisdom and stability ('The Latter Lucky Feet'). Deity Ahir Budhnya brings kundalini energy and depth. Saturn lordship gives discipline and patience.",
            "lal_kitab_note": "Governed by Saturn. Saturn's effect depends on House 10 ('Pakka Ghar'). In Jupiter's sign (Pisces). Can give deep wisdom but requires patience. Saturn remedies may apply."
            },
            {"num": 27, "name": "Revati", "sanskrit": "Revati", "devanagari": "रेवती", "lord": "Mercury", "remainder": 8,
            "deity": "Pushan (Nourisher, Protector of Travelers/Flocks)", "symbol": "Fish swimming in the sea, Drum", "start_degree": 346.6666, "end_degree": 360.0,
            "padas_rashi": ["Pisces"]*4, "padas_navamsha": ["Sagittarius", "Capricorn", "Aquarius", "Pisces"],
            "syllables": ["दे (De)", "दो (Do)", "चा (Cha)", "ची (Chi)"],
            "gana": "Deva (Divine)", "yoni": "Gaja (Female Elephant)", "nadi": "Antya (Kapha)", "guna": "Sattvic", "tattva": "Water",
            "motivation": "Moksha", "nature": "Mridu/Maitra (Soft/Friendly)",
            "keywords": "Nourishment, Protection, Travel, Wealth, Completion, Spirituality, Compassion",
            "bphs_note": "The final Nakshatra ('The Wealthy'). Represents nourishment, safety in travel, and completion. Deity Pushan guides souls. Mercury lordship gives intellect. A Gandanta point ends here.",
            "lal_kitab_note": "Governed by Mercury. Mercury's effect depends on House 7 ('Pakka Ghar'). In Jupiter's sign (Pisces). Often considered good for wealth and protection. Mercury remedies may apply."
            }
        ]
    @staticmethod 
    def get_all_nakshatras_with_long() -> List[Dict[str, Any]]:
        """
        Returns Nakshatra data including precise longitude spans.
        Each Nakshatra spans 13 degrees 20 minutes (13.333333 degrees).
        *** NOTE: You need to fill in the data for ALL 27 Nakshatras here ***
        """
        nakshatras = [
            {"num": 1, "name": "Ashwini", "sanskrit": "Ashwini", "devanagari": "अश्विनी", "lord": "Ketu", "remainder": 0,
            "longitude_start": 0.0, "longitude_end": 13.333333,
            "deity": "Ashwini Kumaras", "symbol": "Horse's Head", "span": 13.333333, # Added span
            "syllables": ["चू (Chu)", "चे (Che)", "चो (Cho)", "ला (La)"]}, # Add other attributes if needed
            {"num": 2, "name": "Bharani", "sanskrit": "Bharani", "devanagari": "भरणी", "lord": "Venus", "remainder": 1,
            "longitude_start": 13.333333, "longitude_end": 26.666666,
            "deity": "Yama", "symbol": "Yoni", "span": 13.333333,
            "syllables": ["ली (Li)", "लू (Lu)", "ले (Le)", "लो (Lo)"]},
            {"num": 3, "name": "Krittika", "sanskrit": "Krittika", "devanagari": "कृत्तिका", "lord": "Sun", "remainder": 2,
            "longitude_start": 26.666666, "longitude_end": 40.0,
            "deity": "Agni", "symbol": "Knife/Flame", "span": 13.333334, # Adjusted slightly for 40.0 end
            "syllables": ["अ (A)", "ई (I)", "उ (U)", "ए (E)"]},
            {"num": 4, "name": "Rohini", "sanskrit": "Rohini", "devanagari": "रोहिणी", "lord": "Moon", "remainder": 3,
            "longitude_start": 40.0, "longitude_end": 53.333333,
            "deity": "Brahma", "symbol": "Cart/Chariot", "span": 13.333333,
            "syllables": ["ओ (O)", "वा (Va)", "वी (Vi)", "वू (Vu)"]},
            {"num": 5, "name": "Mrigashira", "sanskrit": "Mrigashira", "devanagari": "मृगशिरा", "lord": "Mars", "remainder": 4,
            "longitude_start": 53.333333, "longitude_end": 66.666666,
            "deity": "Soma", "symbol": "Deer's Head", "span": 13.333333,
            "syllables": ["वे (Ve)", "वो (Vo)", "का (Ka)", "की (Ki)"]},
            {"num": 6, "name": "Ardra", "sanskrit": "Ardra", "devanagari": "आर्द्रा", "lord": "Rahu", "remainder": 5,
            "longitude_start": 66.666666, "longitude_end": 80.0,
            "deity": "Rudra", "symbol": "Teardrop/Diamond", "span": 13.333334,
            "syllables": ["कू (Ku)", "घ (Gha)", "ङ (Na)", "छ (Chha)"]},
            {"num": 7, "name": "Punarvasu", "sanskrit": "Punarvasu", "devanagari": "पुनर्वसु", "lord": "Jupiter", "remainder": 6,
            "longitude_start": 80.0, "longitude_end": 93.333333,
            "deity": "Aditi", "symbol": "Bow & Quiver", "span": 13.333333,
            "syllables": ["के (Ke)", "को (Ko)", "हा (Ha)", "ही (Hi)"]},
            {"num": 8, "name": "Pushya", "sanskrit": "Pushya", "devanagari": "पुष्य", "lord": "Saturn", "remainder": 7,
            "longitude_start": 93.333333, "longitude_end": 106.666666,
            "deity": "Brihaspati", "symbol": "Cow's Udder/Flower", "span": 13.333333,
            "syllables": ["हू (Hu)", "हे (He)", "हो (Ho)", "डा (Da)"]},
            {"num": 9, "name": "Ashlesha", "sanskrit": "Ashlesha", "devanagari": "आश्लेषा", "lord": "Mercury", "remainder": 8,
            "longitude_start": 106.666666, "longitude_end": 120.0,
            "deity": "Nagas", "symbol": "Coiled Serpent", "span": 13.333334,
            "syllables": ["डी (Di)", "डू (Du)", "डे (De)", "डो (Do)"]},
            {"num": 10, "name": "Magha", "sanskrit": "Magha", "devanagari": "मघा", "lord": "Ketu", "remainder": 0,
            "longitude_start": 120.0, "longitude_end": 133.333333,
            "deity": "Pitrs", "symbol": "Throne Room", "span": 13.333333,
            "syllables": ["मा (Ma)", "मी (Mi)", "मू (Mu)", "मे (Me)"]},
            {"num": 11, "name": "Purva Phalguni", "sanskrit": "Purva Phalguni", "devanagari": "पूर्व फाल्गुनी", "lord": "Venus", "remainder": 1,
            "longitude_start": 133.333333, "longitude_end": 146.666666,
            "deity": "Bhaga", "symbol": "Front legs of Bed", "span": 13.333333,
            "syllables": ["मो (Mo)", "टा (Ta)", "टी (Ti)", "टू (Tu)"]},
            {"num": 12, "name": "Uttara Phalguni", "sanskrit": "Uttara Phalguni", "devanagari": "उत्तर फाल्गुनी", "lord": "Sun", "remainder": 2,
            "longitude_start": 146.666666, "longitude_end": 160.0,
            "deity": "Aryaman", "symbol": "Back legs of Bed", "span": 13.333334,
            "syllables": ["टे (Te)", "टो (To)", "पा (Pa)", "पी (Pi)"]},
            {"num": 13, "name": "Hasta", "sanskrit": "Hasta", "devanagari": "हस्त", "lord": "Moon", "remainder": 3,
            "longitude_start": 160.0, "longitude_end": 173.333333,
            "deity": "Savitar", "symbol": "Hand", "span": 13.333333,
            "syllables": ["पू (Pu)", "ष (Sha)", "ण (Na)", "ठ (Tha)"]},
            {"num": 14, "name": "Chitra", "sanskrit": "Chitra", "devanagari": "चित्रा", "lord": "Mars", "remainder": 4,
            "longitude_start": 173.333333, "longitude_end": 186.666666,
            "deity": "Tvashtar", "symbol": "Bright Jewel/Pearl", "span": 13.333333,
            "syllables": ["पे (Pe)", "पो (Po)", "रा (Ra)", "री (Ri)"]},
            {"num": 15, "name": "Swati", "sanskrit": "Swati", "devanagari": "स्वाति", "lord": "Rahu", "remainder": 5,
            "longitude_start": 186.666666, "longitude_end": 200.0,
            "deity": "Vayu", "symbol": "Young Shoot/Sword", "span": 13.333334,
            "syllables": ["रू (Ru)", "रे (Re)", "रो (Ro)", "ता (Ta)"]},
            {"num": 16, "name": "Vishakha", "sanskrit": "Vishakha", "devanagari": "विशाखा", "lord": "Jupiter", "remainder": 6,
            "longitude_start": 200.0, "longitude_end": 213.333333,
            "deity": "Indra-Agni", "symbol": "Triumphal Archway", "span": 13.333333,
            "syllables": ["ती (Ti)", "तू (Tu)", "ते (Te)", "तो (To)"]},
            {"num": 17, "name": "Anuradha", "sanskrit": "Anuradha", "devanagari": "अनुराधा", "lord": "Saturn", "remainder": 7,
            "longitude_start": 213.333333, "longitude_end": 226.666666,
            "deity": "Mitra", "symbol": "Lotus Flower/Archway", "span": 13.333333,
            "syllables": ["ना (Na)", "नी (Ni)", "नू (Nu)", "ने (Ne)"]},
            {"num": 18, "name": "Jyestha", "sanskrit": "Jyestha", "devanagari": "ज्येष्ठा", "lord": "Mercury", "remainder": 8,
            "longitude_start": 226.666666, "longitude_end": 240.0,
            "deity": "Indra", "symbol": "Earring/Umbrella", "span": 13.333334,
            "syllables": ["नो (No)", "या (Ya)", "यी (Yi)", "यू (Yu)"]},
            {"num": 19, "name": "Mula", "sanskrit": "Mula", "devanagari": "मूल", "lord": "Ketu", "remainder": 0,
            "longitude_start": 240.0, "longitude_end": 253.333333,
            "deity": "Nirriti", "symbol": "Bundle of Roots", "span": 13.333333,
            "syllables": ["ये (Ye)", "यो (Yo)", "भा (Bha)", "भी (Bhi)"]},
            {"num": 20, "name": "Purva Ashadha", "sanskrit": "Purva Ashadha", "devanagari": "पूर्वाषाढ़ा", "lord": "Venus", "remainder": 1,
            "longitude_start": 253.333333, "longitude_end": 266.666666,
            "deity": "Apas", "symbol": "Elephant Tusk/Fan", "span": 13.333333,
            "syllables": ["भू (Bhu)", "धा (Dha)", "फा (Pha)", "ढा (Dha)"]},
            {"num": 21, "name": "Uttara Ashadha", "sanskrit": "Uttara Ashadha", "devanagari": "उत्तराषाढ़ा", "lord": "Sun", "remainder": 2,
            "longitude_start": 266.666666, "longitude_end": 280.0,
            "deity": "Vishvadevas", "symbol": "Elephant Tusk/Planks", "span": 13.333334,
            "syllables": ["भे (Bhe)", "भो (Bho)", "जा (Ja)", "जी (Ji)"]},
            {"num": 22, "name": "Shravana", "sanskrit": "Shravana", "devanagari": "श्रवण", "lord": "Moon", "remainder": 3,
            "longitude_start": 280.0, "longitude_end": 293.333333,
            "deity": "Vishnu", "symbol": "Ear/Footprints", "span": 13.333333,
            "syllables": ["खी (Khi)", "खू (Khu)", "खे (Khe)", "खो (Kho)"]},
            {"num": 23, "name": "Dhanishta", "sanskrit": "Dhanishta", "devanagari": "धनिष्ठा", "lord": "Mars", "remainder": 4,
            "longitude_start": 293.333333, "longitude_end": 306.666666,
            "deity": "Ashta Vasus", "symbol": "Drum/Flute", "span": 13.333333,
            "syllables": ["गा (Ga)", "गी (Gi)", "गू (Gu)", "गे (Ge)"]},
            {"num": 24, "name": "Shatabhisha", "sanskrit": "Shatabhisha", "devanagari": "शतभिषा", "lord": "Rahu", "remainder": 5,
            "longitude_start": 306.666666, "longitude_end": 320.0,
            "deity": "Varuna", "symbol": "Empty Circle/100 Flowers", "span": 13.333334,
            "syllables": ["गो (Go)", "सा (Sa)", "सी (Si)", "सू (Su)"]},
            {"num": 25, "name": "Purva Bhadrapada", "sanskrit": "Purva Bhadrapada", "devanagari": "पूर्व भाद्रपद", "lord": "Jupiter", "remainder": 6,
            "longitude_start": 320.0, "longitude_end": 333.333333,
            "deity": "Aja Ekapada", "symbol": "Front legs of Cot/Sword", "span": 13.333333,
            "syllables": ["से (Se)", "सो (So)", "दा (Da)", "दी (Di)"]},
            {"num": 26, "name": "Uttara Bhadrapada", "sanskrit": "Uttara Bhadrapada", "devanagari": "उत्तर भाद्रपद", "lord": "Saturn", "remainder": 7,
            "longitude_start": 333.333333, "longitude_end": 346.666666,
            "deity": "Ahir Budhnya", "symbol": "Back legs of Cot/Serpent", "span": 13.333333,
            "syllables": ["दू (Du)", "थ (Tha)", "झ (Jha)", "ञ (Na)"]},
            {"num": 27, "name": "Revati", "sanskrit": "Revati", "devanagari": "रेवती", "lord": "Mercury", "remainder": 8,
            "longitude_start": 346.666666, "longitude_end": 360.0,
            "deity": "Pushan", "symbol": "Fish/Drum", "span": 13.333334,
            "syllables": ["दे (De)", "दो (Do)", "चा (Cha)", "ची (Chi)"]},
        ]
        # You might want to add other details like Gana, Yoni, Nadi etc. here as well
        return nakshatras

    @staticmethod

    def get_all_rashis() -> List[Dict[str, Any]]:
        """
        Returns a list of all 12 Rashis (Zodiac Signs) with their
        key attributes (lord, element, modality) and advanced
        details from BPHS and Lal Kitab.

        Returns:
            list: A list of dictionaries, where each dictionary is a rashi.
        """
        return [
            {"name": "Aries", "sanskrit": "Mesha", "devanagari": "मेष", "lord": "Mars", "tattva": "Fire (Agni)",
            "modality": "Movable (Chara)", "gender": "Male (Odd)", "kalapurusha": "Head", "rising": "Shirshodaya (Rises with Head)",
            "nature": "Kshatriya (Warrior), Quadruped", "direction": "East",
            "bphs_special": {
                "exaltation": "Sun (10°)",
                "debilitation": "Saturn (20°)",
                "mooltrikona": "Mars (0°-12°)"
            },
            "lal_kitab_note": "Considered the 'Lagna' of the Kalapurusha (House 1). Energy of self, destiny, and new beginnings. Sun's exaltation here promises high status. Mars here is 'Mangal Nek' (good Mars).",
            "description": "Represents initiative, courage, impulsiveness, and the 'spark' of life."
            },
            {"name": "Taurus", "sanskrit": "Vrishabha", "devanagari": "वृषभ", "lord": "Venus", "tattva": "Earth (Prithvi)",
            "modality": "Fixed (Sthira)", "gender": "Female (Even)", "kalapurusha": "Face & Neck", "rising": "Prishtodaya (Rises with Back)",
            "nature": "Vaishya (Merchant), Quadruped", "direction": "South",
            "bphs_special": {
                "exaltation": "Moon (3°)",
                "debilitation": "Ketu (Classical)",
                "mooltrikona": "Moon (4°-30°)"
            },
            "lal_kitab_note": "Energy of House 2. Represents wealth (dhana), family (kutumba), and speech. Rahu is considered exalted here. A strong Venus here gives immense material comforts.",
            "description": "Represents stability, material resources, sensuality, and determination."
            },
            {"name": "Gemini", "sanskrit": "Mithuna", "devanagari": "मिथुन", "lord": "Mercury", "tattva": "Air (Vayu)",
            "modality": "Dual (Dwiswabhava)", "gender": "Male (Odd)", "kalapurusha": "Arms & Shoulders", "rising": "Shirshodaya (Rises with Head)",
            "nature": "Shudra (Service), Biped (Human)", "direction": "West",
            "bphs_special": {
                "exaltation": "Rahu (Classical)",
                "debilitation": "Ketu (Classical)",
                "mooltrikona": "None"
            },
            "lal_kitab_note": "Energy of House 3. Represents siblings, courage, and communication. Mercury (Budh) and Rahu are friends; Rahu's exaltation here can give cleverness and media success.",
            "description": "Represents communication, intellect, adaptability, and duality."
            },
            {"name": "Cancer", "sanskrit": "Karka", "devanagari": "कर्क", "lord": "Moon", "tattva": "Water (Jala)",
            "modality": "Movable (Chara)", "gender": "Female (Even)", "kalapurusha": "Heart & Chest", "rising": "Prishtodaya (Rises with Back)",
            "nature": "Brahmin (Priest), Keeta (Insect/Reptile)", "direction": "North",
            "bphs_special": {
                "exaltation": "Jupiter (5°)",
                "debilitation": "Mars (28°)",
                "mooltrikona": "None"
            },
            "lal_kitab_note": "Energy of House 4. Represents mother, home, and emotions. Jupiter's exaltation here is paramount, granting great wisdom, happiness, and 'Gajakesari' results.",
            "description": "Represents emotion, nurturing, the inner world, and domesticity."
            },
            {"name": "Leo", "sanskrit": "Simha", "devanagari": "सिंह", "lord": "Sun", "tattva": "Fire (Agni)",
            "modality": "Fixed (Sthira)", "gender": "Male (Odd)", "kalapurusha": "Stomach & Upper Abdomen", "rising": "Shirshodaya (Rises with Head)",
            "nature": "Kshatriya (Warrior), Quadruped", "direction": "East",
            "bphs_special": {
                "exaltation": "None",
                "debilitation": "None",
                "mooltrikona": "Sun (0°-20°)"
            },
            "lal_kitab_note": "Energy of House 5. Represents progeny, creativity, and 'Sarkar' (government). The Sun's own 'throne'. A strong Sun here gives authority and creative intelligence.",
            "description": "Represents self-expression, leadership, creative power, and royalty."
            },
            {"name": "Virgo", "sanskrit": "Kanya", "devanagari": "कन्या", "lord": "Mercury", "tattva": "Earth (Prithvi)",
            "modality": "Dual (Dwiswabhava)", "gender": "Female (Even)", "kalapurusha": "Hips & Lower Abdomen", "rising": "Shirshodaya (Rises with Head)",
            "nature": "Vaishya (Merchant), Biped (Human)", "direction": "South",
            "bphs_special": {
                "exaltation": "Mercury (15°)",
                "debilitation": "Venus (27°)",
                "mooltrikona": "Mercury (16°-20°)"
            },
            "lal_kitab_note": "Energy of House 6. Represents debts, diseases, and enemies (Ripu). Mercury's exaltation here gives sharp analytical skill. Debilitated Venus ('Neecha Shukra') here is problematic.",
            "description": "Represents service, analysis, perfection, and health."
            },
            {"name": "Libra", "sanskrit": "Tula", "devanagari": "तुला", "lord": "Venus", "tattva": "Air (Vayu)",
            "modality": "Movable (Chara)", "gender": "Male (Odd)", "kalapurusha": "Groin & Lower Back", "rising": "Shirshodaya (Rises with Head)",
            "nature": "Shudra (Service), Biped (Human)", "direction": "West",
            "bphs_special": {
                "exaltation": "Saturn (20°)",
                "debilitation": "Sun (10°)",
                "mooltrikona": "Venus (0°-15°)"
            },
            "lal_kitab_note": "Energy of House 7. Represents marriage, partnership, and worldly balance. Saturn's exaltation ('Uchcha Shani') here gives great judgment and public life, but can delay marriage.",
            "description": "Represents harmony, relationships, justice, and diplomacy."
            },
            {"name": "Scorpio", "sanskrit": "Vrischika", "devanagari": "वृश्चिक", "lord": "Mars", "tattva": "Water (Jala)",
            "modality": "Fixed (Sthira)", "gender": "Female (Even)", "kalapurusha": "Private Parts", "rising": "Shirshodaya (Rises with Head)",
            "nature": "Brahmin (Priest), Keeta (Insect)", "direction": "North",
            "bphs_special": {
                "exaltation": "Ketu (Classical)",
                "debilitation": "Moon (3°)",
                "mooltrikona": "None"
            },
            "lal_kitab_note": "Energy of House 8. Represents death, inheritance, and hidden knowledge. Mars' 'watery' sign. Ketu is considered exalted here, giving deep intuitive and occult abilities.",
            "description": "Represents transformation, intensity, occultism, and hidden power."
            },
            {"name": "Sagittarius", "sanskrit": "Dhanu", "devanagari": "धनु", "lord": "Jupiter", "tattva": "Fire (Agni)",
            "modality": "Dual (Dwiswabhava)", "gender": "Male (Odd)", "kalapurusha": "Thighs", "rising": "Prishtodaya (Rises with Back)",
            "nature": "Kshatriya (Warrior), Biped/Quadruped", "direction": "East",
            "bphs_special": {
                "exaltation": "Ketu (Classical)",
                "debilitation": "Rahu (Classical)",
                "mooltrikona": "Jupiter (0°-10°)"
            },
            "lal_kitab_note": "Energy of House 9. Represents luck (Bhagya), father, and dharma. This is Jupiter's 'throne' (Mooltrikona). Ketu's exaltation here gives deep spiritual insight.",
            "description": "Represents wisdom, expansion, higher truth, and optimism."
            },
            {"name": "Capricorn", "sanskrit": "Makara", "devanagari": "मकर", "lord": "Saturn", "tattva": "Earth (Prithvi)",
            "modality": "Movable (Chara)", "gender": "Female (Even)", "kalapurusha": "Knees", "rising": "Prishtodaya (Rises with Back)",
            "nature": "Vaishya (Merchant), Jala-chara (Watery)", "direction": "South",
            "bphs_special": {
                "exaltation": "Mars (28°)",
                "debilitation": "Jupiter (5°)",
                "mooltrikona": "None"
            },
            "lal_kitab_note": "Energy of House 10. Represents karma, career, and public status. Saturn's own house. Mars' exaltation ('Uchcha Mangal') here creates a powerful, relentless worker (Karmayogi).",
            "description": "Represents structure, discipline, public life, and achievement."
            },
            {"name": "Aquarius", "sanskrit": "Kumbha", "devanagari": "कुम्भ", "lord": "Saturn", "tattva": "Air (Vayu)",
            "modality": "Fixed (Sthira)", "gender": "Male (Odd)", "kalapurusha": "Calves & Ankles", "rising": "Shirshodaya (Rises with Head)",
            "nature": "Shudra (Service), Biped (Human)", "direction": "West",
            "bphs_special": {
                "exaltation": "None",
                "debilitation": "None",
                "mooltrikona": "Saturn (0°-20°)"
            },
            "lal_kitab_note": "Energy of House 11. Represents gains (Labha), friends, and society. This is Saturn's Mooltrikona or 'throne'. Rahu is also considered very powerful here, giving gains from new-age tech.",
            "description": "Represents innovation, humanity, collective ideals, and gains."
            },
            {"name": "Pisces", "sanskrit": "Meena", "devanagari": "मीन", "lord": "Jupiter", "tattva": "Water (Jala)",
            "modality": "Dual (Dwiswabhava)", "gender": "Female (Even)", "kalapurusha": "Feet", "rising": "Ubhayodaya (Rises Both Ways)",
            "nature": "Brahmin (Priest), Jala-chara (Fish)", "direction": "North",
            "bphs_special": {
                "exaltation": "Venus (27°)",
                "debilitation": "Mercury (15°)",
                "mooltrikona": "None"
            },
            "lal_kitab_note": "Energy of House 12. Represents expenses, spirituality, and 'Moksha' (liberation). Venus' exaltation ('Uchcha Shukra') here gives high-end luxury and sensual pleasures.",
            "description": "Represents spirituality, dissolution, compassion, and universal consciousness."
            }
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


def get_planet_notes(planet_name: str, app_instance: 'AstroVighatiElite') -> tuple[str, str]:
    """Gets BPHS and Lal Kitab notes for a planet."""
    # Ensure get_all_planets() is accessible via app_instance.astro_data
    if hasattr(app_instance, 'astro_data') and hasattr(app_instance.astro_data, 'get_all_planets'):
        planet_data = next((p for p in app_instance.astro_data.get_all_planets() if p['name'] == planet_name), None)
        if planet_data:
            return planet_data.get('bphs_note', 'N/A'), planet_data.get('lal_kitab_note', 'N/A')
    return 'N/A', 'N/A'


class DashaTimelineTab(ttk.Frame):
    """
    This class defines the "Dasha Timeline" tab with precise calculations.
    Calculates and displays Vimshottari Dasha sequence (Mahadasha & Antardasha)
    based on the Moon's exact longitude at birth. Requires 'python-dateutil'.
    """
    def __init__(self, parent: ttk.Notebook, app: 'AstroVighatiElite') -> None:
        super().__init__(parent)
        self.app = app
        # --- FIX: Ensure Nakshatra data is loaded via the app instance ---
        if hasattr(self.app, 'astro_data') and hasattr(self.app.astro_data, 'get_all_nakshatras_with_long'):
            self.nakshatra_data = self.app.astro_data.get_all_nakshatras_with_long()
        else:
            # Fallback or error handling if the method isn't found
            messagebox.showerror("Data Error", "Nakshatra longitude data method not found in app instance.")
            self.nakshatra_data = [] # Prevent further errors

        # --- Dasha System Constants ---
        self.dasha_periods: Dict[str, int] = {
            "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
            "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17
        }
        self.planet_order: List[str] = list(self.dasha_periods.keys())
        self.total_dasha_cycle = sum(self.dasha_periods.values()) # 120

        # --- Define theme colors HERE ---
        self.theme_bg = "#2e2e2e"       # Main background
        self.theme_fg = "#ffffff"       # Main text color
        self.select_bg = "#005f9e"      # Selection highlight background
        self.header_fg = "#ffcc66"      # Header text color
        self.alt_row_color = "#3a3a3a"  # Alternate row color for Treeview

        self.create_styles()
        self.create_ui()

    def create_styles(self):
        style = ttk.Style()
        style.configure("Dasha.Treeview", rowheight=25)
        # --- FIX: Ensure Treeview respects theme background ---
        style.configure("Dasha.Treeview", background=self.theme_bg, fieldbackground=self.theme_bg, foreground=self.theme_fg)
        style.configure("Dasha.Treeview.Heading", font=('Segoe UI', 10, 'bold'))
        style.map("Dasha.Treeview",
                  background=[('selected', self.select_bg)],
                  foreground=[('selected', self.theme_fg)])
        # Tag for Mahadasha rows (bold font)
        style.configure("MahadashaRow.Treeview", font=('Segoe UI', 10, 'bold'))
        # Optional: You can add a specific background for Mahadasha rows too
        # style.configure("MahadashaRow.Treeview", background=self.alt_row_color) # Example

    def create_ui(self) -> None:
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(expand=True, fill='both')

        paned = ttk.PanedWindow(main_frame, orient='vertical')
        paned.pack(expand=True, fill='both')

        # --- Input Panel ---
        input_outer_frame = ttk.Frame(paned)
        paned.add(input_outer_frame, weight=0)

        ttk.Label(input_outer_frame, text="📊 VIMSHOTTARI DASHA (विंशोत्तरी दशा)",
                  style='Title.TLabel').pack(pady=(0, 15))

        input_frame = ttk.LabelFrame(input_outer_frame, text="Precise Birth Details", padding=15)
        input_frame.pack(fill='x')
        input_frame.grid_columnconfigure(1, weight=1)
        input_frame.grid_columnconfigure(3, weight=0) # Adjust weights for better spacing
        input_frame.grid_columnconfigure(4, weight=0)
        input_frame.grid_columnconfigure(6, weight=0)
        input_frame.grid_columnconfigure(8, weight=1) # Let last entry expand a bit


        # Birth Date & Time
        ttk.Label(input_frame, text="Birth Date:").grid(row=0, column=0, sticky='w', pady=5, padx=5)
        self.birth_date_var = tk.StringVar(value=datetime.now().strftime("%d-%b-%Y"))
        ttk.Entry(input_frame, textvariable=self.birth_date_var, width=12).grid(row=0, column=1, sticky='ew', padx=5)

        ttk.Label(input_frame, text="Birth Time (24hr):").grid(row=0, column=2, sticky='w', pady=5, padx=5)
        self.birth_time_var = tk.StringVar(value=datetime.now().strftime("%H:%M:%S"))
        ttk.Entry(input_frame, textvariable=self.birth_time_var, width=10).grid(row=0, column=3, columnspan=5, sticky='ew', padx=5) # Span time entry

        # Moon Nakshatra & Longitude
        ttk.Label(input_frame, text="Moon Nakshatra:").grid(row=1, column=0, sticky='w', pady=5, padx=5)
        self.moon_nak_var = tk.StringVar()
        # --- FIX: Ensure nak_values uses the correct data source ---
        nak_values = [f"{n['num']}. {n['name']}" for n in self.nakshatra_data] if self.nakshatra_data else []
        self.nak_combo = ttk.Combobox(input_frame, textvariable=self.moon_nak_var, values=nak_values,
                                       state='readonly', width=20)
        self.nak_combo.grid(row=1, column=1, sticky='ew', padx=5)
        if nak_values: self.nak_combo.current(0)

        ttk.Label(input_frame, text="Moon Longitude:").grid(row=1, column=2, sticky='w', pady=5, padx=5)
        # Degrees
        ttk.Label(input_frame, text="°").grid(row=1, column=4, sticky='w') # Use symbol
        self.moon_deg_var = tk.StringVar(value="10")
        ttk.Entry(input_frame, textvariable=self.moon_deg_var, width=4).grid(row=1, column=3, sticky='e') # Align right
        # Minutes
        ttk.Label(input_frame, text="'").grid(row=1, column=6, sticky='w') # Use symbol
        self.moon_min_var = tk.StringVar(value="0")
        ttk.Entry(input_frame, textvariable=self.moon_min_var, width=4).grid(row=1, column=5, sticky='e') # Align right
        # Seconds
        ttk.Label(input_frame, text='"').grid(row=1, column=8, sticky='w', padx=(0,5)) # Use symbol
        self.moon_sec_var = tk.StringVar(value="0")
        ttk.Entry(input_frame, textvariable=self.moon_sec_var, width=4).grid(row=1, column=7, sticky='e') # Align right


        # Button Frame
        button_frame = ttk.Frame(input_frame)
        button_frame.grid(row=2, column=0, columnspan=9, pady=10, sticky='w')

        ttk.Button(button_frame, text="Auto-Fill from Kundli",
                   command=self.autofill_from_kundli).pack(side='left', padx=5, ipady=5)

        ttk.Button(button_frame, text="Calculate Accurate Dasha",
                   command=self.calculate_dasha, style='Accent.TButton').pack(side='left', padx=5, ipady=5)

        # --- Output Panel (Treeview) ---
        output_frame = ttk.Frame(paned)
        paned.add(output_frame, weight=1)

        output_label = ttk.Label(output_frame, text="Dasha Periods (Mahadasha / Antardasha)", style="Header.TLabel")
        output_label.pack(pady=(10, 5))

        tree_frame = ttk.Frame(output_frame)
        tree_frame.pack(expand=True, fill='both', padx=10, pady=(0, 10))

        cols = ("Period", "Lord", "Start Date", "End Date", "Duration")
        self.dasha_tree = ttk.Treeview(tree_frame, columns=cols, show='headings', style="Dasha.Treeview")

        # --- Configure Column Headings and Widths ---
        self.dasha_tree.heading("Period", text="Level")
        self.dasha_tree.column("Period", width=60, anchor='w', stretch=False)
        self.dasha_tree.heading("Lord", text="Lord")
        self.dasha_tree.column("Lord", width=100, anchor='w')
        self.dasha_tree.heading("Start Date", text="Starts")
        self.dasha_tree.column("Start Date", width=110, anchor='center')
        self.dasha_tree.heading("End Date", text="Ends")
        self.dasha_tree.column("End Date", width=110, anchor='center')
        self.dasha_tree.heading("Duration", text="Duration")
        self.dasha_tree.column("Duration", width=150, anchor='center') # Wider for YMD

        # Add Scrollbar
        tree_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.dasha_tree.yview)
        self.dasha_tree.configure(yscrollcommand=tree_scroll.set)
        tree_scroll.pack(side='right', fill='y')
        self.dasha_tree.pack(side='left', expand=True, fill='both')

        # Add binding for showing notes on selection
        self.dasha_tree.bind('<<TreeviewSelect>>', self.show_dasha_notes)

        # --- Notes Area ---
        notes_frame = ttk.LabelFrame(output_frame, text="Interpretation Notes (Selected Period)", padding=10)
        notes_frame.pack(fill='x', padx=10, pady=(5, 10))

        self.notes_text = scrolledtext.ScrolledText(notes_frame, font=('Segoe UI', 10), wrap='word', height=8, # Slightly taller
                                                    background=self.theme_bg, foreground=self.theme_fg,
                                                    relief='flat', borderwidth=0, highlightthickness=0,
                                                    insertbackground=self.theme_fg) # Cursor color
        self.notes_text.pack(fill='x', expand=True)
        self.notes_text.insert('1.0', "Select a Dasha/Antardasha period in the table above to see notes.\n"
                                     "Remember: Actual results depend heavily on the lord's strength, placement, aspects, and transits in the *birth chart*.")
        self.notes_text.config(state='disabled')


    def autofill_from_kundli(self) -> None:
        """Reads from the central app.chart_data to fill inputs."""
        if not self.app.chart_data or 'positions' not in self.app.chart_data or 'inputs' not in self.app.chart_data:
            messagebox.showwarning("No Data", "Please generate a chart in the 'Kundli & Vargas' tab first.")
            return

        try:
            inputs = self.app.chart_data['inputs']
            moon_data = self.app.chart_data['positions'].get("Moon")

            if not moon_data:
                messagebox.showerror("Error", "Moon position data not found in the current chart.")
                return

            moon_nak_name_raw = moon_data.get('nakshatra')
            # --- Ensure nakshatra name format matches dropdown (e.g., "Ashwini" not "1. Ashwini") ---
            # You might need to adjust this based on how your Kundli stores the name
            moon_nak_name = moon_nak_name_raw.split('. ')[-1] if '. ' in moon_nak_name_raw else moon_nak_name_raw

            moon_longitude_decimal = moon_data.get('longitude') # EXPECTING 0-360 value

            if not moon_nak_name or moon_longitude_decimal is None:
                messagebox.showerror("Error", "Moon Nakshatra or precise Longitude (longitude_decimal) not found in the current chart data.")
                return

            # Set Date & Time (using stored strings/numbers)
            day = inputs.get('day', 1)
            month_num = inputs.get('month', 1) # Expecting month number
            year = inputs.get('year', 2000)
            hour = inputs.get('hour', 12)
            minute = inputs.get('minute', 0)
            second = inputs.get('second', 0)

            # Format date using datetime for consistency with Dasha calc
            try:
                temp_dt = datetime(year, month_num, day, hour, minute, second)
                self.birth_date_var.set(temp_dt.strftime("%d-%b-%Y"))
                self.birth_time_var.set(temp_dt.strftime("%H:%M:%S"))
            except ValueError:
                 messagebox.showwarning("Date Warning", "Could not format date from Kundli inputs, using defaults.")
                 self.birth_date_var.set(f"{day:02d}-{month_num:02d}-{year}") # Fallback
                 self.birth_time_var.set(f"{hour:02d}:{minute:02d}:{second:02d}")


            # Find and set Nakshatra in Combobox
            moon_nak_info = next((n for n in self.nakshatra_data if n['name'] == moon_nak_name), None)
            if moon_nak_info:
                 listbox_value = f"{moon_nak_info['num']}. {moon_nak_info['name']}"
                 # Find the index in the combobox values
                 if listbox_value in self.nak_combo['values']:
                     cb_index = self.nak_combo['values'].index(listbox_value)
                     self.nak_combo.current(cb_index)
                 else: # If not found (e.g., mismatch in name format), set text
                      self.moon_nak_var.set(listbox_value)
            else:
                 messagebox.showwarning("Warning", f"Could not find Nakshatra details for {moon_nak_name} in the dropdown.")
                 self.moon_nak_var.set(moon_nak_name) # Set raw name if not found


            # Set Longitude (convert decimal 0-360 to Deg/Min/Sec)
            if 0 <= moon_longitude_decimal <= 360:
                total_seconds = moon_longitude_decimal * 3600
                degrees = int(total_seconds // 3600)
                minutes = int((total_seconds % 3600) // 60)
                seconds = int(total_seconds % 60)

                self.moon_deg_var.set(str(degrees))
                self.moon_min_var.set(str(minutes))
                self.moon_sec_var.set(str(seconds))
                self.app.status_var.set("Dasha details auto-filled.")
            else:
                 messagebox.showerror("Longitude Error", f"Invalid Moon Longitude ({moon_longitude_decimal}) found in chart data. Must be 0-360.")
                 return


        except KeyError as e:
            messagebox.showerror("Auto-Fill Error", f"Missing expected data key in the loaded chart: {e}")
        except Exception as e:
            messagebox.showerror("Auto-Fill Error", f"Could not auto-fill data: {e}\nCheck console for details.")
            import traceback
            traceback.print_exc()

    def calculate_dasha(self) -> None:
        """Calculates and displays the Precise Dasha sequence including Bhuktis."""
        try:
            # --- 1. Get and Validate Inputs ---
            birth_date_str = self.birth_date_var.get()
            birth_time_str = self.birth_time_var.get()
            nak_combo_text = self.moon_nak_var.get()

            if not nak_combo_text:
                 messagebox.showerror("Input Error", "Please select the Moon Nakshatra.")
                 return

            # Parse Nakshatra selection (using num from dropdown)
            try:
                nak_num = int(nak_combo_text.split('.')[0])
                nak_data = next((n for n in self.nakshatra_data if n['num'] == nak_num), None)
                if not nak_data: raise ValueError("Nakshatra data not found for selected number")
            except (ValueError, IndexError):
                messagebox.showerror("Input Error", f"Invalid Nakshatra selection format: {nak_combo_text}")
                return

            # Parse Birth Datetime
            try:
                birth_dt = datetime.strptime(f"{birth_date_str} {birth_time_str}", "%d-%b-%Y %H:%M:%S")
            except ValueError:
                 try:
                     birth_dt = datetime.strptime(f"{birth_date_str} {birth_time_str}", "%d/%m/%Y %H:%M:%S")
                 except ValueError:
                     messagebox.showerror("Input Error", "Invalid Date or Time format.\nPlease use DD-Mon-YYYY (e.g., 23-Oct-2025) and HH:MM:SS (24hr).")
                     return

            # Parse Moon Longitude (handle potential errors)
            try:
                deg = int(self.moon_deg_var.get())
                minute = int(self.moon_min_var.get())
                sec = int(self.moon_sec_var.get())
                if not (0 <= deg < 360 and 0 <= minute < 60 and 0 <= sec < 60):
                     raise ValueError("Longitude values out of range (Deg 0-359, Min/Sec 0-59).")
                # Calculate absolute decimal longitude
                moon_longitude_decimal = deg + minute / 60.0 + sec / 3600.0
            except ValueError as e:
                messagebox.showerror("Input Error", f"Invalid Moon Longitude values. Please enter valid numbers.\nError: {e}")
                return

            # --- 2. Precise Calculation ---
            nak_span = nak_data.get('span', 13.333333) # Get span from data or default
            nak_start = nak_data['longitude_start']
            nak_end = nak_data['longitude_end']

            # Verify Moon longitude is within the selected Nakshatra span (with tolerance)
            tolerance = 0.0001 # Small tolerance
            correct_nak_data = None
            if not (nak_start - tolerance <= moon_longitude_decimal < nak_end + tolerance):
                 for n in self.nakshatra_data:
                     # Handle wrap-around for Revati (ends at 360 or 0)
                     is_revati = n['num'] == 27
                     lon_end = 360.0 if is_revati else n['longitude_end']
                     if n['longitude_start'] - tolerance <= moon_longitude_decimal < lon_end + tolerance:
                         correct_nak_data = n
                         break
                 
                 if correct_nak_data and correct_nak_data['num'] != nak_data['num']:
                     messagebox.showwarning("Longitude Mismatch",
                          f"Entered Moon Longitude ({moon_longitude_decimal:.4f}°) falls in {correct_nak_data['name']}, not the selected {nak_data['name']}.\n"
                          f"Recalculating based on the correct Nakshatra: {correct_nak_data['name']}.")
                     nak_data = correct_nak_data # Use the correct Nakshatra data
                     # Update combobox selection visually
                     listbox_value = f"{nak_data['num']}. {nak_data['name']}"
                     if listbox_value in self.nak_combo['values']:
                          cb_index = self.nak_combo['values'].index(listbox_value)
                          self.nak_combo.current(cb_index)
                     else:
                          self.moon_nak_var.set(listbox_value) # Fallback

                 elif not correct_nak_data:
                     messagebox.showerror("Error", f"Could not determine Nakshatra for the entered longitude {moon_longitude_decimal:.4f}°.")
                     return
            
            # Recalculate based on potentially corrected nak_data
            nak_lord = nak_data['lord']
            nak_start = nak_data['longitude_start']
            nak_end = 360.0 if nak_data['num'] == 27 else nak_data['longitude_end'] # Handle Revati end
            nak_span = nak_end - nak_start 

            # Calculate remaining portion accurately
            traversed_longitude = moon_longitude_decimal - nak_start
            remaining_longitude = nak_end - moon_longitude_decimal
            
            # Handle edge cases precisely
            if abs(traversed_longitude) < tolerance: traversed_longitude = 0.0
            if abs(remaining_longitude) < tolerance: remaining_longitude = 0.0
            if nak_span < tolerance: # Avoid division by zero
                messagebox.showerror("Error", "Nakshatra span is too small.")
                return

            proportion_remaining = remaining_longitude / nak_span
            if not (0.0 <= proportion_remaining <= 1.0): # Sanity check
                 # If proportion is slightly off due to float precision near boundaries, clamp it
                 proportion_remaining = max(0.0, min(1.0, proportion_remaining))
                 print(f"Clamped proportion remaining: {proportion_remaining}") # Debug print


            total_years_first_dasha = self.dasha_periods[nak_lord]
            balance_years_decimal = total_years_first_dasha * proportion_remaining

            # Convert balance decimal years to Y/M/D using precise days
            total_days_balance = balance_years_decimal * 365.2425
            try:
                 # Calculate end date using timedelta first for days
                 balance_timedelta = timedelta(days=total_days_balance)
                 first_md_end_date = birth_dt + balance_timedelta
                 # Now calculate Y/M/D from the timedelta for display
                 temp_rel = relativedelta(days=total_days_balance)
                 balance_years = temp_rel.years
                 balance_months = temp_rel.months
                 balance_days = temp_rel.days + (temp_rel.microseconds / (1000000 * 86400)) # Include fraction of day
                 balance_days = int(math.ceil(balance_days)) # Round day up

            except (OverflowError, ValueError) as dt_err:
                 messagebox.showerror("Calculation Error", f"Could not calculate the end date of the first Dasha balance: {dt_err}")
                 return

            # --- 3. Populate Treeview ---
            for item in self.dasha_tree.get_children():
                self.dasha_tree.delete(item)

            # --- Display the first partial Mahadasha ---
            duration_str_first = f"{balance_years}Y {balance_months}M {balance_days}D (Balance)"
            md_id_first = self.dasha_tree.insert("", "end", text=nak_lord, # Use text for lord maybe?
                                                values=("MD", nak_lord,
                                                 birth_dt.strftime('%d-%b-%Y %H:%M'), # Add time
                                                 first_md_end_date.strftime('%d-%b-%Y %H:%M'),
                                                 duration_str_first),
                                                tags=('MahadashaRow', nak_lord))

            # --- Calculate Antardashas for the First (Balance) Mahadasha ---
            proportion_traversed = 1.0 - proportion_remaining
            md_years_first = self.dasha_periods[nak_lord]
            dasha_years_elapsed_in_first_md = proportion_traversed * md_years_first
            md_lord_index_first = self.planet_order.index(nak_lord)

            elapsed_ad_years_cumulative = 0.0
            current_ad_start_date_first = birth_dt # Start from birth time

            for j in range(len(self.planet_order)):
                ad_lord_index = (md_lord_index_first + j) % len(self.planet_order)
                ad_lord = self.planet_order[ad_lord_index]
                ad_years = self.dasha_periods[ad_lord]
                ad_duration_years_decimal = (md_years_first * ad_years) / self.total_dasha_cycle

                # Check if this AD was already completed before birth
                if elapsed_ad_years_cumulative + ad_duration_years_decimal <= dasha_years_elapsed_in_first_md + tolerance:
                    elapsed_ad_years_cumulative += ad_duration_years_decimal
                    continue # Skip this completed AD

                # This is the AD running at birth or a subsequent one within the balance
                if elapsed_ad_years_cumulative <= dasha_years_elapsed_in_first_md:
                    # This is the AD running at birth - calculate its balance
                    balance_ad_years = (elapsed_ad_years_cumulative + ad_duration_years_decimal) - dasha_years_elapsed_in_first_md
                    ad_total_days_balance = balance_ad_years * 365.2425
                    ad_bal_timedelta = timedelta(days=ad_total_days_balance)
                    ad_end_date = birth_dt + ad_bal_timedelta

                    # Get Y/M/D for display
                    temp_rel_ad_bal = relativedelta(days=ad_total_days_balance)
                    ad_bal_y = temp_rel_ad_bal.years
                    ad_bal_m = temp_rel_ad_bal.months
                    ad_bal_d_f = temp_rel_ad_bal.days + (temp_rel_ad_bal.microseconds / (1000000 * 86400))
                    ad_bal_d = int(math.ceil(ad_bal_d_f))
                    duration_str_ad = f"{ad_bal_y}Y {ad_bal_m}M {ad_bal_d}D (Balance)"

                else:
                    # This is a full AD subsequent to the one at birth, within the first MD's balance
                    ad_total_days = ad_duration_years_decimal * 365.2425
                    ad_timedelta = timedelta(days=ad_total_days)
                    ad_end_date = current_ad_start_date_first + ad_timedelta

                    # Get Y/M/D for display
                    temp_rel_ad = relativedelta(days=ad_total_days)
                    ad_y = temp_rel_ad.years
                    ad_m = temp_rel_ad.months
                    ad_d_f = temp_rel_ad.days + (temp_rel_ad.microseconds / (1000000 * 86400))
                    ad_d = int(math.ceil(ad_d_f))
                    duration_str_ad = f"{ad_y}Y {ad_m}M {ad_d}D"


                # Ensure AD doesn't go beyond the first MD's end date
                if ad_end_date > first_md_end_date:
                    time_diff = first_md_end_date - current_ad_start_date_first
                    temp_rel_partial = relativedelta(days=time_diff.total_seconds() / 86400.0)
                    part_y = temp_rel_partial.years
                    part_m = temp_rel_partial.months
                    part_d_f = temp_rel_partial.days + (temp_rel_partial.microseconds / (1000000 * 86400))
                    part_d = int(math.ceil(part_d_f))
                    duration_str_ad = f"{part_y}Y {part_m}M {part_d}D (Partial)"
                    ad_end_date = first_md_end_date # Cap it

                self.dasha_tree.insert(md_id_first, "end", values=("  AD", ad_lord,
                                                 current_ad_start_date_first.strftime('%d-%b-%Y %H:%M'),
                                                 ad_end_date.strftime('%d-%b-%Y %H:%M'),
                                                 duration_str_ad), tags=(ad_lord,))

                current_ad_start_date_first = ad_end_date
                elapsed_ad_years_cumulative += ad_duration_years_decimal # Increment cumulative time

                if current_ad_start_date_first >= first_md_end_date - timedelta(seconds=1): # Allow tiny difference
                    break # Stop if we've filled the first MD balance


            # --- Loop through Subsequent Full Mahadashas ---
            current_md_start_date = first_md_end_date

            # Iterate through the *next* 8 full Mahadashas (total 9 periods in a cycle)
            for i in range(1, len(self.planet_order)):
                md_lord_index = (md_lord_index_first + i) % len(self.planet_order)
                md_lord = self.planet_order[md_lord_index]
                md_years = self.dasha_periods[md_lord]
                md_end_date = current_md_start_date + relativedelta(years=md_years)
                duration_str_md = f"{md_years} Years"

                # Insert Mahadasha row
                md_id = self.dasha_tree.insert("", "end", values=("MD", md_lord,
                                                 current_md_start_date.strftime('%d-%b-%Y %H:%M'),
                                                 md_end_date.strftime('%d-%b-%Y %H:%M'),
                                                 duration_str_md), tags=('MahadashaRow', md_lord))

                current_ad_start_date = current_md_start_date # Reset AD start for this MD

                # --- Loop through Antardashas for this Full Mahadasha ---
                for j in range(len(self.planet_order)):
                    ad_lord_index = (md_lord_index + j) % len(self.planet_order)
                    ad_lord = self.planet_order[ad_lord_index]
                    ad_years = self.dasha_periods[ad_lord]

                    # Calculate AD duration using precise days
                    ad_duration_years_decimal = (md_years * ad_years) / self.total_dasha_cycle
                    ad_total_days = ad_duration_years_decimal * 365.2425
                    ad_timedelta = timedelta(days=ad_total_days)
                    ad_end_date = current_ad_start_date + ad_timedelta

                    # Get Y/M/D for display
                    temp_rel_ad = relativedelta(days=ad_total_days)
                    ad_y = temp_rel_ad.years
                    ad_m = temp_rel_ad.months
                    ad_d_f = temp_rel_ad.days + (temp_rel_ad.microseconds / (1000000 * 86400))
                    ad_d = int(math.ceil(ad_d_f))
                    duration_str_ad = f"{ad_y}Y {ad_m}M {ad_d}D"

                    # Insert Antardasha row as a child of the Mahadasha
                    self.dasha_tree.insert(md_id, "end", values=("  AD", ad_lord,
                                                 current_ad_start_date.strftime('%d-%b-%Y %H:%M'),
                                                 ad_end_date.strftime('%d-%b-%Y %H:%M'),
                                                 duration_str_ad), tags=(ad_lord,))

                    current_ad_start_date = ad_end_date

                current_md_start_date = md_end_date # Next MD starts


            # Apply Mahadasha row styling tag
            # Note: This might make the entire row background colored.
            # Treeview styling can be limited. Consider alternating row colors instead if needed.
            # self.dasha_tree.tag_configure('MahadashaRow', background=self.alt_row_color)


            self.app.status_var.set("Accurate Dasha timeline calculated.")

        except ImportError:
            messagebox.showerror("Dependency Error", "The 'python-dateutil' library is required.\nPlease install it: pip install python-dateutil")
        except Exception as e:
            messagebox.showerror("Error", f"Could not calculate Dasha.\nError: {type(e).__name__} - {e}\nCheck console for details.")
            import traceback
            traceback.print_exc()


    def show_dasha_notes(self, event: Optional[tk.Event]) -> None:
        """Shows interpretation notes for the selected Dasha/Antardasha lord."""
        selected_items = self.dasha_tree.selection()
        if not selected_items:
            # Clear notes if nothing selected
            self.notes_text.config(state='normal')
            self.notes_text.delete('1.0', tk.END)
            self.notes_text.insert('1.0', "Select a Dasha/Antardasha period...")
            self.notes_text.config(state='disabled')
            return

        item_id = selected_items[0]
        item_values = self.dasha_tree.item(item_id, "values")
        item_tags = self.dasha_tree.item(item_id, "tags")

        if not item_values or not item_tags:
            return

        period_type_raw = item_values[0].strip() # MD or AD
        lord = item_values[1]
        start_date_str = item_values[2]
        end_date_str = item_values[3]
        
        # Determine if it's MD or AD based on the first column value
        period_type = "Mahadasha (MD)" if period_type_raw == "MD" else "Antardasha (AD)"
        
        # Find the parent item (Mahadasha lord) if an Antardasha is selected
        md_lord = lord # Assume it's an MD initially
        if period_type == "Antardasha (AD)":
             parent_id = self.dasha_tree.parent(item_id)
             if parent_id:
                 md_values = self.dasha_tree.item(parent_id, "values")
                 if md_values:
                     md_lord = md_values[1] # Get the Mahadasha lord from the parent
        
        # Planet name should be the first tag (used for coloring/notes)
        planet_lord = item_tags[-1] if item_tags else lord # Get last tag, should be planet name


        bphs_note, lk_note = get_planet_notes(planet_lord, self.app)

        note = f"Selected Period: {planet_lord} {period_type}\n"
        if period_type == "Antardasha (AD)":
             note += f"(Running under {md_lord} Mahadasha)\n"
        note += f"Period: {start_date_str} to {end_date_str}\n"
        note += "─────────────────────────────────────────────────\n"
        note += "General Vimshottari Interpretation:\n"
        if period_type == "Mahadasha (MD)":
            note += f"  • The overall theme for these ~{self.dasha_periods.get(planet_lord, '?')} years revolves around {planet_lord}'s significations and condition in the birth chart.\n"
        else: # Antardasha
            note += f"  • Within the broader {md_lord} MD, this sub-period brings {planet_lord}'s themes to the forefront.\n"
            note += f"  • Results are a blend: {planet_lord}'s nature interacts with {md_lord}'s overall influence. Check their relationship (friendly/enemy) in the chart.\n"

        note += "─────────────────────────────────────────────────\n"
        note += f"BPHS Notes on Lord ({planet_lord}):\n"
        note += f"{textwrap.fill(bphs_note, width=60, initial_indent='  ', subsequent_indent='  ')}\n\n"
        note += f"Lal Kitab Notes on Lord ({planet_lord}):\n"
        note += f"{textwrap.fill(lk_note, width=60, initial_indent='  ', subsequent_indent='  ')}\n\n"
        note += ("IMPORTANT:\n"
                 "Actual results are highly specific to the individual's birth chart.\n"
                 f"Analyze the {period_type} lord ({planet_lord})'s:\n"
                 "  - Dignity (Exaltation, Own Sign, Debilitation etc.)\n"
                 "  - House Placement (Kendra, Trikona, Dusthana etc.)\n"
                 "  - Aspects Received & Given\n"
                 "  - Conjunctions\n"
                 "  - Role in Yogas/Doshas\n"
                 f"{'  - Relationship with the Mahadasha lord (' + md_lord + ')' if period_type == 'Antardasha (AD)' else ''}\n"
                 "  - Current Transits (Gochar)")


        self.notes_text.config(state='normal')
        self.notes_text.delete('1.0', tk.END)
        self.notes_text.insert('1.0', note)
        self.notes_text.config(state='disabled')

class EnhancedNakshatraTab(ttk.Frame):
    """
    This class defines the "Nakshatra Explorer" tab with enhanced UI and data.
    """
    def __init__(self, parent: ttk.Notebook, app: 'AstroVighatiElite') -> None:
        super().__init__(parent)
        self.app = app
        self.all_nakshatras = self.app.astro_data.get_all_nakshatras() # Cache data

        # Define theme colors
        self.theme_bg = "#2e2e2e"
        self.theme_fg = "#ffffff"
        self.select_bg = "#005f9e"
        self.header_fg = "#ffcc66" # Example: Gold for headers

        self.create_styles()
        self.create_ui()

    def create_styles(self):
        """Configure custom ttk styles."""
        style = ttk.Style()
        style.configure("NakshatraHeader.TLabel", foreground=self.header_fg,
                        font=('Segoe UI', 13, 'bold'))
        style.configure("NakshatraSubHeader.TLabel", foreground=self.header_fg,
                        font=('Segoe UI', 12, 'bold'))
        # Style for the Entry widget if needed
        style.map("TEntry",
                  fieldbackground=[('!focus', self.theme_bg)],
                  foreground=[('!focus', self.theme_fg)],
                  insertcolor=[('', self.theme_fg)]) # Cursor color

    def create_ui(self) -> None:
        paned = ttk.PanedWindow(self, orient='horizontal')
        paned.pack(expand=True, fill='both', padx=15, pady=15)

        # Left Panel (List & Search)
        left_panel = ttk.Frame(paned, padding=(15, 10))
        paned.add(left_panel, weight=1)

        ttk.Label(left_panel, text="⭐ NAKSHATRA LIST", style='NakshatraHeader.TLabel').pack(pady=(0, 15))

        # Search Box
        self.search_var = tk.StringVar()
        self.search_var.trace_add('write', self.filter_nakshatras)
        search_entry = ttk.Entry(left_panel, textvariable=self.search_var, width=30, 
                                font=('Segoe UI', 10))
        search_entry.pack(fill='x', pady=(0, 10))
        # Placeholder text (requires a bit more logic if needed)
        # search_entry.insert(0, "Search by Name, Lord...") 

        # Listbox Frame
        list_frame = ttk.Frame(left_panel)
        list_frame.pack(fill='both', expand=True)

        nak_scrollbar = ttk.Scrollbar(list_frame, orient='vertical')
        self.nak_listbox = tk.Listbox(
            list_frame,
            font=('Segoe UI', 11),
            exportselection=False,
            yscrollcommand=nak_scrollbar.set,
            background=self.theme_bg,
            foreground=self.theme_fg,
            selectbackground=self.select_bg,
            selectforeground=self.theme_fg,
            highlightthickness=0,
            borderwidth=0,
            activestyle='none',
            relief='flat'
        )
        nak_scrollbar.config(command=self.nak_listbox.yview)
        nak_scrollbar.pack(side='right', fill='y')
        self.nak_listbox.pack(side='left', fill='both', expand=True)
        self.nak_listbox.bind('<<ListboxSelect>>', self.on_select)

        self.populate_list() # Fill the list on startup

        # Right Panel (Notebook for Details & Syllables)
        right_panel = ttk.Frame(paned, padding=(15, 10, 0, 10))
        paned.add(right_panel, weight=3) # Increased weight

        self.details_notebook = ttk.Notebook(right_panel)
        self.details_notebook.pack(fill='both', expand=True)

        # --- Configure Notebook Style (optional, depends on theme) ---
        style = ttk.Style()
        style.configure('TNotebook.Tab', padding=[10, 5], font=('Segoe UI', 10, 'bold'))

        # Common ScrolledText options
        text_options = {
            "font": ("Courier New", 10), # Monospace for details
            "wrap": 'word',
            "padx": 15,
            "pady": 15,
            "background": self.theme_bg,
            "foreground": self.theme_fg,
            "highlightthickness": 0,
            "borderwidth": 0,
            "relief": 'flat',
            "insertbackground": self.theme_fg
        }

        # Tab 1: Details
        details_frame = ttk.Frame(self.details_notebook) # Removed padding, use ScrolledText's padding
        self.details_notebook.add(details_frame, text="🌟 Details")
        self.details_text = scrolledtext.ScrolledText(details_frame, **text_options)
        self.details_text.pack(fill='both', expand=True)

        # Tab 2: Name Syllables
        syllables_frame = ttk.Frame(self.details_notebook) # Removed padding
        self.details_notebook.add(syllables_frame, text="🗣️ Syllables")
        # Use a slightly different font if preferred for this reference
        syllable_text_options = text_options.copy()
        syllable_text_options["font"] = ("Segoe UI", 11) # Proportional font might be okay here
        self.syllables_text = scrolledtext.ScrolledText(syllables_frame, **syllable_text_options)
        self.syllables_text.pack(fill='both', expand=True)

        # Populate the syllables tab
        self.populate_syllables_tab()
        self.syllables_text.config(state='disabled') # Read-only


        # Select the first item by default
        if self.nak_listbox.size() > 0:
            self.nak_listbox.selection_set(0)
            self.on_select(None) # Trigger display


    def populate_list(self, filter_term: Optional[str] = None) -> None:
        """Fills/Refills the listbox, optionally filtering."""
        self.nak_listbox.delete(0, tk.END)
        search_term = filter_term.lower() if filter_term else None

        for nak in self.all_nakshatras:
            display_name = f" {nak.get('num', '?')}. {nak['name']} ({nak['devanagari']})"
            
            # Check if filtering is needed
            if search_term:
                 # More comprehensive search
                 match = (search_term in nak['name'].lower() or
                          search_term in nak['sanskrit'].lower() or
                          search_term in nak['lord'].lower() or
                          search_term in nak['deity'].lower() or
                          search_term in str(nak.get('num', '')))
                 if match:
                      self.nak_listbox.insert(tk.END, display_name)
            else:
                 # No filter, add all
                 self.nak_listbox.insert(tk.END, display_name)

    def filter_nakshatras(self, *args: Any) -> None:
        """Calls populate_list with the current search term."""
        self.populate_list(self.search_var.get())

    def populate_syllables_tab(self) -> None:
        """Fills the 'Name Syllables' tab with a formatted summary."""
        self.syllables_text.config(state='normal')
        self.syllables_text.delete('1.0', tk.END)
        
        title = "NAKSHATRA NAME SYLLABLES (AVAKAHADA CHAKRA)"
        header_bar = "═" * 66
        
        # Define tags for bold and header
        self.syllables_text.tag_configure("header", font=('Segoe UI', 12, 'bold'), justify='center')
        self.syllables_text.tag_configure("subheader", font=('Segoe UI', 10), foreground="#cccccc") # Lighter gray
        self.syllables_text.tag_configure("nak_name", font=('Segoe UI', 11, 'bold'))
        self.syllables_text.tag_configure("syllable_data", font=('Segoe UI', 11))

        # Insert Header
        self.syllables_text.insert(tk.END, f"{title}\n", "header")
        self.syllables_text.insert(tk.END, f"{header_bar}\n\n", "header")
        
        # Insert Subheader description
        desc = ("Traditional starting syllables for names based on the Moon's "
                "Nakshatra Pada (quarter) at birth.\n\n")
        self.syllables_text.insert(tk.END, desc, "subheader")
        
        # Insert Nakshatra Data
        for nak in self.all_nakshatras:
            syllables = nak.get('syllables', ['N/A']*4)
            syllable_str = f"Pada 1: {syllables[0]}, Pada 2: {syllables[1]}, Pada 3: {syllables[2]}, Pada 4: {syllables[3]}"
            
            nak_display = f"{nak.get('num', '?')}. {nak['name']} ({nak['devanagari']})"
            self.syllables_text.insert(tk.END, f"{nak_display}\n", "nak_name")
            self.syllables_text.insert(tk.END, f"    {syllable_str}\n\n", "syllable_data")
            
        self.syllables_text.config(state='disabled')
        
    def on_select(self, event: Optional[tk.Event]) -> None:
        """Called when a user clicks on an item in the listbox."""
        selection = self.nak_listbox.curselection()
        if not selection: return 

        # Get listbox text and extract the number part to find the nakshatra
        nak_name_full = self.nak_listbox.get(selection[0]).strip()
        try:
            # Extract number like "1." from " 1. Ashwini (अश्विनी)"
            nak_num_str = nak_name_full.split('.')[0]
            nak_num = int(nak_num_str)
        except (ValueError, IndexError):
            print(f"Error parsing Nakshatra number from: {nak_name_full}")
            return # Handle potential parsing error

        # Find the matching data dictionary using the number
        nak_data = next((n for n in self.all_nakshatras if n.get('num') == nak_num), None)

        if nak_data:
            self.show_details(nak_data)
            # Switch focus to the details tab when selection changes
            self.details_notebook.select(0)

    def show_details(self, nak: Dict[str, Any]) -> None:
        """Displays the formatted details for a selected Nakshatra."""
        self.details_text.config(state='normal')
        self.details_text.delete('1.0', tk.END)
        
        title = f"{nak.get('num', '?')}. {nak['name'].upper()} ({nak['devanagari']})"
        separator = "─" * 66 

        # Helper for wrapping text - ensure import textwrap at top
        def wrap_text(text: str, width: int = 66, indent='  ') -> str:
            if not text or not text.strip(): return indent + "N/A"
            lines = text.split('\n')
            wrapped_lines = [textwrap.fill(
                line, width=width, initial_indent=indent, subsequent_indent=indent,
                break_long_words=False, replace_whitespace=False
            ) for line in lines]
            return '\n'.join(wrapped_lines)

        syllables = nak.get('syllables', ['N/A']*4)
        padas_nav = nak.get('padas_navamsha', ['?']*4)

        details = f"""
 {title.center(66)}
{separator}

 CORE ATTRIBUTES
{separator}
   {'Ruling Lord':<18}: {nak.get('lord','N/A')}
   {'Presiding Deity':<18}: {nak.get('deity', 'N/A')}
   {'Symbol':<18}: {nak.get('symbol', 'N/A')}

 CLASSIFICATION (BPHS / Classical)
{separator}
   {'Gana (Temperament)':<18}: {nak.get('gana', 'N/A')}
   {'Yoni (Animal)':<18}: {nak.get('yoni', 'N/A')}
   {'Nadi (Constitution)':<18}: {nak.get('nadi', 'N/A')}
   {'Guna (Quality)':<18}: {nak.get('guna', 'N/A')}
   {'Tattva (Element)':<18}: {nak.get('tattva', 'N/A')}
   {'Motivation':<18}: {nak.get('motivation', 'N/A')}
   {'Nature':<18}: {nak.get('nature', 'N/A')}

 PADA (QUARTERS) & NAME SYLLABLES
{separator}
   {'Pada 1 Navamsha':<18}: {padas_nav[0]:<15} Syllable: {syllables[0]}
   {'Pada 2 Navamsha':<18}: {padas_nav[1]:<15} Syllable: {syllables[1]}
   {'Pada 3 Navamsha':<18}: {padas_nav[2]:<15} Syllable: {syllables[2]}
   {'Pada 4 Navamsha':<18}: {padas_nav[3]:<15} Syllable: {syllables[3]}

 KEYWORDS & SIGNIFICATIONS
{separator}
{wrap_text(nak.get('keywords', 'N/A'))}

 BPHS / CLASSICAL NOTE
{separator}
{wrap_text(nak.get('bphs_note', 'N/A'))}

 LAL KITAB NOTE
{separator}
{wrap_text(nak.get('lal_kitab_note', 'N/A'))}
"""
        self.details_text.insert('1.0', details.strip())
        self.details_text.config(state='disabled')

class EnhancedPlanetTab(ttk.Frame):
    """
    This class defines the "Planetary Guide" tab with enhanced aesthetics.
    Uses a tk.Listbox for a stable, clean, and efficient UI.
    """
    def __init__(self, parent: ttk.Notebook, app: 'AstroVighatiElite') -> None:
        super().__init__(parent)
        self.app = app
        self.all_planets = self.app.astro_data.get_all_planets()
        
        # --- Define theme colors for easier management ---
        self.theme_bg = "#2e2e2e" 
        self.theme_fg = "#ffffff"
        self.select_bg = "#005f9e" # A slightly different blue for selection
        self.header_fg = "#ffcc66" # Example color for headers

        self.create_styles() # Create custom styles
        self.create_ui()

    def create_styles(self):
        """Configure custom ttk styles if needed (e.g., for headers)."""
        style = ttk.Style()
        # You might already have a Heading.TLabel, adjust if needed
        style.configure("TabHeader.TLabel", foreground=self.header_fg, 
                        font=('Segoe UI', 13, 'bold')) 
        style.configure("DetailHeader.TLabel", foreground=self.header_fg,
                        font=('Segoe UI', 12, 'bold'))

    def create_ui(self) -> None:
        # --- Increased padding for the main paned window ---
        paned = ttk.PanedWindow(self, orient='horizontal')
        paned.pack(expand=True, fill='both', padx=15, pady=15) # Increased padx/pady

        # Left Panel (List)
        # --- Increased padding ---
        left_panel = ttk.Frame(paned, padding=(15, 10)) 
        paned.add(left_panel, weight=1)

        ttk.Label(left_panel, text="🪐 NAVAGRAHA (नवग्रह)", style='TabHeader.TLabel').pack(pady=(0, 15)) # Increased bottom padding

        # --- Listbox Implementation ---
        
        # Create the Listbox 
        self.planet_listbox = tk.Listbox(
            left_panel, 
            font=('Segoe UI', 12), # Slightly larger font for list items
            exportselection=False,
            
            # --- Enhanced Styling ---
            background=self.theme_bg,
            foreground=self.theme_fg,
            selectbackground=self.select_bg,
            selectforeground=self.theme_fg,
            highlightthickness=0, 
            borderwidth=0,
            activestyle='none', # Remove dotted outline on selection
            relief='flat' # Ensure flat appearance
        )
        
        # Pack the listbox 
        # --- Added vertical padding ---
        self.planet_listbox.pack(fill='both', expand=True, pady=(0, 5)) 

        # Bind the selection event
        self.planet_listbox.bind('<<ListboxSelect>>', self.on_select)

        # Populate the listbox
        for planet in self.all_planets:
            self.planet_listbox.insert(tk.END, f" {planet['symbol']}  {planet['name']} ({planet['devanagari']})") # Added extra space after symbol

        # Right Panel (Details)
        # --- Increased padding ---
        right_panel = ttk.Frame(paned, padding=(15, 10)) 
        paned.add(right_panel, weight=3) 
        
        # Header Label for the right panel 
        # --- Using a specific style ---
        self.planet_header_label = ttk.Label(right_panel, text="", style="DetailHeader.TLabel")
        self.planet_header_label.pack(pady=(0, 15), fill='x', anchor='w') # Increased bottom padding

        self.planet_text = scrolledtext.ScrolledText(
            right_panel, 
            font=("Courier New", 10), 
            wrap='word',
            padx=15, # Increased padding inside text area
            pady=15,
            # --- Style to match theme ---
            background=self.theme_bg,
            foreground=self.theme_fg,
            highlightthickness=0,
            borderwidth=0,
            relief='flat',
            insertbackground=self.theme_fg # Cursor color if editable
        )
        self.planet_text.pack(fill='both', expand=True)

        # Select first item by default
        if self.planet_listbox.size() > 0:
            self.planet_listbox.selection_set(0)
            self.on_select(None) 


    def on_select(self, event: Optional[tk.Event]) -> None:
        """Called when a user clicks on an item in the listbox."""
        selection = self.planet_listbox.curselection()
        if not selection: 
            return

        selected_index = selection[0]
        planet_data = self.all_planets[selected_index]
        
        if planet_data:
            self.show_planet(planet_data)


    def show_planet(self, planet: Dict[str, Any]) -> None:
        """Displays the formatted details for a selected Planet."""
        
        # Update the header label
        # --- Added extra spacing ---
        self.planet_header_label.config(text=f" {planet['symbol']}   {planet['name']} ({planet['devanagari']})")
        
        self.planet_text.config(state='normal')
        self.planet_text.delete('1.0', tk.END)
        
        # --- Define consistent line separator ---
        separator = "─" * 66 

        # Helper for formatting lists
        def join_list(lst):
            return ", ".join(lst) if lst else "None"

        # Helper for wrapping long text blocks
        def wrap_text(text: str, width: int = 66) -> str: # Adjusted width
            lines = text.split('\n')
            wrapped_lines = [textwrap.fill(
                line, 
                width=width, 
                initial_indent='  ', # Indent wrapped text
                subsequent_indent='  ',
                break_long_words=False,
                replace_whitespace=False
            ) for line in lines]
            # Remove initial indent if the original text was empty or just whitespace
            if not text.strip():
                 return ""
            # Ensure the first line doesn't have double indent if it wasn't wrapped
            if len(wrapped_lines) > 0 and not wrapped_lines[0].startswith('  '):
                 wrapped_lines[0] = '  ' + wrapped_lines[0] # Add indent manually if needed
                 
            return '\n'.join(wrapped_lines).strip() # Strip leading/trailing whitespace from final block


        # Using f-string for cleaner formatting, removed ASCII box
        details = f"""
 BPHS KARAKA (SIGNIFICATOR)
{separator}
{wrap_text(planet.get('karaka','N/A'))}

 BPHS DIGNITIES & CORE
{separator}
"""
        dignities = planet.get('dignities', {})
        for dignity, value in dignities.items():
            details += f"   {dignity:<18}: {value}\n" 
            
        details += f"""
   {('Nature'):<18}: {planet.get('nature','N/A')}
   {('Vimshottari Dasha'):<18}: {planet.get('vimshottari_dasha','N/A')}
   {('Aspects'):<18}: {planet.get('aspects', 'N/A')}

 BPHS ATTRIBUTES
{separator}
   {('Gender'):<18}: {planet.get('gender','N/A')}
   {('Element (Tattva)'):<18}: {planet.get('element', 'N/A')}
   {('Caste'):<18}: {planet.get('caste', 'N/A')}
   {('Direction'):<18}: {planet.get('direction', 'N/A')}
   {('Gemstone'):<18}: {planet.get('gemstone', 'N/A')}
   {('Deity'):<18}: {planet.get('deity', 'N/A')}
   {('Body Part'):<18}: {planet.get('body_part', 'N/A')}

 BPHS RELATIONSHIPS (Graha Maitri)
{separator}
   {('Friends'):<18}: {join_list(planet.get('friendly',[]))}
   {('Neutral'):<18}: {join_list(planet.get('neutral', []))}
   {('Enemies'):<18}: {join_list(planet.get('enemy',[]))}

 ADVANCED NOTES
{separator}
 BPHS NOTE:
{wrap_text(planet.get('bphs_note', 'N/A'))}

 LAL KITAB NOTE:
{wrap_text(planet.get('lal_kitab_note', 'N/A'))}
"""
        self.planet_text.insert('1.0', details.strip()) # Use strip() to remove leading/trailing blank lines
        self.planet_text.config(state='disabled')
                
class EnhancedRashiTab(ttk.Frame):
    """
    This class defines the "Rashi Explorer" tab.

    Purpose:
    A simple, read-only encyclopedia for the 12 Rashis (Zodiac Signs)
    with advanced details for astrological study.
    """
    def __init__(self, parent: ttk.Notebook, app: 'AstroVighatiElite') -> None:
        super().__init__(parent)
        self.app = app # This holds the reference to your main app
        self.create_ui()

    def create_ui(self) -> None:
        paned = ttk.PanedWindow(self, orient='horizontal')
        paned.pack(expand=True, fill='both', padx=10, pady=10)

        # Left Panel (List)
        left_panel = ttk.Frame(paned, padding=10)
        paned.add(left_panel, weight=1)

        ttk.Label(left_panel, text="♈ ZODIAC SIGNS (राशि)", style='Heading.TLabel').pack(pady=(0, 10))

        # --- Listbox Frame for Scrollbar ---
        list_frame = ttk.Frame(left_panel)
        list_frame.pack(fill='both', expand=True)
        
        rashi_scrollbar = ttk.Scrollbar(list_frame, orient='vertical')
        self.rashi_listbox = tk.Listbox(list_frame, font=('Segoe UI', 12), exportselection=False,
                                        yscrollcommand=rashi_scrollbar.set)
        rashi_scrollbar.config(command=self.rashi_listbox.yview)
        
        rashi_scrollbar.pack(side='right', fill='y')
        self.rashi_listbox.pack(side='left', fill='both', expand=True)
        # --- End Listbox Frame ---

        self.rashi_listbox.bind('<<ListboxSelect>>', self.on_select)

        # Assumes self.app.astro_data.get_all_rashis() exists
        for rashi in self.app.astro_data.get_all_rashis():
            self.rashi_listbox.insert(tk.END, f" {rashi['name']} ({rashi['devanagari']})")

        # Right Panel (Details)
        right_panel = ttk.Frame(paned, padding=10)
        paned.add(right_panel, weight=3) # Give more weight to details

        self.rashi_text = scrolledtext.ScrolledText(
            right_panel, 
            font=("Courier New", 10), # IMPORTANT: Use a monospace font
            wrap='word',
            padx=10,
            pady=10
        )
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

    def show_details(self, rashi: Dict[str, Any]) -> None:
        """Displays the formatted details for a selected Rashi."""
        self.rashi_text.config(state='normal')
        self.rashi_text.delete('1.0', tk.END)
        
        title = f"{rashi['name'].upper()} ({rashi['sanskrit']} / {rashi['devanagari']})"
        bphs = rashi.get('bphs_special', {}) # Get the sub-dict

        details = f"""
╔══════════════════════════════════════════════════════════════════╗
║  {title.center(62)}  ║
╚══════════════════════════════════════════════════════════════════╝

BPHS CORE (CLASSICAL)
──────────────────────────────────────────────────────────────────
 Ruling Lord    : {rashi.get('lord','N/A')}
 Gender         : {rashi.get('gender','N/A')}
 Tattva (Element) : {rashi.get('tattva','N/A')}
 Modality (Nature): {rashi.get('modality','N/A')}
 Rising         : {rashi.get('rising','N/A')}
 Kalapurusha    : {rashi.get('kalapurusha','N/A')}
 Nature         : {rashi.get('nature','N/A')}
 Direction      : {rashi.get('direction','N/A')}

BPHS KARAKATVAS (SIGNIFICATIONS)
──────────────────────────────────────────────────────────────────
 Exaltation     : {bphs.get('exaltation', 'None')}
 Debilitation   : {bphs.get('debilitation', 'None')}
 Mooltrikona    : {bphs.get('mooltrikona', 'None')}

DESCRIPTION
──────────────────────────────────────────────────────────────────
 {rashi.get('description','N/A')}

LAL KITAB PERSPECTIVE
──────────────────────────────────────────────────────────────────
 {rashi.get('lal_kitab_note','N/A')}
"""
        self.rashi_text.insert('1.0', details)
        self.rashi_text.config(state='disabled')
        
# --- Enhanced Data Functions ---

def get_mahapurusha_data_detailed() -> List[Dict[str, Any]]:
    """Returns detailed structured data for Pancha Mahapurusha Yogas."""
    return [
        {"category": "Mahapurusha Yoga", "name": "Ruchaka Yoga", "devanagari": "रूचक योग", "planet": "Mars",
         "formation": "Mars in a Kendra (1st, 4th, 7th, 10th house from Ascendant) AND in its own sign (Aries, Scorpio) or exaltation sign (Capricorn).",
         "logic": "Mars represents energy, courage, action, and determination. When strongly placed in an angular house (Kendra), which represents the pillars of life (self, home/mother, spouse/partnerships, career/public life), Mars infuses these areas with its core qualities. The individual becomes driven, courageous, and action-oriented in a way that defines their core identity and life path. It signifies a 'Martian' personality making its mark.",
         "bphs_results": """
         BPHS describes the native as having a long face, attractive brows, dark hair, possibly cruel tendencies, fond of battle, and commanding presence.
         - **Effects**: Grants physical strength, bravery, leadership qualities, success in competitive fields (military, police, sports, surgery), acquisition of land/property, potentially a commanding or aggressive nature.
         - **Variations**: Strongest in Capricorn (exaltation), then Aries (Mooltrikona), then Scorpio. Placement in different Kendras modifies expression (1H: Personality, 4H: Domestic strength/conflict, 7H: Dominant partner/business, 10H: Powerful career).
         """,
         "lal_kitab_note": """
         Lal Kitab doesn't use the term 'Ruchaka Yoga'. However:
         - Mars exalted in H10 (Capricorn) is considered extremely powerful ('Uchcha Mangal'), forming a 'Karmayogi' (driven worker) combination, excellent for career.
         - Mars in H1 (Aries or Scorpio) can be 'Mangal Nek' (good) or 'Mangal Bad' depending on other factors, giving strong will but potential aggression.
         - Focus is on the house Mars occupies and aspects, e.g., Mars in H3 ('Pakka Ghar') is strong. Remedies involve Mars items (honey, sindoor, helping brothers).
         """
        },
        {"category": "Mahapurusha Yoga", "name": "Bhadra Yoga", "devanagari": "भद्र योग", "planet": "Mercury",
         "formation": "Mercury in a Kendra (1st, 4th, 7th, 10th house from Ascendant) AND in its own sign (Gemini) or own & exaltation sign (Virgo).",
         "logic": "Mercury represents intellect ('Buddhi'), communication, analysis, adaptability, and skill. When strongly placed in a Kendra, these qualities become central to the native's life expression. The person's intelligence, speech, and analytical abilities define their interactions with the world and their path.",
         "bphs_results": """
         BPHS describes the native as lion-like (strong build), with a steady gait, long arms, learned, eloquent, virtuous, and having a 'satwik' nature.
         - **Effects**: Grants high intelligence, sharp analytical skills, excellent communication (writing, speaking), dexterity, success in fields like academia, commerce, astrology, law, writing, media. Gives a youthful appearance and adaptability.
         - **Variations**: Strongest in Virgo (exaltation + Mooltrikona), then Gemini. Placement modifies expression (1H: Intellectual personality, 4H: Learned mother/home environment, 7H: Intelligent partner/business, 10H: Career in communication/analysis).
         """,
         "lal_kitab_note": """
         Term not used.
         - Mercury exalted in H6 (Virgo) gives sharp intellect, good for analysis and dealing with enemies/competition, but potentially problematic for maternal relatives ('nankaa ghar').
         - Mercury in H7 ('Pakka Ghar') needs support.
         - Mercury in Gemini (e.g., H1, H4, H7, H10) is strong but analyzed based on house rules. Remedies often involve serving young girls ('kanya daan' symbolism), using green items, or piercing the nose.
         """
        },
        {"category": "Mahapurusha Yoga", "name": "Hamsa Yoga", "devanagari": "हंस योग", "planet": "Jupiter",
         "formation": "Jupiter in a Kendra (1st, 4th, 7th, 10th house from Ascendant) AND in its own sign (Sagittarius, Pisces) or exaltation sign (Cancer).",
         "logic": "Jupiter ('Guru') represents wisdom, knowledge, expansion, dharma (righteousness), wealth, and fortune. When strong in a Kendra, these divine qualities become foundational pillars of the native's life, guiding their actions and bestowing grace.",
         "bphs_results": """
         BPHS describes the native as having markings of Shankha (conch), Padma (lotus), etc. on hands/feet, handsome, virtuous, respected by rulers, fond of righteous deeds.
         - **Effects**: Grants wisdom, knowledge of scriptures/philosophy, high morals, respect, good fortune, wealth, happiness from children, often association with teaching, law, finance, or spiritual guidance.
         - **Variations**: Strongest in Cancer (exaltation), then Sagittarius (Mooltrikona), then Pisces. Placement modifies expression (1H: Wise/respected personality, 4H: Happy home/mother, good education, 7H: Noble partner, fortunate partnerships, 10H: Esteemed career in teaching/finance/law).
         """,
         "lal_kitab_note": """
         Term not used.
         - Jupiter exalted in H4 (Cancer) is considered extremely auspicious, granting immense happiness, property, and divine grace ('Dev Guru' blessings).
         - Jupiter in H9 ('Pakka Ghar') is strong for dharma and fortune.
         - Jupiter in Sagittarius/Pisces (e.g., H1, H4, H7, H10) is powerful but analyzed by house. Remedies involve wearing gold, applying saffron ('kesar') tilak, respecting elders/gurus.
         """
        },
        {"category": "Mahapurusha Yoga", "name": "Malavya Yoga", "devanagari": "मालव्य योग", "planet": "Venus",
         "formation": "Venus in a Kendra (1st, 4th, 7th, 10th house from Ascendant) AND in its own sign (Taurus, Libra) or exaltation sign (Pisces).",
         "logic": "Venus ('Shukra') represents love, beauty, arts, pleasure, luxury, relationships, and diplomacy. When strong in a Kendra, these qualities define the native's life experience, bringing refinement, comfort, and strong relationship focus.",
         "bphs_results": """
         BPHS describes the native as having a slender waist, attractive appearance, bright eyes, learned, wealthy, blessed with spouse, vehicles, and sensual enjoyments.
         - **Effects**: Grants physical beauty, charm, artistic talents (music, arts, fashion), luxurious lifestyle, vehicles, happy relationships, diplomatic skills, success in creative fields or dealing with luxuries/women.
         - **Variations**: Strongest in Pisces (exaltation), then Libra (Mooltrikona), then Taurus. Placement modifies expression (1H: Charming personality, 4H: Beautiful home/vehicles, happy mother, 7H: Attractive/loving spouse, success in partnerships, 10H: Career in arts/luxury/diplomacy).
         """,
         "lal_kitab_note": """
         Term not used.
         - Venus exalted in H12 (Pisces) gives high-level comforts and luxury ('Uchcha Shukra') but can also indicate high expenses or hidden relationships.
         - Venus in H7 ('Pakka Ghar') affects marriage significantly.
         - Venus in Taurus/Libra (e.g., H1, H4, H7, H10) is strong but analyzed by house rules. Remedies often involve serving cows ('Gau Seva'), donating ghee/curd, maintaining good character.
         """
        },
        {"category": "Mahapurusha Yoga", "name": "Sasa Yoga", "devanagari": "शश योग", "planet": "Saturn",
         "formation": "Saturn in a Kendra (1st, 4th, 7th, 10th house from Ascendant) AND in its own sign (Capricorn, Aquarius) or exaltation sign (Libra).",
         "logic": "Saturn ('Shani') represents discipline, structure, responsibility, perseverance, justice, and connection to the masses. When strong in a Kendra, these qualities form the foundation of the native's life, leading to authority and influence built through hard work and time.",
         "bphs_results": """
         BPHS describes the native as commanding armies, ruling villages or towns, potentially having questionable morals (depending on other factors), interested in others' wealth, but successful and authoritative.
         - **Effects**: Grants discipline, patience, perseverance, leadership, authority, influence over masses, success in politics, real estate, judiciary, or large organizations. Can indicate a serious demeanor. Rise often comes later in life after considerable effort.
         - **Variations**: Strongest in Libra (exaltation), then Aquarius (Mooltrikona), then Capricorn. Placement modifies expression (1H: Serious/disciplined personality, 4H: Property, influence in homeland, 7H: Mature/stable partner, public dealings, 10H: Powerful career, leadership).
         """,
         "lal_kitab_note": """
         Term not used.
         - Saturn exalted in H7 (Libra) is considered very good for wealth and status ('Uchcha Shani') but potentially problematic for marital harmony (delay or detachment).
         - Saturn in H10 ('Pakka Ghar') is strong for career.
         - Saturn in Capricorn/Aquarius (e.g., H1, H4, H7, H10) gives strong results based on house rules. Remedies involve donating oil, black cloth, serving the needy, feeding crows/snakes.
         """
        }
    ]

def get_rajyoga_data_detailed() -> List[Dict[str, Any]]:
    """Returns detailed structured data for common Rajyogas."""
    return [
        {"category": "Rajyoga", "name": "Dharma-Karmadhipati Yoga", "devanagari": "धर्म कर्माधिपति योग",
         "formation": "A connection between the lord of the 9th house (Dharma Bhava - fortune, righteousness, father, higher learning) and the lord of the 10th house (Karma Bhava - career, status, public life, action). Connection types: \n  • Conjunction (in any house, stronger in auspicious ones like Kendras/Trikonas).\n  • Mutual Aspect (Parashari aspects).\n  • Parivartana Yoga (Exchange of signs).\n  • Placement in each other's house.",
         "logic": "This yoga links the house of purpose, fortune, and divine grace (9H) with the house of action, status, and worldly achievement (10H). It signifies that the native's actions (10H) are aligned with their purpose and supported by fortune (9H), leading to significant rise, success, and recognition in their profession and public life.",
         "bphs_results": """
         Considered a Maha Raja Yoga (Great Royal Combination) in BPHS. Parashara states this makes one a 'King or equal to a King'.
         - **Effects**: Grants high status, authority, success in career, fame, wealth, virtuous conduct, leadership roles, fulfillment of ambitions. The strength depends on the involved planets' dignity, house placement, and freedom from affliction. Strongest when formed in Kendras or Trikonas.
         """,
         "lal_kitab_note": """
         The concept of linking fortune (H9 - Jupiter's domain) and career (H10 - Saturn's domain) is highly valued.
         - Conjunctions of planets ruling/representing these houses are analyzed based on the house they occur in. For example, Jupiter+Saturn can be powerful but also indicate struggle depending on placement.
         - Lal Kitab emphasizes the 'activation age' of planets and houses, suggesting such yogas might fructify strongly at specific times. Remedies aim to strengthen the positive planet and pacify any negative influences.
         """
        },
        {"category": "Rajyoga", "name": "Gaja Kesari Yoga", "devanagari": "गज केसरी योग",
         "formation": "Jupiter ('Gaja' - Elephant) is placed in a Kendra (1st, 4th, 7th, 10th house) from the Moon ('Kesari' - Lion, metaphorically). Important conditions for full effect: \n  • Jupiter and Moon should be strong (not debilitated, combust, or heavily afflicted).\n  • Ideally, Jupiter should not be in the 6th, 8th, or 12th house from the Ascendant.",
         "logic": "The Moon represents the mind, emotions, and public perception. Jupiter represents wisdom, knowledge, expansion, and benevolence. When Jupiter strongly influences the Moon from an angular position, it imbues the mind with wisdom, optimism, morality, and expansive thinking. This leads to recognition, respect, and noble conduct.",
         "bphs_results": """
         BPHS highlights this yoga's positive effects: Makes the native intelligent, virtuous, wealthy, acclaimed by rulers (authorities), possess lasting fame, build villages/towns (implying leadership/development), and destroy enemies through intellect. The analogy suggests the noble power (Jupiter) protecting/guiding the mind (Moon).
         - **Effects**: Generally bestows intelligence, good speech, virtuous nature, fame, wealth, respect, strong character, and ability to influence others positively.
         """,
         "lal_kitab_note": """
         While the specific Kendra-from-Moon rule isn't used, the combination or mutual aspect of Moon and Jupiter is considered highly auspicious ('Sona+Chandi' - Gold+Silver).
         - Jupiter exalted in H4 (Cancer - Moon's sign) strongly resonates with Gaja Kesari principles, giving immense domestic happiness and wisdom.
         - If either planet is afflicted or in a 'bad' house (e.g., H6, H8, H12), the positive effects are reduced. Remedies aim to strengthen both planets (e.g., serving mother for Moon, respecting elders for Jupiter, using silver and gold).
         """
        },
        {"category": "Rajyoga", "name": "Neecha Bhanga Rajyoga", "devanagari": "नीच भंग राजयोग",
         "formation": "Cancellation ('Bhanga') of a planet's debilitation ('Neecha'). Numerous rules exist in classical texts, key ones include:\n  • Lord of the sign where the planet is debilitated (Dispositor) is in a Kendra from Lagna or Moon.\n  • Planet which gets Exalted in the sign where the planet is debilitated is in a Kendra from Lagna or Moon.\n  • Debilitated planet is conjunct or aspected by its Exaltation Lord.\n  • Debilitated planet aspects its own sign of debilitation.\n  • Debilitated planet exchanges signs with its Dispositor (a form of Parivartana).\n  • Two debilitated planets aspect each other.\n  • Debilitated planet is exalted in the Navamsha chart (D9).",
         "logic": "A planet in debilitation is weak and struggles to express its positive qualities. 'Neecha Bhanga' implies that this weakness is overcome due to specific redeeming factors. This often signifies initial struggles, low self-esteem, or hardship related to the planet's significations, followed by a significant rise, often sudden or unexpected, as the 'cancellation' takes effect. The native gains strength through overcoming weakness.",
         "bphs_results": """
         BPHS and other classics like Phaladeepika extensively list the rules for cancellation. A properly cancelled debilitation is stated to produce results equivalent to an exalted planet ('Raja Yoga'), making the person powerful, wealthy, and virtuous. The timing often corresponds to the Dasha periods of the planets involved in the cancellation.
         - **Effects**: Potential for great success after initial struggles, resilience, overcoming adversity, achieving high status unexpectedly. The specific area of life depends on the planet and house involved.
         """,
         "lal_kitab_note": """
         Lal Kitab doesn't use the term 'Neecha Bhanga'. It analyzes debilitated planets ('Mandi Graha') based on house placement.
         - A debilitated planet might receive support ('Madaad') from friendly planets placed in specific relative positions, mitigating the negativity.
         - Some placements of debilitated planets are considered particularly bad (e.g., Sun in H7, Saturn in H1).
         - Remedies focus on strengthening supporting planets or pacifying the debilitated planet through donations or actions related to its significations (e.g., serving uncles for bad Saturn).
         """
        },
         {"category": "Rajyoga", "name": "Viparita Rajyoga", "devanagari": "विपरीत राजयोग",
         "formation": "Formed by lords of Dusthana houses (6th: Roga/Ripu - disease, debt, enemies; 8th: Randhra/Ayur - obstacles, longevity, secrets; 12th: Vyaya - loss, expense, isolation). Three types:\n  • **Harsha Yoga**: 6th Lord in 8th or 12th house.\n  • **Sarala Yoga**: 8th Lord in 6th or 12th house.\n  • **Vimala Yoga**: 12th Lord in 6th or 8th house.\n  **Crucial Condition**: The involved Dusthana lords should be relatively strong (e.g., not combust or heavily afflicted by other malefics) and SHOULD NOT be conjunct or aspected by lords of auspicious houses (Kendras, Trikonas).",
         "logic": "'Viparita' means contrary or inverse. The negative potential of one difficult house lord placed in another difficult house tends to destroy the negativity of both houses involved, leading to positive outcomes arising from adversity. It's like 'a poison nullifies another poison'. The native gains through loss, overcomes enemies through challenges, or benefits from unexpected events.",
         "bphs_results": """
         BPHS describes these yogas:
         - **Harsha**: Happiness, enjoyment, destruction of enemies, good fortune.
         - **Sarala**: Learning, prosperity, overcomes obstacles, long-lived, defeats foes.
         - **Vimala**: Frugal, independent, virtuous conduct, happiness, good profession.
         - **Effects**: Gives unexpected rise in life, sudden gains, ability to overcome powerful enemies or obstacles, success through unconventional means, often after a period of struggle or loss. Strength depends on the planets involved and lack of affliction.
         """,
         "lal_kitab_note": """
         The direct concept doesn't exist. However, planets in H6, H8, H12 are analyzed with specific rules:
         - Sometimes, a malefic planet placed in these houses is said to 'kill' the negativity of the house (e.g., Mars in H6 can destroy enemies, Ketu in H6).
         - Conversely, benefics in these houses are often considered weak or problematic ('Mande Graha').
         - Lal Kitab focuses heavily on specific conjunctions and aspects within these houses, rather than just lordship placements. Remedies are highly specific to the planets and house.
         """
        },
        {"category": "Rajyoga", "name": "Budhaditya Yoga", "devanagari": "बुधादित्य योग",
         "formation": "Conjunction of the Sun (Aditya) and Mercury (Budha) in the same house. Conditions for strength:\n  • Mercury should not be combust (too close to the Sun, typically within 8-12 degrees depending on tradition). If combust, its intellectual power is weakened.\n  • The conjunction should occur in an auspicious house (Kendra, Trikona, 2H, 11H) or in favorable signs (like Gemini, Virgo, Leo).",
         "logic": "The Sun represents soul, authority, and vitality. Mercury represents intellect, communication, and skill. Their combination synergizes these qualities, bestowing sharp intelligence, analytical ability, eloquence, learning capacity, and potential for recognition or status.",
         "bphs_results": """
         BPHS and other texts praise this yoga. It is said to grant intelligence 'equal to the Sun's brilliance', skill in arts and sciences, persuasive speech, good reputation, wealth, and physical attractiveness. The house of conjunction significantly influences the area of manifestation.
         - **Effects**: High intelligence, good education, strong communication skills, analytical mind, success in fields requiring intellect (writing, teaching, consulting, business).
         """,
         "lal_kitab_note": """
         Sun + Mercury conjunction is analyzed based on the house it occupies.
         - Very auspicious in houses like H1, H4, H5, H11, considered 'Raj Yoga Saman' (equal to Raj Yoga), promising intelligence, wealth, and status.
         - Can be problematic in certain houses (e.g., H7 - affecting spouse/partners, H10 - potentially causing career instability if afflicted).
         - Mercury's combustion ('Budh Ast') is a key factor. Remedies aim to strengthen Mercury (e.g., green items, serving sisters/aunts) or balance the Sun's dominance.
         """
         },
        {"category": "Rajyoga", "name": "Chandra Mangala Yoga", "devanagari": "चंद्र मंगल योग",
         "formation": "Conjunction of the Moon and Mars in the same house, or being in mutual aspect (opposition 7th/7th, or Mars' special 4th/8th aspect onto Moon).",
         "logic": "Combines the Moon (mind, emotions, liquidity, public) with Mars (energy, action, drive, property). This synergy creates a dynamic mind focused on action and acquisition. Mars provides the energy to manifest the Moon's desires, particularly regarding wealth and assets.",
         "bphs_results": """
         Classical texts often associate this yoga strongly with wealth generation ('Dhana Yoga'). BPHS suggests wealth possibly earned through dealings related to women, liquids, or even potentially unethical means if afflicted. It can also indicate a quick temper, impulsiveness, but also strong initiative and earning capacity.
         - **Effects**: Strong drive, ambition, ability to earn wealth quickly, potential for property ownership, energetic mind, sometimes impatience or emotional volatility. Strength depends on sign/house placement and aspects.
         """,
         "lal_kitab_note": """
         Moon + Mars is generally considered a 'Lakshmi Yoga', highly auspicious for wealth ('Paisa'). Mars provides support ('Madaad') to the Moon (cash flow).
         - Its effect is highly house-dependent. For example, in H4 (Moon's 'Pakka Ghar'), it can be excellent for property but potentially bad for mother's peace due to Mars. In H6, it might lead to debt issues.
         - Remedies often focus on Mars (donating 'masoor dal', honey, sindoor) to channel its energy positively.
         """
        },
        # Add more Rajyogas here...
    ]

def get_dosha_data_detailed() -> List[Dict[str, Any]]:
    """Returns detailed structured data for common Doshas."""
    return [
        {"category": "Dosha", "name": "Manglik Dosha", "devanagari": "मांगलिक दोष",
         "formation": "Mars placed in the 1st (personality), 4th (domestic peace), 7th (spouse), 8th (marital longevity/obstacles), or 12th (bed pleasures/loss) house from the Ascendant (Lagna), Moon (Chandra Lagna), or Venus (Kalatra Karaka). Some traditions (esp. South India) also include the 2nd house (family/speech).",
         "logic": "Mars is a fiery, aggressive planet representing energy, conflict, and separation. Its placement in these sensitive houses related to self, home, partnership, and intimacy disrupts harmony. It injects Martian qualities (aggression, dominance, impatience, accidents) into areas requiring sensitivity and compromise, leading to marital friction, separation, or potential harm/ill health to the partner.",
         "bphs_results": """
         BPHS (Stree Jataka chapter) explicitly links Mars in these houses (1, 4, 7, 8, 12) to potential widowhood for a female, implying danger to the spouse. It states the effect applies equally causing widower-hood for males.
         - **Cancellation (Bhanga)**: The primary cancellation mentioned in BPHS is marriage to another person with a similar Manglik Dosha, nullifying the effect. Other classical cancellations include: Mars in own sign (Aries/Scorpio) or exaltation (Capricorn), Mars aspected by strong benefics (esp. Jupiter), Mars in certain signs within these houses (e.g., Mars in Leo/Aquarius often considered less malefic), presence of strong benefics in Kendras.
         """,
         "lal_kitab_note": """
         Lal Kitab doesn't use the specific 1/4/7/8/12 house rule from Lagna/Moon/Venus. It identifies 'Mangal Bad' (Bad Mars) based on specific house placements or conjunctions, regardless of marriage implications:
         - Mars in H1 or H8 is often considered 'Bad'.
         - Mars in H4 is particularly bad, said to 'burn' family happiness.
         - Mars conjunct Saturn is highly problematic ('Manda Mangal').
         - Remedies focus on pacifying Mars ('Thanda Karna') or improving its effects, e.g., feeding sweet tandoori roti to dogs, donating 'masoor dal' (red lentils), keeping an elephant tusk (real/ivory substitute), respecting brothers.
         """
        },
        {"category": "Dosha", "name": "Kaal Sarpa Dosha", "devanagari": "काल सर्प दोष",
         "formation": "All seven classical planets (Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn) are located between the Rahu-Ketu axis (within 180 degrees). Two main types:\n  • **Anuloma**: Planets moving towards Rahu (Ketu -> Rahu direction).\n  • **Viloma**: Planets moving towards Ketu (Rahu -> Ketu direction).\n  Partial Kaal Sarpa is when one planet escapes the axis.",
         "logic": "(Modern Interpretation) Rahu (the head - insatiable desire, future karma) and Ketu (the tail - detachment, past karma) represent the karmic axis. When all planets are 'hemmed' or 'trapped' between them, the native's life is strongly influenced by this karmic pull. It suggests a life where free will feels constrained, events happen suddenly, and progress is often blocked or delayed until the karmic pattern is worked through (often stated to be effective up to mid-life).",
         "bphs_results": """
         **This yoga is NOT mentioned in BPHS** or other primary classical astrological texts like Phaladeepika, Jataka Parijata, Saravali. It gained prominence in 20th-century Indian astrology. Classical scholars argue that Rahu/Ketu act through their dispositors and conjunctions, and this 'hemming' concept is not a standalone principle in Parashari astrology. The effects attributed to it can often be explained by other classical combinations involving Rahu/Ketu or house lordships.
         """,
         "lal_kitab_note": """
         Lal Kitab **does not use the term 'Kaal Sarpa Dosha'**.
         - It analyzes Rahu and Ketu based on their house placement, conjunctions, and aspects according to its unique principles.
         - For example, Rahu in H12 ('Pakka Ghar') or Ketu in H6 ('Pakka Ghar') have specific interpretations. Conjunctions like Rahu+Moon (Grahan) or Rahu+Jupiter (Chandal) are given specific meanings and remedies.
         - Remedies are always specific to Rahu or Ketu based on their position and affliction (e.g., floating coal/barley/radish, keeping items like solid silver elephant).
         """
        },
        {"category": "Dosha", "name": "Pitra Dosha", "devanagari": "पितृ दोष",
         "formation": "A broad category indicating ancestral afflictions or karmic debts. No single combination, but common indicators include:\n  • **Sun afflicted**: Sun (significator of father/lineage) conjunct/aspected by Saturn, Rahu, or Ketu, especially in malefic houses or debilitation (Libra).\n  • **9th House afflicted**: 9H (father, ancestors, past merits) or 9th Lord afflicted by Saturn, Rahu, Ketu, or lords of Dusthanas.\n  • **Moon afflicted**: Moon (mother/mind) can also indicate maternal lineage issues if afflicted similarly.\n  • **Rahu/Ketu axis**: Across Lagna/7H or 2H/8H involving Sun/Moon/Jupiter.",
         "logic": "The Sun and 9th house represent the connection to the paternal lineage, ancestors ('Pitrs'), and the store of past good karma ('Punya'). Afflictions indicate unresolved issues, unfulfilled duties, or negative karmic patterns passed down ('Rin' - debt) or curses ('Shrap') from ancestors. This blockage manifests as obstacles in the native's life, particularly concerning progeny (5H often gets impacted), health, finances, and overall well-being, as the ancestral blessings are obstructed.",
         "bphs_results": """
         BPHS has a specific chapter titled **'Purva Janma Shapadyaya' (Curses from Past Lives)** which is the classical foundation for Pitra Dosha. It details numerous specific combinations indicating curses from father, mother, brother, spouse, Brahmin, etc., primarily manifesting as difficulty or denial in having children.
         - **Example (Father's Curse)**: Sun in debilitation (Libra) in 5H, 5th Lord with malefic, Lagna Lord weak/afflicted.
         - **Remedies**: BPHS suggests remedies like Japa (mantra), Homa (fire ritual), Daana (charity), Tarpana/Shraddha (rituals for ancestors), feeding Brahmins, and specific worship based on the afflicting planet.
         """,
         "lal_kitab_note": """
         **Pitra Rin (Ancestral Debt) is a fundamental concept in Lal Kitab.** It believes certain planetary placements indicate specific debts owed due to actions (or inactions) of ancestors, which the native must remedy ('Upay').
         - **Examples**: Jupiter in H5 (debt related to Guru/father), Venus in H2/H7 afflicted (debt related to wife/mother figure), Saturn in H10/H11 afflicted (debt related to property/livelihood).
         - **Diagnosis**: Based on specific planet+house combinations.
         - **Remedies**: Unique and specific to the identified debt, often involving collective action by blood relatives (e.g., collecting equal money for religious purpose), serving specific relatives (e.g., uncles for Saturn), or specific donations/rituals.
         """
        },
        # ... (Include other Doshas like Grahan, Kendradhipati, etc. with similar detailed structure) ...
         {"category": "Dosha", "name": "Grahan Dosha", "devanagari": "ग्रहण दोष",
         "formation": "'Eclipse Affliction'. Sun or Moon conjunct Rahu or Ketu in the same house. Proximity (degrees) matters; closer conjunction is stronger.",
         "logic": "Rahu (North Node) and Ketu (South Node) are the astronomical points where eclipses occur. They are considered shadow entities that 'overpower' or 'afflict' the luminaries (Sun - soul, authority; Moon - mind, emotions) when conjunct. This dims the natural light and signifies psychological complexes, internal conflicts, or challenges related to the significations of the luminary involved.",
         "bphs_results": """
         BPHS describes the results of Sun/Moon conjunctions with Rahu/Ketu:
         - **Sun+Rahu/Ketu**: Can indicate issues with father, authority figures, government; lack of self-confidence, ego problems, health issues (heart, bones, eyes); potential for unconventional fame or downfall.
         - **Moon+Rahu/Ketu**: Indicates mental turmoil, emotional instability, phobias, illusions, difficult relationship with mother; potential for psychic sensitivity or psychological issues; fluctuations in public life. Affliction is stronger during eclipses near the time of birth.
         """,
         "lal_kitab_note": """
         Called 'Grahan Yoga' (Eclipse Yoga). Considered highly significant and problematic.
         - **Sun+Rahu**: Bad for father, government favors, reputation. Remedy: Floating coal ('koyla') or wheat ('gehu') in running water.
         - **Sun+Ketu**: Bad for progeny (son), bodily health (joints). Remedy: Feeding monkeys (related to Sun), helping son/nephew.
         - **Moon+Rahu**: Bad for mother, mental peace, finances ('khazana'). Remedy: Floating barley ('jau') washed in milk, wearing silver.
         - **Moon+Ketu**: Bad for mother and progeny (son), causes detachment or mental confusion. Remedy: Feeding dogs (Ketu), wearing gold in ear (for progeny). The house of conjunction heavily modifies results.
         """
        },
        {"category": "Dosha", "name": "Kendradhipati Dosha", "devanagari": "केन्द्राधिपति दोष",
         "formation": "Applies ONLY to natural benefic planets (Jupiter, Venus, Mercury, strong/waxing Moon) when they OWN a Kendra house (1st, 4th, 7th, 10th from Ascendant). The 1st house lordship is generally exempt as it's also a Trikona. The dosha is strongest for Jupiter and Mercury owning the 7th or 10th.",
         "logic": "This is a core Parashari principle of functional nature. Kendras are pillars requiring strong 'guards'. Benefics are considered 'gentle' and thus less effective or even obstructive when ruling these powerful houses; they lose some inherent beneficence. Conversely, natural malefics (Saturn, Mars) are 'tough' and become better 'guards', thus shedding some maleficence when ruling Kendras (esp. if not also ruling a Trikona).",
         "bphs_results": """
         This principle is fundamental to how BPHS determines the functional benefic/malefic nature of planets for each Ascendant.
         - **Example**: For Gemini Ascendant, Jupiter (great benefic) owns 7H & 10H (two Kendras) and is classified as a functional malefic, capable of causing significant issues during its Dasha. For Virgo Ascendant, Jupiter owns 4H & 7H, also gaining this dosha. Venus for Cancer (owns 4H/11H) or Leo (owns 3H/10H) gets the dosha from Kendra ownership.
         - **Cancellation**: If the benefic also owns a Trikona (1H, 5H, 9H), it becomes a powerful Yogakaraka, cancelling the dosha (e.g., Venus for Capricorn/Aquarius, Mars for Cancer/Leo). Placement in Dusthanas (6, 8, 12) can sometimes mitigate the dosha by weakening the planet's ability to obstruct.
         """,
         "lal_kitab_note": """
         **This concept of functional maleficence based on Kendra lordship DOES NOT EXIST in Lal Kitab.**
         - Planets are analyzed based on their inherent nature, house placement ('Pakka Ghar', 'Khaana'), conjunctions, aspects (Lal Kitab aspects are different), and ' सोया / जागा' (sleeping/awake) status.
         - A benefic like Jupiter is always considered fundamentally benefic, but its results depend entirely on its house and combinations according to LK rules, not its Kendra lordship.
         """
        },
         {"category": "Dosha", "name": "Guru Chandal Dosha", "devanagari": "गुरु चांडाल दोष",
         "formation": "Conjunction of Jupiter (Guru) and Rahu (Chandal - signifies outcast, unorthodox) OR Jupiter and Ketu in the same house.",
         "logic": "Jupiter represents wisdom, dharma, teachers, expansion, and traditional knowledge. Rahu represents obsession, illusion, foreign influences, unconventionality, and breaking norms. Ketu represents detachment, past karma, headless action, spirituality, and criticism. \n  • **Jupiter+Rahu**: Rahu's obsessive, materialistic, and unorthodox energy 'pollutes' or overshadows Jupiter's wisdom and ethics. Can lead to flawed judgment, disrespect for gurus/tradition, using knowledge for selfish ends, unorthodox beliefs, or association with 'outcast' elements.\n  • **Jupiter+Ketu**: Ketu's critical, headless, or detached energy can undermine Jupiter's faith and expansion. Can lead to excessive self-criticism, doubt in teachers/beliefs, rejecting traditional wisdom, spiritual confusion, or focusing only on flaws.",
         "bphs_results": """
         Classical texts consider these challenging conjunctions.
         - **Jupiter+Rahu**: Often linked to heterodoxy, association with lower strata or foreigners, potential for financial speculation (Rahu amplifying Jupiter's wealth signification), but also clouded judgment and ethical compromises.
         - **Jupiter+Ketu**: Can indicate deep spiritual seeking but also breaks in education, dissatisfaction with gurus, challenges with children, or sharp critical abilities used negatively. Effects highly dependent on sign, house, and strength.
         """,
         "lal_kitab_note": """
         Analyzed based on house.
         - **Jupiter+Rahu**: Described as 'Hathi Be-Mahavat' (Elephant without a driver). Rahu (elephant) overpowers Jupiter (driver). Generally gives bad results for the house they occupy, causing misguided expansion or obsession. Remedies aim to separate them (e.g., wear gold for Jupiter, keep Rahu items like fennel separately).
         - **Jupiter+Ketu**: Considered somewhat better than Jup+Rahu, especially in certain houses. Ketu (son) can sometimes follow Jupiter's (grandfather) guidance. However, can still cause issues related to progeny or spiritual path. Remedies might involve serving elders (Jupiter) and dogs (Ketu).
         """
        },
        {"category": "Dosha", "name": "Vish Yoga", "devanagari": "विष योग",
         "formation": "'Poison Yoga'. Formed by the conjunction of Saturn (Shani) and the Moon (Chandra) in the same house, OR their strong mutual aspect (opposition 7/7, Saturn's 3rd/10th aspect on Moon, Moon aspecting Saturn).",
         "logic": "The Moon represents the mind ('Manas'), emotions, mother, nourishment, and is soft/watery/receptive. Saturn represents sorrow ('Duhkha'), restriction, delays, coldness, discipline, and is hard/cold/dry/constrictive. When Saturn strongly influences the Moon, its heavy, pessimistic, and 'poisonous' qualities afflict the sensitive mind. This creates emotional blockages, pessimism, melancholy, fear, detachment from mother, or difficulty feeling/expressing emotions.",
         "bphs_results": """
         This is a well-known and generally feared classical yoga. BPHS and other texts associate it with mental suffering, sorrow, emotional coldness, pessimism, difficulties with the mother, and potential for depression or psychological issues depending on severity and house placement (stronger in Kendras or afflicting Lagna). It can also make one disciplined and capable of enduring hardship, but often at the cost of emotional well-being.
         """,
         "lal_kitab_note": """
         Considered a very negative combination ('Zeher' - poison).
         - Described as 'Maa ke doodh mein zeher' (poison in mother's milk) or 'Chandrama par Saanp ka pehra' (snake guarding the Moon).
         - Highly detrimental to mental peace, mother's health/relationship, and finances (Moon represents liquidity).
         - Effects vary by house (e.g., in H4 can ruin domestic peace, in H10 affects career).
         - Remedies often involve separating their energies: Offering milk (Moon) on a Shivalingam (Saturn), donating Saturn items (oil, black cloth) while strengthening Moon (silver, pearls, serving mother), avoiding black/blue colors.
         """
        },
        {"category": "Dosha", "name": "Kemadruma Dosha", "devanagari": "केमद्रुम दोष",
         "formation": "A major lunar dosha. Formed when there are NO planets (excluding the Sun, Rahu, and Ketu - Nodes are considered shadow points) in the 2nd house AND the 12th house counted *from the Moon's position*.",
         "logic": "The Moon (mind) thrives on connection and reflection (planets nearby). The 2nd house from any point represents resources/support immediately following it, and the 12th represents support/expenditure just behind it. When both these adjacent houses are empty, the Moon is left isolated (' अकेली चंद्रमा '). This signifies a lack of immediate emotional, social, or financial support structure around the mind, leading to feelings of loneliness, instability, poverty, and mental distress.",
         "bphs_results": """
         BPHS describes Kemadruma Yoga as causing poverty, sorrow, hard work with little reward, dependence on others, and a generally miserable or isolated existence. It is considered a strong 'Daridra Yoga' (yoga for poverty).
         - **HOWEVER, BPHS and other texts give MANY CANCELLATIONS (Bhanga)** which are extremely common, making the *uncancelled* Kemadruma quite rare. Key cancellations include:
           • Planets in a Kendra (1, 4, 7, 10) *from the Moon*.
           • Planets in a Kendra *from the Ascendant*.
           • Moon conjunct any planet (other than Sun/Nodes).
           • Moon aspected by Jupiter.
           • Moon in Navamsha exalted or in own sign.
           • All planets aspecting the Moon.
           If cancelled, the dosha's negative effects are greatly reduced or nullified.
         """,
         "lal_kitab_note": """
         The specific configuration of planets flanking the Moon (2nd/12th empty) is **not a primary concept** in Lal Kitab.
         - The Moon's condition is assessed based on the HOUSE it occupies (e.g., Moon in H6, H8, H12 is generally bad), its conjunctions (e.g., Moon+Saturn = Vish Yoga, Moon+Rahu = Grahan), and whether it's 'sleeping' or 'awake'.
         - Loneliness or lack of support would be interpreted based on afflictions to the Moon or houses like H4 (home/mother) or H11 (friends/network). Remedies would target the specific affliction found according to LK principles.
         """
        }
    ]

class YogasDoshasTab(ttk.Frame):
    """
    This class defines the "Yogas & Doshas" tab using a list/detail layout
    with category separators in the listbox.
    """
    def __init__(self, parent: ttk.Notebook, app: 'AstroVighatiElite') -> None:
        super().__init__(parent)
        self.app = app

        # Combine and Sort Data
        self.all_data = get_mahapurusha_data_detailed() + get_rajyoga_data_detailed() + get_dosha_data_detailed()
        self.all_data.sort(key=lambda item: (item['category'], item['name']))

        # Define theme colors and category specifics
        self.theme_bg = "#2e2e2e"
        self.theme_fg = "#ffffff"
        self.select_bg = "#005f9e"
        self.header_fg = "#ffcc66" # Gold for headers
        self.separator_fg = "#aaaaaa" # Lighter gray for separators
        self.category_info = {
            "Dosha": {"icon": "🔥", "color": "#FFA07A"}, # Light Salmon
            "Mahapurusha Yoga": {"icon": "🌟", "color": "#ADD8E6"}, # Light Blue
            "Rajyoga": {"icon": "👑", "color": "#90EE90"}, # Light Green
            "Unknown": {"icon": "❓", "color": self.theme_fg} # Default
        }

        # This will map listbox index to original self.all_data index
        self.listbox_map: List[int] = []
        # This will store indices of separator items
        self.separator_indices: List[int] = []

        self.create_styles()
        self.create_ui()

    def create_styles(self):
        """Configure custom ttk styles."""
        style = ttk.Style()
        style.configure("YogaDoshaHeader.TLabel", foreground=self.header_fg,
                        font=('Segoe UI', 13, 'bold'))
        style.map("TEntry",
                  fieldbackground=[('!focus', self.theme_bg)],
                  foreground=[('!focus', self.theme_fg)],
                  insertcolor=[('', self.theme_fg)])

    def create_ui(self) -> None:
        paned = ttk.PanedWindow(self, orient='horizontal')
        paned.pack(expand=True, fill='both', padx=15, pady=15)

        # Left Panel (List & Search)
        left_panel = ttk.Frame(paned, padding=(15, 10))
        paned.add(left_panel, weight=1)

        ttk.Label(left_panel, text="🔮 YOGA & DOSHA LIST", style='YogaDoshaHeader.TLabel').pack(pady=(0, 15))

        # Search Box
        self.search_var = tk.StringVar()
        self.search_var.trace_add('write', self.filter_list)
        search_entry = ttk.Entry(left_panel, textvariable=self.search_var, width=30,
                                font=('Segoe UI', 10))
        search_entry.pack(fill='x', pady=(0, 10))

        # Listbox Frame
        list_frame = ttk.Frame(left_panel)
        list_frame.pack(fill='both', expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient='vertical')
        self.item_listbox = tk.Listbox(
            list_frame,
            font=('Segoe UI', 11),
            exportselection=False,
            yscrollcommand=scrollbar.set,
            background=self.theme_bg,
            foreground=self.theme_fg,
            selectbackground=self.select_bg,
            selectforeground=self.theme_fg,
            highlightthickness=0,
            borderwidth=0,
            activestyle='none',
            relief='flat'
        )
        scrollbar.config(command=self.item_listbox.yview)
        scrollbar.pack(side='right', fill='y')
        self.item_listbox.pack(side='left', fill='both', expand=True)
        self.item_listbox.bind('<<ListboxSelect>>', self.on_select)

        # Right Panel (Details)
        right_panel = ttk.Frame(paned, padding=(15, 10, 0, 10))
        paned.add(right_panel, weight=3) # Increased weight

        # Header Label for the right panel
        self.item_header_label = ttk.Label(right_panel, text="", style="YogaDoshaHeader.TLabel")
        self.item_header_label.pack(pady=(0, 15), fill='x', anchor='w')

        # Create self.item_text HERE
        self.item_text = scrolledtext.ScrolledText(
            right_panel,
            font=("Courier New", 10), # Monospace for details
            wrap='word',
            padx=15,
            pady=15,
            background=self.theme_bg,
            foreground=self.theme_fg,
            highlightthickness=0,
            borderwidth=0,
            relief='flat',
            insertbackground=self.theme_fg
        )
        self.item_text.pack(fill='both', expand=True)

        # Populate Listbox and Select First Item AFTER Both Panels are Created
        self.populate_list()
        self.select_first_item()

    def select_first_item(self):
         """Selects the first non-separator item in the list."""
         if self.item_listbox.size() > 0:
             first_valid_index = -1
             for i in range(self.item_listbox.size()):
                 if i not in self.separator_indices:
                     first_valid_index = i
                     break
             if first_valid_index != -1:
                 # Ensure listbox is updated before trying to select
                 self.item_listbox.update_idletasks()
                 try:
                     self.item_listbox.selection_set(first_valid_index)
                     self.item_listbox.see(first_valid_index) # Scroll to selection
                     self.on_select(None) # Trigger display
                 except tk.TclError:
                     print(f"Warning: Could not select index {first_valid_index} initially.")


    def populate_list(self, filter_term: Optional[str] = None) -> None:
        """Fills/Refills the listbox, optionally filtering, adding separators when not filtering."""
        self.item_listbox.delete(0, tk.END)
        self.listbox_map = []
        self.separator_indices = []
        search_term = filter_term.lower() if filter_term else None
        current_category = None
        listbox_idx = 0

        for original_data_index, item in enumerate(self.all_data):
            category = item.get('category', 'Unknown')
            name = item.get('name', 'N/A')
            devanagari = item.get('devanagari', '')

            # Filtering Logic
            should_add = True
            if search_term:
                match = (search_term in name.lower() or
                         search_term in category.lower() or
                         search_term in item.get('planet','').lower() or
                         search_term in devanagari.lower())
                if not match:
                    should_add = False

            if should_add:
                # Add Separator Header (only if NOT filtering)
                if not search_term and category != current_category:
                    category_display = category.replace(" Yoga", "").upper()
                    separator_text = f"────── {category_display} ──────"
                    self.item_listbox.insert(tk.END, separator_text)
                    self.item_listbox.itemconfig(listbox_idx,
                                                foreground=self.separator_fg,
                                                selectbackground=self.theme_bg,
                                                selectforeground=self.separator_fg)
                    self.separator_indices.append(listbox_idx)
                    listbox_idx += 1
                    current_category = category

                # Add the Actual Item
                info = self.category_info.get(category, self.category_info["Unknown"])
                display_name = f" {info['icon']} {name} ({devanagari})"
                self.item_listbox.insert(tk.END, display_name)
                self.item_listbox.itemconfig(listbox_idx, foreground=info['color'])
                self.listbox_map.append(original_data_index)
                listbox_idx += 1


    def filter_list(self, *args: Any) -> None:
        """Calls populate_list with the current search term and handles selection."""
        search_term = self.search_var.get()
        self.populate_list(search_term)
        
        # Select first match after filtering or clear if no match
        if self.item_listbox.size() > 0:
             first_valid_index = -1
             for i in range(self.item_listbox.size()):
                 if i not in self.separator_indices: # Ensure it's not a separator
                     first_valid_index = i
                     break
             if first_valid_index != -1:
                 self.item_listbox.selection_set(first_valid_index)
                 self.on_select(None)
             else: # Only separators left, clear details
                 self.item_header_label.config(text="")
                 self.item_text.config(state='normal')
                 self.item_text.delete('1.0', tk.END)
                 self.item_text.insert('1.0', "  No matching Yogas or Doshas found.")
                 self.item_text.config(state='disabled')
        else: # Listbox is completely empty
            self.item_header_label.config(text="")
            self.item_text.config(state='normal')
            self.item_text.delete('1.0', tk.END)
            self.item_text.insert('1.0', "  No matching Yogas or Doshas found.")
            self.item_text.config(state='disabled')


    def on_select(self, event: Optional[tk.Event]) -> None:
        """Called when a user clicks on an item in the listbox."""
        selection = self.item_listbox.curselection()
        if not selection: return

        selected_listbox_index = selection[0]

        # Prevent selection/action on separators
        if selected_listbox_index in self.separator_indices:
             # Find the next valid item index if possible
             next_valid_index = -1
             for i in range(selected_listbox_index + 1, self.item_listbox.size()):
                 if i not in self.separator_indices:
                     next_valid_index = i
                     break
             # If a valid item is found below, select it instead
             if next_valid_index != -1:
                 self.item_listbox.selection_clear(0, tk.END)
                 self.item_listbox.selection_set(next_valid_index)
                 self.item_listbox.activate(next_valid_index)
                 self.item_listbox.see(next_valid_index)
                 # Manually call on_select again for the NEW selection
                 self.after(10, lambda: self.on_select(None)) # Use 'after' to avoid recursion depth issues
             return # Stop processing the separator click

        # Calculate correct index in listbox_map
        num_separators_before = sum(1 for sep_idx in self.separator_indices if sep_idx < selected_listbox_index)
        map_index = selected_listbox_index - num_separators_before

        if 0 <= map_index < len(self.listbox_map):
            original_data_index = self.listbox_map[map_index]
            item_data = self.all_data[original_data_index]
            self.show_details(item_data)
        else:
             # Error handling
             self.item_text.config(state='normal')
             self.item_text.delete('1.0', tk.END)
             self.item_text.insert('1.0', f"Error: Index mapping failed for selection {selected_listbox_index}.")
             self.item_text.config(state='disabled')


    def show_details(self, item: Dict[str, Any]) -> None:
        """Displays the formatted details for a selected Yoga/Dosha."""
        self.item_text.config(state='normal')
        self.item_text.delete('1.0', tk.END)

        category = item.get('category', 'Unknown')
        name = item.get('name', 'N/A')
        devanagari = item.get('devanagari', '')

        info = self.category_info.get(category, self.category_info["Unknown"])
        self.item_header_label.config(text=f" {info['icon']} {name} ({devanagari})")

        separator = "─" * 66

        def wrap_text(text: str, width: int = 66, indent='  ') -> str:
            if not text or not text.strip(): return indent + "N/A"
            text_str = str(text)
            lines = text_str.split('\n')
            wrapped_lines = []
            for line in lines:
                 # Check if line contains bullet points (•) or numbered lists (e.g., '• ')
                 is_list_item = line.strip().startswith('•') or (len(line.strip()) > 1 and line.strip()[0].isdigit() and line.strip()[1:3] in ['. ','- '])
                 
                 # Adjust subsequent indent for list items to maintain alignment
                 sub_indent = indent + '  ' if is_list_item else indent
                 
                 wrapped_line = textwrap.fill(
                     line.strip(), 
                     width=width,
                     initial_indent=indent,
                     subsequent_indent=sub_indent, # Use adjusted indent
                     break_long_words=False,
                     replace_whitespace=False
                 )
                 if not line.strip():
                      wrapped_lines.append("") # Keep paragraph breaks as empty lines
                 else:
                      wrapped_lines.append(wrapped_line)

            final_text = '\n'.join(wrapped_lines) if wrapped_lines else indent + "N/A"
            return final_text


        details = f"""
 [{category.upper()}]
{separator}

 FORMATION:
{separator}
{wrap_text(item.get('formation', 'N/A'))}
"""
        if 'planet' in item:
             details += f"""
   {'Planet Involved':<18}: {item['planet']}
"""

        details += f"""
 ASTROLOGICAL LOGIC:
{separator}
{wrap_text(item.get('logic', 'N/A'))}

 BPHS / CLASSICAL RESULTS:
{separator}
{wrap_text(item.get('bphs_results', 'N/A'))}

 LAL KITAB PERSPECTIVE:
{separator}
{wrap_text(item.get('lal_kitab_note', 'N/A'))}
"""
        self.item_text.insert('1.0', details.strip())
        self.item_text.config(state='disabled')
        
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