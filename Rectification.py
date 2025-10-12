import math
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import datetime
import swisseph as swe
from collections import defaultdict

# --- Global Data Definitions ---

SIGNS = {
    1: "Aries", 2: "Taurus", 3: "Gemini", 4: "Cancer", 5: "Leo", 6: "Virgo",
    7: "Libra", 8: "Scorpio", 9: "Sagittarius", 10: "Capricorn", 11: "Aquarius", 12: "Pisces"
}

SIGN_NATURE = {
    1: "Odd", 2: "Even", 3: "Odd", 4: "Even", 5: "Odd", 6: "Even",
    7: "Odd", 8: "Even", 9: "Odd", 10: "Even", 11: "Odd", 12: "Even"
}

SIGN_MODALITY = {
    1: "Movable", 4: "Movable", 7: "Movable", 10: "Movable",
    2: "Fixed", 5: "Fixed", 8: "Fixed", 11: "Fixed",
    3: "Dual", 6: "Dual", 9: "Dual", 12: "Dual"
}

PLANET_NAMES = {
    swe.SUN: "Sun", swe.MOON: "Moon", swe.MARS: "Mars", swe.MERCURY: "Mercury",
    swe.JUPITER: "Jupiter", swe.VENUS: "Venus", swe.SATURN: "Saturn",
    swe.MEAN_NODE: "Rahu"
}

# --- Core Calculation Engines ---

class AstronomicalCalculator:
    """
    Handles all core astronomical calculations using the Swiss Ephemeris library with
    proper UTC conversion and Lahiri Ayanamsa for precise Sidereal positions.
    """
    def __init__(self, ayanamsa='LAHIRI'):
        swe.set_ephe_path(None)
        self.ayanamsa_code = getattr(swe, f'SIDM_{ayanamsa}')
        swe.set_sid_mode(self.ayanamsa_code)

    def get_julian_day(self, year, month, day, hour, minute, second, timezone_offset):
        """Converts local time (including seconds) to Julian Day UTC."""
        birth_dt_local = datetime.datetime(year, month, day, hour, minute, second)
        birth_dt_utc = birth_dt_local - datetime.timedelta(hours=timezone_offset)
        julian_day_utc = swe.utc_to_jd(
            birth_dt_utc.year, birth_dt_utc.month, birth_dt_utc.day,
            birth_dt_utc.hour, birth_dt_utc.minute, birth_dt_utc.second, 1
        )[1]
        return julian_day_utc

    def calculate_d1(self, julian_day_utc, lat, lon):
        """
        Calculates the D1 natal chart. Returns detailed data for calculations
        and raw data for simple display.
        """
        chart_data = {}
        raw_chart_data_for_display = []

        try:
            # Calculate Ascendant
            _, ascmc = swe.houses(julian_day_utc, lat, lon, b'P')
            asc_longitude = ascmc[0]
            sign, dms, sign_num, lon_dec = self._format_longitude(asc_longitude)
            chart_data["Ascendant"] = {"sign_num": sign_num, "lon_decimal": lon_dec, "sign_name": sign, "dms": dms}
            raw_chart_data_for_display.append(("Ascendant", sign, dms))

            # Calculate Planets
            for planet_id, name in PLANET_NAMES.items():
                planet_pos = swe.calc_ut(julian_day_utc, planet_id, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)[0]
                planet_longitude = planet_pos[0]
                sign, dms, sign_num, lon_dec = self._format_longitude(planet_longitude)
                chart_data[name] = {"sign_num": sign_num, "lon_decimal": lon_dec, "sign_name": sign, "dms": dms}
                raw_chart_data_for_display.append((name, sign, dms))

                # Calculate Ketu from Rahu
                if name == "Rahu":
                    ketu_longitude = (planet_longitude + 180) % 360
                    sign, dms, sign_num, lon_dec = self._format_longitude(ketu_longitude)
                    chart_data["Ketu"] = {"sign_num": sign_num, "lon_decimal": lon_dec, "sign_name": sign, "dms": dms}
                    raw_chart_data_for_display.append(("Ketu", sign, dms))

        except (swe.Error, TypeError, IndexError, ValueError) as e:
            messagebox.showerror("Calculation Error", f"An error occurred in Swiss Ephemeris: {e}")
            return None, None

        return chart_data, raw_chart_data_for_display

    def get_dasha_at_event(self, birth_jd_utc, event_jd_utc):
        """Calculates Vimshottari Dasha lords at the time of an event."""
        moon_pos = swe.calc_ut(birth_jd_utc, swe.MOON, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)[0][0]

        dasha_lords = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
        dasha_lengths = [7, 20, 6, 10, 7, 18, 16, 19, 17] # In years
        nakshatra_span = 360 / 27

        nakshatra_num = int(moon_pos / nakshatra_span)
        nakshatra_lord_index = nakshatra_num % 9

        moon_in_nakshatra = moon_pos % nakshatra_span
        elapsed_dasha_days = (moon_in_nakshatra / nakshatra_span) * dasha_lengths[nakshatra_lord_index] * 365.25
        dasha_start_jd = birth_jd_utc - elapsed_dasha_days

        for i in range(10): # Check next 10 Mahadashas
            md_lord_index = (nakshatra_lord_index + i) % 9
            md_lord = dasha_lords[md_lord_index]
            md_start_jd = dasha_start_jd + sum(dasha_lengths[(nakshatra_lord_index + j) % 9] for j in range(i)) * 365.25
            md_length_days = dasha_lengths[md_lord_index] * 365.25
            md_end_jd = md_start_jd + md_length_days

            if md_start_jd <= event_jd_utc < md_end_jd:
                ad_start_jd = md_start_jd
                ad_lord_index_current = md_lord_index
                for _ in range(9):
                    ad_lord = dasha_lords[ad_lord_index_current]
                    ad_length_days = (dasha_lengths[ad_lord_index_current] / 120) * md_length_days
                    ad_end_jd = ad_start_jd + ad_length_days
                    if ad_start_jd <= event_jd_utc < ad_end_jd:
                        return md_lord, ad_lord
                    ad_start_jd = ad_end_jd
                    ad_lord_index_current = (ad_lord_index_current + 1) % 9
        return None, None

    def _format_longitude(self, lon_decimal):
        """Converts decimal longitude to sign, DMS string, sign number, and longitude within sign."""
        sign_num = int(lon_decimal / 30) + 1
        lon_in_sign = lon_decimal % 30
        sign_name = SIGNS.get(sign_num, "Error")
        deg = int(lon_in_sign)
        min_dec = (lon_in_sign - deg) * 60
        minute = int(min_dec)
        sec = round((min_dec - minute) * 60, 2)
        dms_str = f"{deg:02d}° {minute:02d}' {sec:05.2f}\""
        return sign_name, dms_str, sign_num, lon_in_sign

class VargaCalculator:
    """
    Calculates various divisional charts (Vargas) using standard Parashari methods.
    The D9 calculation has been fully corrected.
    """
    def __init__(self):
        self.D24_DEITIES = ("Skanda","Parashudhara","Anala","Vishwakarma","Bhaga","Mitra","Maya","Antaka","Vrishadhvaja","Govinda","Jayanta","Vasuki")
        self.D60_DEITIES = ("Ghora","Rakshasa","Deva","Kubera","Yaksha","Kinnara","Bhrashta","Kulaghna","Garala","Vahni","Maya","Puriihaka","Apampathi","Marutwana","Kaala","Sarpa","Amrita","Indu","Mridu","Komala","Heramba","Brahma","Vishnu","Maheshwara","Deva","Ardra","Kalinasa","Kshiteesa","Kamalakara","Gulika","Mrityu","Kaala","Davagni","Ghora","Yama","Kantaka","Sudha","Amrita","Poorna","VishaDagdha","Kulanasa","Vamshakshya","Utpata","Kaala","Saumya","Komala","Seetala","Karaladamshtra","Chandramukhi","Praveena","Kaalpavaka","Dandayudha","Nirmala","Saumya","Kroora","Atisheetala","Amrita","Payodhi","Bhramana","Chandrarekha")

    def calculate(self, varga_num, d1_lon_in_sign, d1_sign_num):
        """Main dispatcher for calculating the requested varga."""
        varga_map = {
            2: self._calculate_d2, 3: self._calculate_d3, 4: self._calculate_d4,
            7: self._calculate_d7, 9: self._calculate_d9, 10: self._calculate_d10,
            12: self._calculate_d12, 16: self._calculate_d16, 20: self._calculate_d20,
            24: self._calculate_d24, 60: self._calculate_d60
        }
        if varga_num in varga_map:
            return varga_map[varga_num](d1_lon_in_sign, d1_sign_num)
        return None, None, "N/A"

    def _calculate_d2(self, lon, sign_num): # Hora
        amsa_index = math.floor(lon / 15)
        varga_lon = (lon % 15) * 2
        sign_nat = SIGN_NATURE[sign_num]
        sign, details = (5, "Sun's Hora") if (sign_nat == "Odd" and amsa_index == 0) or (sign_nat == "Even" and amsa_index == 1) else (4, "Moon's Hora")
        return sign, varga_lon, details

    def _calculate_d3(self, lon, sign_num): # Parashari Drekkana
        amsa_index = math.floor(lon / 10)
        varga_lon = (lon % 10) * 3
        offset = [0, 4, 8][amsa_index]
        sign = (sign_num + offset - 1) % 12 + 1
        return sign, varga_lon, ""

    def _calculate_d4(self, lon, sign_num): # Chaturthamsa
        amsa_index = math.floor(lon / 7.5)
        varga_lon = (lon % 7.5) * 4
        sign = ((sign_num - 1) + (amsa_index * 3)) % 12 + 1
        return sign, varga_lon, ""

    def _calculate_d7(self, lon, sign_num): # Saptamsa
        amsa_index = math.floor(lon / (30 / 7))
        varga_lon = (lon % (30 / 7)) * 7
        start_sign = sign_num if SIGN_NATURE[sign_num] == "Odd" else (sign_num + 6)
        sign = (start_sign + amsa_index - 1) % 12 + 1
        return sign, varga_lon, ""

    def _calculate_d9(self, lon, sign_num): # *** CORRECTED Parashari Navamsa ***
        """
        Calculates the Navamsa sign and longitude.
        - Movable signs (1,4,7,10) count from the sign itself.
        - Fixed signs (2,5,8,11) count from the 9th sign from it.
        - Dual signs (3,6,9,12) count from the 5th sign from it.
        """
        amsa_size = 30 / 9
        amsa_index = math.floor(lon / amsa_size)
        varga_lon = (lon % amsa_size) * 9
        
        modality = SIGN_MODALITY[sign_num]
        start_sign = 0
        
        if modality == "Movable":
            start_sign = sign_num
        elif modality == "Fixed":
            start_sign = (sign_num + 8 - 1) % 12 + 1 # 9th sign from the current one
        elif modality == "Dual":
            start_sign = (sign_num + 4 - 1) % 12 + 1 # 5th sign from the current one

        final_sign = (start_sign + amsa_index - 1) % 12 + 1
        return final_sign, varga_lon, ""

    def _calculate_d10(self, lon, sign_num): # Dasamsa
        amsa_index = math.floor(lon / 3)
        varga_lon = (lon % 3) * 10
        start_sign = sign_num if SIGN_NATURE[sign_num] == "Odd" else (sign_num + 8)
        sign = (start_sign + amsa_index - 1) % 12 + 1
        return sign, varga_lon, ""

    def _calculate_d12(self, lon, sign_num): # Dwadasamsa
        amsa_index = math.floor(lon / 2.5)
        varga_lon = (lon % 2.5) * 12
        sign = (sign_num + amsa_index - 1) % 12 + 1
        return sign, varga_lon, ""

    def _calculate_d16(self, lon, sign_num): # Shodasamsa
        amsa_index = math.floor(lon / 1.875)
        varga_lon = (lon % 1.875) * 16
        modality = SIGN_MODALITY[sign_num]
        if modality == "Movable": start_sign = 1
        elif modality == "Fixed": start_sign = 5
        else: start_sign = 9
        sign = (start_sign + amsa_index - 1) % 12 + 1
        return sign, varga_lon, ""

    def _calculate_d20(self, lon, sign_num): # Vimsamsa
        amsa_index = math.floor(lon / 1.5)
        varga_lon = (lon % 1.5) * 20
        modality = SIGN_MODALITY[sign_num]
        if modality == "Movable": start_sign = 1
        elif modality == "Fixed": start_sign = 9
        else: start_sign = 5
        sign = (start_sign + amsa_index - 1) % 12 + 1
        return sign, varga_lon, ""

    def _calculate_d24(self, lon, sign_num): # Siddhamsa
        amsa_index = math.floor(lon / 1.25)
        varga_lon = (lon % 1.25) * 24
        deity_idx = amsa_index % 12
        if SIGN_NATURE[sign_num] == "Odd":
            sign = (5 + amsa_index - 1) % 12 + 1
            details = self.D24_DEITIES[deity_idx]
        else: # Even
            sign = (4 - amsa_index - 1 + 12 * 2) % 12 + 1
            details = self.D24_DEITIES[11 - deity_idx]
        return sign, varga_lon, details

    def _calculate_d60(self, lon, sign_num): # Shashtyamsa
        lon_from_aries = lon + (sign_num - 1) * 30
        amsa_index_raw = math.floor(lon_from_aries * 2)
        varga_sign = (amsa_index_raw // 60) % 12 + 1 # Corrected sign calculation
        amsa_index_in_sign = amsa_index_raw % 60
        varga_lon = (lon_from_aries * 2 % 1) * 30
        details = self.D60_DEITIES[amsa_index_in_sign]
        return varga_sign, varga_lon, details

# --- GUI and Helper Functions ---

def decimal_to_dms(decimal_degrees):
    """Converts a decimal degree value into a formatted DMS string."""
    if not isinstance(decimal_degrees, (int, float)): return "N/A"
    if decimal_degrees >= 30.0: decimal_degrees = 29.99999
    degrees = int(decimal_degrees)
    minutes_float = (decimal_degrees - degrees) * 60
    minutes = int(minutes_float)
    seconds = round((minutes_float - minutes) * 60, 2)
    return f"{degrees:02d}° {minutes:02d}' {seconds:05.2f}\""

class AstroApp(tk.Tk):
    """The main application window."""
    def __init__(self):
        super().__init__()
        self.d1_calculator = AstronomicalCalculator()
        self.varga_calculator = VargaCalculator()
        self.title("AstroVighati Pro - Unified Vedic Calculator")
        self.geometry("1200x800")
        self.d1_chart_data = None
        
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(pady=10, padx=10, fill="both", expand=True)
        self.d1_tab = ttk.Frame(self.notebook)
        self.varga_tab = ttk.Frame(self.notebook)
        self.btr_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.d1_tab, text='Natal Chart (D1) Calculator')
        self.notebook.add(self.varga_tab, text='Divisional Chart (Varga) Calculator')
        self.notebook.add(self.btr_tab, text='Birth Time Rectification')
        
        self.create_d1_tab_widgets()
        self.varga_app_handler = VargaApp(self.varga_tab, self.varga_calculator, self)
        self.btr_app_handler = BirthTimeRectificationApp(self.btr_tab, self)

    def create_d1_tab_widgets(self):
        """Creates the widgets for the D1 calculation tab."""
        frame = ttk.LabelFrame(self.d1_tab, text="Birth Details", padding=10)
        frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(frame, text="Date (DD/MM/YYYY):").grid(row=0, column=0, sticky="w", padx=5)
        self.day_var = tk.StringVar(value="14"); self.month_var = tk.StringVar(value="11"); self.year_var = tk.StringVar(value="2003")
        ttk.Entry(frame, textvariable=self.day_var, width=4).grid(row=0, column=1)
        ttk.Entry(frame, textvariable=self.month_var, width=4).grid(row=0, column=2)
        ttk.Entry(frame, textvariable=self.year_var, width=6).grid(row=0, column=3)
        
        ttk.Label(frame, text="Time (HH:MM:SS 24hr):").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.hour_var = tk.StringVar(value="19"); self.minute_var = tk.StringVar(value="41"); self.second_var = tk.StringVar(value="46")
        ttk.Entry(frame, textvariable=self.hour_var, width=4).grid(row=1, column=1)
        ttk.Entry(frame, textvariable=self.minute_var, width=4).grid(row=1, column=2)
        ttk.Entry(frame, textvariable=self.second_var, width=4).grid(row=1, column=3)

        ttk.Label(frame, text="Latitude / Longitude:").grid(row=2, column=0, sticky="w", padx=5)
        self.lat_var = tk.StringVar(value="28.8344"); self.lon_var = tk.StringVar(value="77.5699")
        ttk.Entry(frame, textvariable=self.lat_var, width=10).grid(row=2, column=1, columnspan=2)
        ttk.Entry(frame, textvariable=self.lon_var, width=10).grid(row=2, column=3, columnspan=2)
        
        ttk.Label(frame, text="Timezone Offset (UTC):").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        self.tz_var = tk.StringVar(value="5.5")
        ttk.Entry(frame, textvariable=self.tz_var, width=4).grid(row=3, column=1)

        ttk.Button(frame, text="Calculate D1 Chart", command=self.calculate_d1_chart).grid(row=4, column=0, columnspan=4, pady=10)

        output_frame = ttk.LabelFrame(self.d1_tab, text="D1 - Lagna Chart", padding=10)
        output_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.d1_tree = ttk.Treeview(output_frame, columns=("planet", "sign", "dms"), show="headings")
        self.d1_tree.heading("planet", text="Planet"); self.d1_tree.heading("sign", text="Sign"); self.d1_tree.heading("dms", text="Longitude (DMS)")
        self.d1_tree.pack(fill="both", expand=True)

    def calculate_d1_chart(self):
        """Callback to handle the D1 chart calculation and update the UI."""
        try:
            year = int(self.year_var.get()); month = int(self.month_var.get()); day = int(self.day_var.get())
            hour = int(self.hour_var.get()); minute = int(self.minute_var.get()); second = int(self.second_var.get())
            lat = float(self.lat_var.get()); lon = float(self.lon_var.get()); tz = float(self.tz_var.get())
        except ValueError:
            messagebox.showerror("Invalid Input", "Please ensure all fields contain valid numbers.")
            return

        self.d1_tree.delete(*self.d1_tree.get_children())
        julian_day = self.d1_calculator.get_julian_day(year, month, day, hour, minute, second, tz)
        self.d1_chart_data, raw_chart_data = self.d1_calculator.calculate_d1(julian_day, lat, lon)

        if raw_chart_data:
            for row in raw_chart_data:
                self.d1_tree.insert("", "end", values=row)
            messagebox.showinfo("Success", "D1 Chart calculated. You can now use this data in other tabs.")
            self.btr_app_handler.load_d1_details() # Update BTR tab with new data

class VargaApp:
    """Handles the improved UI and logic for the Varga Calculator tab."""
    def __init__(self, parent_tab, calculator, main_app):
        self.parent = parent_tab
        self.calculator = calculator
        self.main_app = main_app
        self.varga_map = {
            "D2 - Hora": 2, "D3 - Drekkana": 3, "D4 - Chaturthamsa": 4, "D7 - Saptamsa": 7,
            "D9 - Navamsa": 9, "D10 - Dasamsa": 10, "D12 - Dwadasamsa": 12, "D16 - Shodasamsa": 16,
            "D20 - Vimsamsa": 20, "D24 - Siddhamsa": 24, "D60 - Shashtyamsa": 60
        }
        self.create_widgets()

    def create_widgets(self):
        """Creates all widgets for the Varga tab."""
        control_frame = ttk.LabelFrame(self.parent, text="Varga Calculation", padding=(10, 5))
        control_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(control_frame, text="Chart:").grid(row=0, column=0, sticky="w", padx=5)
        self.varga_var = tk.StringVar()
        self.varga_combo = ttk.Combobox(control_frame, textvariable=self.varga_var, values=list(self.varga_map.keys()), state="readonly", width=20)
        self.varga_combo.grid(row=0, column=1, padx=5); self.varga_combo.set("D9 - Navamsa")

        ttk.Button(control_frame, text="Calculate Full Varga Chart from D1", command=self.calculate_full_varga).grid(row=0, column=2, padx=20)

        self.output_frame = ttk.LabelFrame(self.parent, text="Divisional Chart Results", padding=(10, 5))
        self.output_frame.pack(fill="both", expand=True, padx=10, pady=10)
        columns = ("planet", "d1_pos", "varga_sign", "varga_lon", "details")
        self.tree = ttk.Treeview(self.output_frame, columns=columns, show="headings")
        self.tree.heading("planet", text="Planet"); self.tree.heading("d1_pos", text="D1 Position")
        self.tree.heading("varga_sign", text="Varga Sign"); self.tree.heading("varga_lon", text="Varga Longitude")
        self.tree.heading("details", text="Details")
        self.tree.column("planet", width=100); self.tree.column("d1_pos", width=180); self.tree.column("varga_sign", width=100)
        self.tree.column("varga_lon", width=150); self.tree.column("details", width=150)
        self.tree.pack(fill="both", expand=True)

    def calculate_full_varga(self):
        """Calculates the selected varga chart for all planets from the D1 data."""
        self.tree.delete(*self.tree.get_children())
        if not self.main_app.d1_chart_data:
            messagebox.showerror("No Data", "Please calculate a D1 chart first in the 'Natal Chart' tab.")
            return

        try:
            varga_key = self.varga_var.get(); varga_num = self.varga_map[varga_key]
            self.output_frame.config(text=f"{varga_key} Results")
            planet_order = ["Ascendant", "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]

            for planet_name in planet_order:
                if planet_name in self.main_app.d1_chart_data:
                    planet_data = self.main_app.d1_chart_data[planet_name]
                    sign_num, lon_decimal = planet_data["sign_num"], planet_data["lon_decimal"]
                    d1_pos_str = f"{planet_data['sign_name']} {planet_data['dms']}"
                    
                    varga_sign_num, varga_lon_dec, details = self.calculator.calculate(varga_num, lon_decimal, sign_num)

                    if varga_sign_num is not None:
                        varga_sign_name = SIGNS[varga_sign_num]
                        varga_lon_dms = decimal_to_dms(varga_lon_dec)
                        self.tree.insert("", "end", values=(planet_name, d1_pos_str, varga_sign_name, varga_lon_dms, details))
        except (ValueError, KeyError, tk.TclError) as e:
            messagebox.showerror("Calculation Error", f"An error occurred: {e}")

class BirthTimeRectificationApp:
    def __init__(self, parent_tab, main_app):
        self.parent = parent_tab
        self.main_app = main_app
        self.events = []
        self.engine = RectificationEngine(main_app.d1_calculator, main_app.varga_calculator)
        self.create_widgets()

    def create_widgets(self):
        input_frame = ttk.LabelFrame(self.parent, text="Base Data & Time Range", padding=10)
        input_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(input_frame, text="Date (DD/MM/YYYY):").grid(row=0, column=0, sticky="w", padx=5); self.day_var = tk.StringVar(); self.month_var = tk.StringVar(); self.year_var = tk.StringVar(); ttk.Entry(input_frame, textvariable=self.day_var, width=4).grid(row=0, column=1); ttk.Entry(input_frame, textvariable=self.month_var, width=4).grid(row=0, column=2); ttk.Entry(input_frame, textvariable=self.year_var, width=6).grid(row=0, column=3)
        ttk.Label(input_frame, text="Start Time (HH:MM):").grid(row=1, column=0, sticky="w", padx=5, pady=5); self.start_hour_var = tk.StringVar(); self.start_min_var = tk.StringVar(); ttk.Entry(input_frame, textvariable=self.start_hour_var, width=4).grid(row=1, column=1); ttk.Entry(input_frame, textvariable=self.start_min_var, width=4).grid(row=1, column=2)
        ttk.Label(input_frame, text="End Time (HH:MM):").grid(row=1, column=3, sticky="w", padx=5, pady=5); self.end_hour_var = tk.StringVar(); self.end_min_var = tk.StringVar(); ttk.Entry(input_frame, textvariable=self.end_hour_var, width=4).grid(row=1, column=4); ttk.Entry(input_frame, textvariable=self.end_min_var, width=4).grid(row=1, column=5)
        ttk.Label(input_frame, text="Location & TZ:").grid(row=2, column=0, sticky="w", padx=5); self.lat_var = tk.StringVar(); self.lon_var = tk.StringVar(); self.tz_var = tk.StringVar(); ttk.Entry(input_frame, textvariable=self.lat_var, width=10).grid(row=2, column=1, columnspan=2); ttk.Entry(input_frame, textvariable=self.lon_var, width=10).grid(row=2, column=3, columnspan=2); ttk.Entry(input_frame, textvariable=self.tz_var, width=4).grid(row=2, column=5)
        
        events_frame = ttk.LabelFrame(self.parent, text="Major Life Events", padding=10)
        events_frame.pack(fill="x", padx=10, pady=5)
        self.events_tree = ttk.Treeview(events_frame, columns=("type", "date"), show="headings", height=5)
        self.events_tree.heading("type", text="Event Type"); self.events_tree.heading("date", text="Date (DD/MM/YYYY)")
        self.events_tree.pack(side="left", fill="both", expand=True)
        btn_frame = ttk.Frame(events_frame); btn_frame.pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Add Event", command=self.add_event).pack(pady=2)
        ttk.Button(btn_frame, text="Remove Selected", command=self.remove_event).pack(pady=2)

        ttk.Button(self.parent, text="Rectify Birth Time", command=self.run_rectification).pack(pady=10)
        
        output_frame = ttk.LabelFrame(self.parent, text="Rectification Results (Most Likely Times)", padding=10)
        output_frame.pack(fill="both", expand=True, padx=10, pady=5)
        self.results_tree = ttk.Treeview(output_frame, columns=("time", "score", "d9", "d10", "d24", "d60"), show="headings")
        self.results_tree.heading("time", text="Candidate Time"); self.results_tree.heading("score", text="Score"); self.results_tree.heading("d9", text="D9 Lagna"); self.results_tree.heading("d10", text="D10 Lagna"); self.results_tree.heading("d24", text="D24 Lagna"); self.results_tree.heading("d60", text="D60 Deity")
        self.results_tree.column("score", width=60, anchor="center"); self.results_tree.column("time", width=120, anchor="center")
        self.results_tree.pack(fill="both", expand=True)

    def load_d1_details(self):
        """Loads data from the D1 tab to pre-fill the BTR fields."""
        self.day_var.set(self.main_app.day_var.get()); self.month_var.set(self.main_app.month_var.get()); self.year_var.set(self.main_app.year_var.get())
        self.lat_var.set(self.main_app.lat_var.get()); self.lon_var.set(self.main_app.lon_var.get()); self.tz_var.set(self.main_app.tz_var.get())
        try:
            # Set a default 30-minute range around the entered time
            base_dt = datetime.datetime(2000, 1, 1, int(self.main_app.hour_var.get()), int(self.main_app.minute_var.get()))
            start_dt = base_dt - datetime.timedelta(minutes=15)
            end_dt = base_dt + datetime.timedelta(minutes=15)
            self.start_hour_var.set(start_dt.strftime('%H')); self.start_min_var.set(start_dt.strftime('%M'))
            self.end_hour_var.set(end_dt.strftime('%H')); self.end_min_var.set(end_dt.strftime('%M'))
        except ValueError:
            self.start_hour_var.set(self.main_app.hour_var.get()); self.start_min_var.set(self.main_app.minute_var.get())

    def add_event(self):
        dialog = AddEventDialog(self.parent)
        if dialog.result:
            event_type, event_date = dialog.result
            self.events.append({"type": event_type, "date": event_date})
            self.events_tree.insert("", "end", values=(event_type, event_date.strftime("%d/%m/%Y")))

    def remove_event(self):
        selected_item = self.events_tree.selection()
        if not selected_item: return
        index = self.events_tree.index(selected_item[0])
        del self.events[index]
        self.events_tree.delete(selected_item[0])

    def run_rectification(self):
        self.results_tree.delete(*self.results_tree.get_children())
        try:
            year, month, day = int(self.year_var.get()), int(self.month_var.get()), int(self.day_var.get())
            lat, lon, tz = float(self.lat_var.get()), float(self.lon_var.get()), float(self.tz_var.get())
            start_h, start_m = int(self.start_hour_var.get()), int(self.start_min_var.get())
            end_h, end_m = int(self.end_hour_var.get()), int(self.end_min_var.get())
            if not self.events:
                messagebox.showerror("Error", "Please add at least one life event.")
                return
            start_time = datetime.datetime(year, month, day, start_h, start_m)
            end_time = datetime.datetime(year, month, day, end_h, end_m)
            results = self.engine.rectify_birth_time(start_time, end_time, lat, lon, tz, self.events)
            if not results:
                messagebox.showinfo("No Results", "No probable times found. Try expanding the time range or checking event dates.")
                return
            for res in results[:30]: # Display top 30 results
                time_str = res['time'].strftime('%H:%M:%S')
                self.results_tree.insert("", "end", values=(time_str, res['score'], res['d9_lagna'], res['d10_lagna'], res['d24_lagna'], res['d60_lagna_deity']))
        except (ValueError, KeyError) as e:
            messagebox.showerror("Input Error", f"Please check your inputs. Error: {e}")

class AddEventDialog(simpledialog.Dialog):
    def body(self, master):
        self.title("Add Life Event")
        ttk.Label(master, text="Event Type:").grid(row=0, column=0, sticky="w")
        self.event_type_var = tk.StringVar()
        event_types = ["Marriage", "Career Start", "Education Milestone", "Childbirth"]
        self.event_combo = ttk.Combobox(master, textvariable=self.event_type_var, values=event_types, state="readonly")
        self.event_combo.grid(row=0, column=1, columnspan=3); self.event_combo.set("Marriage")
        ttk.Label(master, text="Date (DD/MM/YYYY):").grid(row=1, column=0, sticky="w", pady=5)
        self.day_var = tk.StringVar(); self.month_var = tk.StringVar(); self.year_var = tk.StringVar()
        ttk.Entry(master, textvariable=self.day_var, width=4).grid(row=1, column=1)
        ttk.Entry(master, textvariable=self.month_var, width=4).grid(row=1, column=2)
        ttk.Entry(master, textvariable=self.year_var, width=6).grid(row=1, column=3)
        return self.event_combo

    def apply(self):
        try:
            day = int(self.day_var.get()); month = int(self.month_var.get()); year = int(self.year_var.get())
            event_date = datetime.date(year, month, day)
            self.result = (self.event_type_var.get(), event_date)
        except (ValueError, TypeError):
            messagebox.showerror("Invalid Date", "Please enter a valid date.")
            self.result = None

class RectificationEngine:
    """A sophisticated engine for birth time rectification using vargas and dasha systems."""
    def __init__(self, d1_calc, varga_calc):
        self.d1_calc = d1_calc
        self.varga_calc = varga_calc
        self.sign_lords = {1: "Mars", 2: "Venus", 3: "Mercury", 4: "Moon", 5: "Sun", 6: "Mercury",
                           7: "Venus", 8: "Mars", 9: "Jupiter", 10: "Saturn", 11: "Saturn", 12: "Jupiter"}

    def rectify_birth_time(self, start_time, end_time, lat, lon, tz, events):
        results = []
        current_time = start_time
        time_step = datetime.timedelta(seconds=10) # Iterate in 10-second intervals

        while current_time <= end_time:
            total_score = 0
            birth_jd = self.d1_calc.get_julian_day(current_time.year, current_time.month, current_time.day,
                                                  current_time.hour, current_time.minute, current_time.second, tz)
            d1_data, _ = self.d1_calc.calculate_d1(birth_jd, lat, lon)

            if not d1_data:
                current_time += time_step
                continue

            varga_charts = self._calculate_all_vargas(d1_data)
            
            # Kunda Principle: A strong indicator of correct birth time
            if self._check_kunda_principle(d1_data):
                total_score += 15

            for event in events:
                event_date = event['date']
                event_jd = self.d1_calc.get_julian_day(event_date.year, event_date.month, event_date.day, 12, 0, 0, tz)
                md_lord, ad_lord = self.d1_calc.get_dasha_at_event(birth_jd, event_jd)

                if md_lord and ad_lord:
                    total_score += self._score_event(event['type'], md_lord, ad_lord, varga_charts)

            if total_score > 0:
                results.append({
                    'time': current_time,
                    'score': total_score,
                    'd9_lagna': varga_charts[9].get('Ascendant', {}).get('sign_name', 'N/A'),
                    'd10_lagna': varga_charts[10].get('Ascendant', {}).get('sign_name', 'N/A'),
                    'd24_lagna': varga_charts[24].get('Ascendant', {}).get('sign_name', 'N/A'),
                    'd60_lagna_deity': varga_charts[60].get('Ascendant', {}).get('details', 'N/A'),
                })

            current_time += time_step

        return sorted(results, key=lambda x: x['score'], reverse=True)

    def _calculate_all_vargas(self, d1_data):
        varga_charts = defaultdict(dict)
        varga_nums = [7, 9, 10, 24, 60]

        for v_num in varga_nums:
            for planet_name, data in d1_data.items():
                sign_num, lon_dec = data['sign_num'], data['lon_decimal']
                v_sign, v_lon, details = self.varga_calc.calculate(v_num, lon_dec, sign_num)
                if v_sign is not None:
                    varga_charts[v_num][planet_name] = {'sign_num': v_sign, 'sign_name': SIGNS[v_sign], 'lon_decimal': v_lon, 'details': details}
        return varga_charts

    def _check_kunda_principle(self, d1_data):
        """Checks if Ascendant's Navamsa is trinal or conjunct to Moon's Navamsa."""
        if "Moon" not in d1_data or "Ascendant" not in d1_data: return False
        
        moon_d9_sign, _, _ = self.varga_calc.calculate(9, d1_data['Moon']['lon_decimal'], d1_data['Moon']['sign_num'])
        asc_d9_sign, _, _ = self.varga_calc.calculate(9, d1_data['Ascendant']['lon_decimal'], d1_data['Ascendant']['sign_num'])

        if moon_d9_sign is None or asc_d9_sign is None: return False

        trines = [moon_d9_sign, (moon_d9_sign + 4 - 1) % 12 + 1, (moon_d9_sign + 8 - 1) % 12 + 1]
        return asc_d9_sign in trines

    def _score_event(self, event_type, md_lord, ad_lord, varga_charts):
        score = 0
        event_map = {
            "Marriage": {"varga": 9, "houses": [1, 7], "karakas": ["Venus", "Jupiter"]},
            "Career Start": {"varga": 10, "houses": [1, 10], "karakas": ["Sun", "Saturn", "Mercury"]},
            "Education Milestone": {"varga": 24, "houses": [1, 4, 5, 9], "karakas": ["Mercury", "Jupiter"]},
            "Childbirth": {"varga": 7, "houses": [1, 5, 9], "karakas": ["Jupiter"]}
        }
        
        config = event_map.get(event_type)
        if not config or config['varga'] not in varga_charts: return 0
            
        chart = varga_charts[config['varga']]
        if 'Ascendant' not in chart: return 0
        
        house_lords = [self._get_lord((chart['Ascendant']['sign_num'] + h - 2) % 12 + 1) for h in config['houses']]
        karakas = config['karakas']

        if md_lord in house_lords: score += 7
        if md_lord in karakas: score += 5
        if self._is_in_kendra_trikona(md_lord, chart): score += 2
        
        if ad_lord in house_lords: score += 10
        if ad_lord in karakas: score += 7
        if self._is_in_kendra_trikona(ad_lord, chart): score += 3

        return score

    def _is_in_kendra_trikona(self, planet_name, chart):
        if planet_name not in chart: return False
        planet_sign = chart[planet_name]['sign_num']
        lagna_sign = chart['Ascendant']['sign_num']
        house = (planet_sign - lagna_sign + 12) % 12 + 1
        return house in [1, 4, 5, 7, 9, 10]

    def _get_lord(self, sign_num):
        return self.sign_lords.get(sign_num)

if __name__ == "__main__":
    app = AstroApp()
    app.mainloop()