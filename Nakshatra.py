# -*- coding: utf-8 -*-
"""
Vedic Birth Time Estimator

An application to determine an approximate birth time window based on a person's
name and date of birth, using the principles of Vedic astrology.

Methodology:
1.  Name to Syllable: The first letters of the name are matched to a Vedic syllable.
2.  Syllable to Nakshatra Pada: The syllable corresponds to one of the 108 Nakshatra
    Padas, which gives a specific 3°20' arc in the zodiac.
3.  Date to Moon Longitude: For the given date of birth, the program calculates
    the Moon's sidereal longitude throughout the day.
4.  Time Window Finding: The application identifies the time range during which
    the Moon was transiting through the specific zodiacal arc identified from the name.
"""

import datetime
import sys
import math
from typing import Optional, Dict, Tuple, NamedTuple
from dataclasses import dataclass
import tkinter as tk
from tkinter import ttk, messagebox

# ==================== DATA MODELS ====================

@dataclass
class NakshatraData:
    """An immutable data class for storing Nakshatra information."""
    name: str
    lord: str
    syllables: Tuple[str, ...]
    rashi_mapping: Tuple[str, ...]

class PredictionResult(NamedTuple):
    """A structure for holding the results of a prediction."""
    nakshatra: str
    pada: int
    rashi: str
    syllable: str
    time_start: Optional[datetime.datetime]
    time_end: Optional[datetime.datetime]
    nakshatra_lord: str

# ==================== CONSTANTS & VEDIC DATA ====================

# The span of one Nakshatra is 13 degrees 20 minutes.
NAKSHATRA_SPAN = 13.333333333333333
# The span of one Rashi (Zodiac Sign) is 30 degrees.
RASHI_SPAN = 30.0

# The starting longitude (in degrees) for each Nakshatra.
NAKSHATRA_LONGITUDES = [
    ('Ashwini', 0.0), ('Bharani', 13.333), ('Krittika', 26.666),
    ('Rohini', 40.0), ('Mrigashirsha', 53.333), ('Ardra', 66.666),
    ('Punarvasu', 80.0), ('Pushya', 93.333), ('Ashlesha', 106.666),
    ('Magha', 120.0), ('Purva Phalguni', 133.333), ('Uttara Phalguni', 146.666),
    ('Hasta', 160.0), ('Chitra', 173.333), ('Swati', 186.666),
    ('Vishakha', 200.0), ('Anuradha', 213.333), ('Jyeshtha', 226.666),
    ('Mula', 240.0), ('Purva Ashadha', 253.333), ('Uttara Ashadha', 266.666),
    ('Shravana', 280.0), ('Dhanishtha', 293.333), ('Shatabhisha', 306.666),
    ('Purva Bhadrapada', 320.0), ('Uttara Bhadrapada', 333.333), ('Revati', 346.666)
]

# Database of Nakshatras, their lords, syllables, and Rashi mappings.
NAKSHATRA_DATABASE: Dict[str, NakshatraData] = {
    'Ashwini': NakshatraData('Ashwini (अश्विनी)', 'Ketu', ('Chu', 'Che', 'Cho', 'La'), ('Aries (मेष)',) * 4),
    'Bharani': NakshatraData('Bharani (भरणी)', 'Venus', ('Li', 'Lu', 'Le', 'Lo'), ('Aries (मेष)',) * 4),
    'Krittika': NakshatraData('Krittika (कृत्तिका)', 'Sun', ('A', 'Ee', 'U', 'E'), ('Aries (मेष)', 'Taurus (वृषभ)', 'Taurus (वृषभ)', 'Taurus (वृषभ)')),
    'Rohini': NakshatraData('Rohini (रोहिणी)', 'Moon', ('O', 'Va', 'Vi', 'Vu'), ('Taurus (वृषभ)',) * 4),
    'Mrigashirsha': NakshatraData('Mrigashirsha (मृगशीर्ष)', 'Mars', ('Ve', 'Vo', 'Ka', 'Ki'), ('Taurus (वृषभ)', 'Taurus (वृषभ)', 'Gemini (मिथुन)', 'Gemini (मिथुन)')),
    'Ardra': NakshatraData('Ardra (आर्द्रा)', 'Rahu', ('Ku', 'Gha', 'Na', 'Chha'), ('Gemini (मिथुन)',) * 4),
    'Punarvasu': NakshatraData('Punarvasu (पुनर्वसु)', 'Jupiter', ('Ke', 'Ko', 'Ha', 'Hi'), ('Gemini (मिथुन)', 'Gemini (मिथुन)', 'Gemini (मिथुन)', 'Cancer (कर्क)')),
    'Pushya': NakshatraData('Pushya (पुष्य)', 'Saturn', ('Hu', 'He', 'Ho', 'Da'), ('Cancer (कर्क)',) * 4),
    'Ashlesha': NakshatraData('Ashlesha (आश्लेषा)', 'Mercury', ('Di', 'Du', 'De', 'Do'), ('Cancer (कर्क)',) * 4),
    'Magha': NakshatraData('Magha (मघा)', 'Ketu', ('Ma', 'Mi', 'Mu', 'Me'), ('Leo (सिंह)',) * 4),
    'Purva Phalguni': NakshatraData('Purva Phalguni (पूर्व फाल्गुनी)', 'Venus', ('Mo', 'Ta', 'Ti', 'Tu'), ('Leo (सिंह)',) * 4),
    'Uttara Phalguni': NakshatraData('Uttara Phalguni (उत्तर फाल्गुनी)', 'Sun', ('Te', 'To', 'Pa', 'Pi'), ('Leo (सिंह)', 'Virgo (कन्या)', 'Virgo (कन्या)', 'Virgo (कन्या)')),
    'Hasta': NakshatraData('Hasta (हस्त)', 'Moon', ('Pu', 'Sha', 'Na', 'Tha'), ('Virgo (कन्या)',) * 4),
    'Chitra': NakshatraData('Chitra (चित्रा)', 'Mars', ('Pe', 'Po', 'Ra', 'Ri'), ('Virgo (कन्या)', 'Virgo (कन्या)', 'Libra (तुला)', 'Libra (तुला)')),
    'Swati': NakshatraData('Swati (स्वाति)', 'Rahu', ('Ru', 'Re', 'Ro', 'Ta'), ('Libra (तुला)',) * 4),
    'Vishakha': NakshatraData('Vishakha (विशाखा)', 'Jupiter', ('Ti', 'Tu', 'Te', 'To'), ('Libra (तुला)', 'Libra (तुला)', 'Libra (तुला)', 'Scorpio (वृश्चिक)')),
    'Anuradha': NakshatraData('Anuradha (अनुराधा)', 'Saturn', ('Na', 'Ni', 'Nu', 'Ne'), ('Scorpio (वृश्चिक)',) * 4),
    'Jyeshtha': NakshatraData('Jyeshtha (ज्येष्ठा)', 'Mercury', ('No', 'Ya', 'Yi', 'Yu'), ('Scorpio (वृश्चिक)',) * 4),
    'Mula': NakshatraData('Mula (मूल)', 'Ketu', ('Ye', 'Yo', 'Bha', 'Bhi'), ('Sagittarius (धनु)',) * 4),
    'Purva Ashadha': NakshatraData('Purva Ashadha (पूर्व आषाढ़)', 'Venus', ('Bhu', 'Dha', 'Pha', 'Dha'), ('Sagittarius (धनु)',) * 4),
    'Uttara Ashadha': NakshatraData('Uttara Ashadha (उत्तर आषाढ़)', 'Sun', ('Bhe', 'Bho', 'Ja', 'Ji'), ('Sagittarius (धनु)', 'Capricorn (मकर)', 'Capricorn (मकर)', 'Capricorn (मकर)')),
    'Shravana': NakshatraData('Shravana (श्रवण)', 'Moon', ('Khi', 'Khu', 'Khe', 'Kho'), ('Capricorn (मकर)',) * 4),
    'Dhanishtha': NakshatraData('Dhanishtha (धनिष्ठा)', 'Mars', ('Ga', 'Gi', 'Gu', 'Ge'), ('Capricorn (मकर)', 'Capricorn (मकर)', 'Aquarius (कुंभ)', 'Aquarius (कुंभ)')),
    'Shatabhisha': NakshatraData('Shatabhisha (शतभिषा)', 'Rahu', ('Go', 'Sa', 'Si', 'Su'), ('Aquarius (कुंभ)',) * 4),
    'Purva Bhadrapada': NakshatraData('Purva Bhadrapada (पूर्व भाद्रपद)', 'Jupiter', ('Se', 'So', 'Da', 'Di'), ('Aquarius (कुंभ)', 'Aquarius (कुंभ)', 'Aquarius (कुंभ)', 'Pisces (मीन)')),
    'Uttara Bhadrapada': NakshatraData('Uttara Bhadrapada (उत्तर भाद्रपद)', 'Saturn', ('Du', 'Tha', 'Jha', 'Na'), ('Pisces (मीन)',) * 4),
    'Revati': NakshatraData('Revati (रेवती)', 'Mercury', ('De', 'Do', 'Cha', 'Chi'), ('Pisces (मीन)',) * 4)
}

# ==================== CORE ASTRONOMICAL LOGIC ====================

class NakshatraPredictor:
    """
    The Vedic prediction engine to estimate a birth time from a name and birth date.
    """
    def _get_julian_day(self, dt: datetime.datetime) -> float:
        """Calculates the Julian Day Number for a given datetime object."""
        year, month, day = dt.year, dt.month, dt.day
        hour, minute, second = dt.hour, dt.minute, dt.second
        if month <= 2:
            year -= 1
            month += 12
        A = year // 100
        B = 2 - A + A // 4
        day_fraction = (hour + minute / 60 + second / 3600) / 24.0
        jd = int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + day + day_fraction + B - 1524.5
        return jd

    def _calculate_ayanamsa(self, jd: float) -> float:
        """
        Calculates the Lahiri Ayanamsa (approximated) for a Julian day.
        The Ayanamsa is the precession of the equinoxes.
        """
        T = (jd - 2451545.0) / 36525
        # Simplified Lahiri Ayanamsa formula for approximation.
        return 23.934469 + (1.396 * T) + (0.000314 * T * T)


    def _calculate_moon_longitude(self, jd: float) -> float:
        """
        Calculates the Moon's sidereal longitude for a given Julian day.
        This uses a simplified model with major corrections.
        """
        T = (jd - 2451545.0) / 36525 # Julian centuries since J2000.0

        # Moon's mean longitude
        L0 = 218.3164477 + 481267.88123421 * T
        # Moon's mean anomaly
        M_moon = 134.9633964 + 477198.8675055 * T
        # Sun's mean anomaly
        M_sun = 357.5291092 + 35999.0502909 * T
        # Sun's mean longitude
        L_sun = 280.466492 + 36000.76983 * T
        # Moon's mean elongation from Sun
        D = L0 - L_sun

        # Apply major perturbation terms for a more accurate tropical longitude
        term1 = 6.289 * math.sin(math.radians(M_moon))         # Equation of the center
        term2 = 1.274 * math.sin(math.radians(2 * D - M_moon)) # Evection
        term3 = 0.658 * math.sin(math.radians(2 * D))          # Variation
        term4 = 0.214 * math.sin(math.radians(2 * M_moon))     # Second correction to equation of center

        tropical_longitude = L0 + term1 + term2 + term3 + term4
        ayanamsa = self._calculate_ayanamsa(jd)
        sidereal_longitude = (tropical_longitude - ayanamsa) % 360
        return sidereal_longitude

    def _find_nakshatra_from_name(self, name: str) -> Optional[Tuple[str, int, str]]:
        """Finds the best-matching Nakshatra and Pada from the start of a name."""
        if not name or not name.strip(): return None
        name_lower = name.lower().strip()
        best_match = None
        longest_match_length = 0
        for nakshatra_name, data in NAKSHATRA_DATABASE.items():
            for pada_idx, syllable in enumerate(data.syllables):
                syllable_lower = syllable.lower()
                if name_lower.startswith(syllable_lower):
                    if len(syllable_lower) > longest_match_length:
                        longest_match_length = len(syllable_lower)
                        pada_number = pada_idx + 1
                        best_match = (nakshatra_name, pada_number, syllable)
        return best_match

    def _get_longitude_range_for_pada(self, nakshatra_name: str, pada: int) -> Optional[Tuple[float, float]]:
        """Returns the longitude range (start, end) for a given Nakshatra Pada."""
        if not (1 <= pada <= 4): return None
        try:
            nak_start_lon = next(lon for name, lon in NAKSHATRA_LONGITUDES if name == nakshatra_name)
        except StopIteration:
            return None
        pada_span = NAKSHATRA_SPAN / 4  # 3.333 degrees per pada
        start_lon = nak_start_lon + (pada - 1) * pada_span
        end_lon = start_lon + pada_span
        return (start_lon, end_lon)

    def predict_time_from_name(self, name: str, birth_date: datetime.date, timezone_offset: float) -> Optional[PredictionResult]:
        """Predicts the time window based on the name and date of birth."""
        nak_details = self._find_nakshatra_from_name(name)
        if not nak_details: return None
        nakshatra_name, pada, syllable = nak_details

        lon_range = self._get_longitude_range_for_pada(nakshatra_name, pada)
        if not lon_range: return None
        start_lon, end_lon = lon_range

        start_dt_utc, end_dt_utc = None, None

        # Search in a 48-hour window to reliably catch the transit
        search_start_local = datetime.datetime.combine(birth_date, datetime.time(0, 0)) - datetime.timedelta(hours=12)

        found_in_range = False

        # Search in 2-minute intervals over 48 hours
        for i in range(1440): # 48 hours * 30 (2-min intervals)
            current_dt_local = search_start_local + datetime.timedelta(minutes=i * 2)
            current_dt_utc = current_dt_local - datetime.timedelta(hours=timezone_offset)
            jd = self._get_julian_day(current_dt_utc)
            moon_lon = self._calculate_moon_longitude(jd)

            in_range = False
            # Check if moon longitude is within the pada's range
            if start_lon < end_lon:
                if start_lon <= moon_lon < end_lon:
                    in_range = True
            else:  # Handles the crossover from 360 to 0 degrees (e.g., Revati to Ashwini)
                if moon_lon >= start_lon or moon_lon < end_lon:
                    in_range = True

            if in_range:
                if not found_in_range:
                    start_dt_utc = current_dt_utc
                    found_in_range = True
                end_dt_utc = current_dt_utc
            elif found_in_range:
                # Once the Moon moves out of the range, we can stop searching.
                break

        if not start_dt_utc or not end_dt_utc: return None

        # Convert the results back to local time for display
        start_dt_local = start_dt_utc + datetime.timedelta(hours=timezone_offset)
        end_dt_local = end_dt_utc + datetime.timedelta(hours=timezone_offset)

        # Clip the time window to only show results for the user-selected date
        start_of_day = datetime.datetime.combine(birth_date, datetime.time.min)
        end_of_day = datetime.datetime.combine(birth_date, datetime.time.max)
        
        # Ensure there is an overlap with the birth date
        if start_dt_local > end_of_day or end_dt_local < start_of_day:
            return None # No valid window found on this specific day.

        clipped_start = max(start_dt_local, start_of_day)
        clipped_end = min(end_dt_local, end_of_day)

        nakshatra_info = NAKSHATRA_DATABASE[nakshatra_name]
        return PredictionResult(
            nakshatra=nakshatra_info.name,
            pada=pada,
            rashi=nakshatra_info.rashi_mapping[pada - 1],
            syllable=syllable,
            time_start=clipped_start,
            time_end=clipped_end,
            nakshatra_lord=nakshatra_info.lord
        )

# ==================== GUI APPLICATION ====================

class ModernNakshatraGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.predictor = NakshatraPredictor()
        self.setup_window()
        self.create_widgets()

    def setup_window(self):
        self.root.title("Vedic Birth Time Estimator")
        self.root.geometry("600x750")
        self.root.minsize(500, 700)
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.colors = {
            'primary': '#4A5568', 'secondary': '#718096', 'bg': '#F7FAFC',
            'card': '#FFFFFF', 'text': '#2D3748', 'text_light': '#A0AEC0'
        }
        self.root.configure(bg=self.colors['bg'])

    def create_widgets(self):
        main_frame = tk.Frame(self.root, bg=self.colors['bg'], padx=25, pady=25)
        main_frame.pack(fill=tk.BOTH, expand=True)
        self.create_header(main_frame)
        self.create_input_section(main_frame)
        self.results_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        self.results_frame.pack(fill=tk.BOTH, expand=True, pady=(20, 0))
        self.create_footer(main_frame)

    def create_header(self, parent):
        tk.Label(parent, text="Vedic Birth Time Estimator", font=('Arial', 24, 'bold'),
                 fg=self.colors['primary'], bg=self.colors['bg']).pack()
        tk.Label(parent, text="Find a probable birth time window from a name and birth date",
                 font=('Arial', 11), fg=self.colors['secondary'], bg=self.colors['bg']).pack(pady=(0, 20))

    def create_input_section(self, parent):
        input_card = tk.Frame(parent, bg=self.colors['card'], relief=tk.SOLID, bd=1,
                              highlightbackground=self.colors['text_light'], highlightthickness=1)
        input_card.pack(fill=tk.X)
        inner_frame = tk.Frame(input_card, bg=self.colors['card'], padx=20, pady=20)
        inner_frame.pack(fill=tk.X)
        inner_frame.columnconfigure(1, weight=1)

        tk.Label(inner_frame, text="Full Name", font=('Arial', 10, 'bold'), fg=self.colors['text'], bg=self.colors['card']).grid(row=0, column=0, sticky='w', pady=5)
        self.name_entry = ttk.Entry(inner_frame, font=('Arial', 10), width=30)
        self.name_entry.grid(row=0, column=1, columnspan=2, sticky='ew', pady=5)

        tk.Label(inner_frame, text="Date of Birth (DD-MM-YYYY)", font=('Arial', 10, 'bold'), fg=self.colors['text'], bg=self.colors['card']).grid(row=1, column=0, sticky='w', pady=5)
        self.date_entry = ttk.Entry(inner_frame, font=('Arial', 10))
        self.date_entry.grid(row=1, column=1, columnspan=2, sticky='ew', pady=5)
        self.date_entry.insert(0, datetime.date.today().strftime("%d-%m-%Y")) # Default to today's date

        tk.Label(inner_frame, text="Timezone (UTC Offset)", font=('Arial', 10, 'bold'), fg=self.colors['text'], bg=self.colors['card']).grid(row=2, column=0, sticky='w', pady=5)
        self.tz_entry = ttk.Entry(inner_frame, font=('Arial', 10))
        self.tz_entry.grid(row=2, column=1, columnspan=2, sticky='ew', pady=5)
        self.tz_entry.insert(0, "5.5")  # Default for India

        predict_btn = tk.Button(inner_frame, text="Find Birth Time Window", font=('Arial', 12, 'bold'),
                                  bg=self.colors['primary'], fg='white', relief=tk.FLAT, cursor='hand2',
                                  command=self.perform_prediction, padx=15, pady=8)
        predict_btn.grid(row=3, column=0, columnspan=3, pady=(20, 10))

    def create_footer(self, parent):
        footer_text = "Disclaimer: This tool provides an estimation based on phonetic sounds and simplified astronomical data. For entertainment purposes only."
        tk.Label(parent, text=footer_text, font=('Arial', 8), fg=self.colors['text_light'], bg=self.colors['bg'], wraplength=450).pack(side=tk.BOTTOM, pady=(10, 0))

    def perform_prediction(self):
        name = self.name_entry.get().strip()
        date_str = self.date_entry.get().strip()
        tz_str = self.tz_entry.get().strip()

        if not name or not date_str or not tz_str:
            messagebox.showerror("Input Error", "Please fill in all fields: Name, Date of Birth, and Timezone.")
            return

        try:
            birth_date = datetime.datetime.strptime(date_str, "%d-%m-%Y").date()
            tz_offset = float(tz_str)
        except ValueError:
            messagebox.showerror("Format Error", "Invalid date format (use DD-MM-YYYY) or timezone format (use a number like 5.5).")
            return

        result = self.predictor.predict_time_from_name(name, birth_date, tz_offset)

        if not result:
            messagebox.showwarning("Not Found", f"No time window could be found for a name starting with '{name}' on {date_str}. This may happen if the Moon was not in the required Nakshatra on that day, or if the name does not follow traditional phonetic syllables.")
            return

        self.display_results(result)

    def display_results(self, result: PredictionResult):
        for widget in self.results_frame.winfo_children():
            widget.destroy()

        tk.Label(self.results_frame, text="Astrological Profile & Birth Window", font=('Arial', 16, 'bold'),
                 fg=self.colors['primary'], bg=self.colors['bg']).pack(pady=(0, 15))

        results_container = tk.Frame(self.results_frame, bg=self.colors['card'], bd=1, relief=tk.SOLID,
                                     highlightbackground=self.colors['text_light'], highlightthickness=1)
        results_container.pack(fill=tk.X, expand=True)

        start_str = result.time_start.strftime('%d-%b %I:%M %p')
        end_str = result.time_end.strftime('%I:%M %p')

        time_str = f"{start_str} to {end_str}"

        details = [
            ("Probable Birth Window", time_str),
            ("Estimated Nakshatra", f"{result.nakshatra} (Pada {result.pada})"),
            ("Nakshatra Lord", result.nakshatra_lord),
            ("Estimated Rashi (Moon Sign)", result.rashi),
            ("Based on Syllable", f"'{result.syllable}'")
        ]

        for i, (label, value) in enumerate(details):
            lbl = tk.Label(results_container, text=label, font=('Arial', 10, 'bold'),
                           bg=self.colors['card'], fg=self.colors['secondary'], anchor='w')
            lbl.grid(row=i, column=0, sticky='ew', padx=15, pady=8)
            val = tk.Label(results_container, text=value, font=('Arial', 10),
                           bg=self.colors['card'], fg=self.colors['text'], anchor='e')
            val.grid(row=i, column=1, sticky='ew', padx=15, pady=8)
            if label == "Probable Birth Window":
                lbl.config(font=('Arial', 11, 'bold'), fg=self.colors['primary'])
                val.config(font=('Arial', 11, 'bold'), fg=self.colors['primary'])

        results_container.columnconfigure(0, weight=1)
        results_container.columnconfigure(1, weight=1)

# ==================== MAIN EXECUTION ====================

def main():
    """The main entry point for the application."""
    try:
        root = tk.Tk()
        app = ModernNakshatraGUI(root)
        root.mainloop()
    except Exception as e:
        print(f"An error occurred while starting the application: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
