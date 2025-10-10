import math
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import datetime
import swisseph as swe

# --- Global Data Definitions ---

SIGNS = {
    1: "Aries", 2: "Taurus", 3: "Gemini", 4: "Cancer", 5: "Leo", 6: "Virgo", 
    7: "Libra", 8: "Scorpio", 9: "Sagittarius", 10: "Capricorn", 11: "Aquarius", 12: "Pisces"
}

SIGN_NATURE = {
    1: "Odd", 2: "Even", 3: "Odd", 4: "Even", 5: "Odd", 6: "Even", 
    7: "Odd", 8: "Even", 9: "Odd", 10: "Even", 11: "Odd", 12: "Even"
}

PLANETS = {
    "Ascendant": swe.ASC, "Sun": swe.SUN, "Moon": swe.MOON, "Mercury": swe.MERCURY, 
    "Venus": swe.VENUS, "Mars": swe.MARS, "Jupiter": swe.JUPITER, "Saturn": swe.SATURN, 
    "Rahu": swe.MEAN_NODE,
}

# --- Core Calculation Engines ---

class NatalChartCalculator:
    # (This class remains unchanged from the last correct version)
    def __init__(self, ayanamsa='LAHIRI'):
        swe.set_ephe_path(None)
        self.ayanamsa_code = getattr(swe, f'SIDM_{ayanamsa}')
        swe.set_sid_mode(self.ayanamsa_code)

    def calculate_d1(self, year, month, day, hour, minute, lat, lon, timezone_offset):
        birth_dt_local = datetime.datetime(year, month, day, hour, minute)
        birth_dt_utc = birth_dt_local - datetime.timedelta(hours=timezone_offset)
        julian_day_utc = swe.utc_to_jd(birth_dt_utc.year, birth_dt_utc.month, birth_dt_utc.day, birth_dt_utc.hour, birth_dt_utc.minute, 0, 1)[1]
        
        chart_data = {} # Use a dictionary for easier lookup
        raw_chart_data = [] # For ordered display

        try:
            _, ascmc = swe.houses(julian_day_utc, lat, lon, b'P')
            asc_longitude = ascmc[0]
            sign, dms, sign_num, lon_dec = self._format_longitude(asc_longitude)
            chart_data["Ascendant"] = {"sign_num": sign_num, "lon_decimal": lon_dec, "sign_name": sign, "dms": dms}
            raw_chart_data.append(("Ascendant", sign, dms))
        except swe.Error as e:
            messagebox.showerror("Swiss Ephemeris Error", f"Could not calculate Ascendant.\n\nDetails: {e}")
            return None, None

        for name, planet_id in PLANETS.items():
            planet_pos = swe.calc_ut(julian_day_utc, planet_id, swe.FLG_SWIEPH | swe.FLG_SIDEREAL)[0]
            planet_longitude = planet_pos[0]
            sign, dms, sign_num, lon_dec = self._format_longitude(planet_longitude)
            chart_data[name] = {"sign_num": sign_num, "lon_decimal": lon_dec, "sign_name": sign, "dms": dms}
            raw_chart_data.append((name, sign, dms))

            if name == "Rahu":
                ketu_longitude = (planet_longitude + 180) % 360
                sign, dms, sign_num, lon_dec = self._format_longitude(ketu_longitude)
                chart_data["Ketu"] = {"sign_num": sign_num, "lon_decimal": lon_dec, "sign_name": sign, "dms": dms}
                raw_chart_data.append(("Ketu", sign, dms))
        return chart_data, raw_chart_data

    def _format_longitude(self, lon_decimal):
        sign_num = int(lon_decimal / 30) + 1
        lon_in_sign = lon_decimal % 30
        sign_name = SIGNS.get(sign_num, "Error")
        deg, min_dec = int(lon_in_sign), (lon_in_sign - int(lon_in_sign)) * 60
        minute, sec_dec = int(min_dec), (min_dec - int(min_dec)) * 60
        sec = round(sec_dec, 2)
        dms_str = f"{deg:02d}° {minute:02d}' {sec:05.2f}\""
        return sign_name, dms_str, sign_num, lon_in_sign

class VargaCalculator:
    def __init__(self):
        self.D24_DEITIES = ("Skanda","Parashudhara","Anala","Vishwakarma","Bhaga","Mitra","Maya","Antaka","Vrishadhvaja","Govinda","Jayanta","Vasuki")
        self.D60_DEITIES = ("Ghora","Rakshasa","Deva","Kubera","Yaksha","Kinnara","Bhrashta","Kulaghna","Garala","Vahni","Maya","Puriihaka","Apampathi","Marutwana","Kaala","Sarpa","Amrita","Indu","Mridu","Komala","Heramba","Brahma","Vishnu","Maheshwara","Deva","Ardra","Kalinasa","Kshiteesa","Kamalakara","Gulika","Mrityu","Kaala","Davagni","Ghora","Yama","Kantaka","Sudha","Amrita","Poorna","VishaDagdha","Kulanasa","Vamshakshya","Utpata","Kaala","Saumya","Komala","Seetala","Karaladamshtra","Chandramukhi","Praveena","Kaalpavaka","Dandayudha","Nirmala","Saumya","Kroora","Atisheetala","Amrita","Payodhi","Bhramana","Chandrarekha")

    def calculate(self, varga_num, d1_lon, d1_sign):
        varga_map = {2: self._calculate_d2, 3: self._calculate_d3, 5: self._calculate_d5, 6: self._calculate_d6, 7: self._calculate_d7, 9: self._calculate_d9, 10: self._calculate_d10, 20: self._calculate_d20, 24: self._calculate_d24, 60: self._calculate_d60}
        if varga_num in varga_map: return varga_map[varga_num](d1_lon, d1_sign)
        return None, None, "N/A"

    def _calculate_d2(self, d1_lon, d1_sign):
        amsa_index = math.floor(d1_lon / 15)
        lon = (d1_lon % 15) * 2
        sign_nat = SIGN_NATURE[d1_sign]
        sign, details = (5, "Sun's Hora") if (sign_nat == "Odd" and amsa_index == 0) or (sign_nat == "Even" and amsa_index == 1) else (4, "Moon's Hora")
        return sign, lon, details

    def _calculate_d3(self, d1_lon, d1_sign):
        amsa_index = math.floor(d1_lon / 10)
        lon = (d1_lon % 10) * 3
        offset = [0, 4, 8][amsa_index]
        sign = (d1_sign + offset - 1) % 12 + 1
        return sign, lon, ""

    def _calculate_d5(self, d1_lon, d1_sign):
        # RECTIFIED: Using a more standard Parashari method.
        amsa_index = math.floor(d1_lon / 6)
        lon = (d1_lon % 6) * 5
        start_sign = 1 if SIGN_NATURE[d1_sign] == "Odd" else 6 # Aries for Odd, Virgo for Even
        sign = (start_sign + amsa_index - 1) % 12 + 1
        return sign, lon, ""
    
    def _calculate_d6(self, d1_lon, d1_sign):
        amsa_index = math.floor(d1_lon / 5)
        lon = (d1_lon % 5) * 6
        start_sign = 1 if SIGN_NATURE[d1_sign] == "Odd" else 7
        sign = (start_sign + amsa_index - 1) % 12 + 1
        return sign, lon, ""

    def _calculate_d7(self, d1_lon, d1_sign):
        amsa_index = math.floor(d1_lon / (30/7))
        lon = (d1_lon % (30/7)) * 7
        start_sign = d1_sign if SIGN_NATURE[d1_sign] == "Odd" else (d1_sign + 6)
        sign = (start_sign + amsa_index - 1) % 12 + 1
        return sign, lon, ""

    def _calculate_d9(self, d1_lon, d1_sign):
        amsa_index = math.floor(d1_lon / (30/9))
        lon = (d1_lon % (30/9)) * 9
        sign_type = (d1_sign - 1) % 4
        start_signs = {0: 1, 1: 10, 2: 7, 3: 4} # Fiery, Earthy, Airy, Watery
        sign = (start_signs[sign_type] + amsa_index - 1) % 12 + 1
        return sign, lon, ""

    def _calculate_d10(self, d1_lon, d1_sign):
        amsa_index = math.floor(d1_lon / 3)
        lon = (d1_lon % 3) * 10
        start_sign = d1_sign if SIGN_NATURE[d1_sign] == "Odd" else (d1_sign + 8)
        sign = (start_sign + amsa_index - 1) % 12 + 1
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
        deity_idx = amsa_index % 12
        if SIGN_NATURE[d1_sign] == "Odd":
            sign = (5 + amsa_index - 1) % 12 + 1
            details = self.D24_DEITIES[deity_idx]
        else:
            sign = (4 - amsa_index - 1 + 12) % 12 + 1
            details = self.D24_DEITIES[11 - deity_idx]
        return sign, lon, details
        
    def _calculate_d60(self, d1_lon, d1_sign):
        # RECTIFIED: Using proper sign calculation for D60.
        amsa_index = math.floor(d1_lon * 2) # 60 divisions in 30 degrees
        lon = (d1_lon * 2 % 1) * 30
        
        sign_offset = amsa_index % 12
        d60_sign = ((d1_sign - 1 + sign_offset) % 12) + 1
        
        details = self.D60_DEITIES[amsa_index]
        return d60_sign, lon, details

# --- Helper Functions for GUI ---
def dms_to_decimal(deg, min, sec): return deg + min / 60 + sec / 3600
def decimal_to_dms(decimal_degrees):
    if decimal_degrees >= 30.0: decimal_degrees = 29.99999
    degrees = int(decimal_degrees); minutes = int((decimal_degrees - degrees) * 60); seconds = round((((decimal_degrees - degrees) * 60) - minutes) * 60, 2)
    if seconds >= 60: seconds -= 60; minutes += 1
    if minutes >= 60: minutes -= 60; degrees += 1
    return f"{degrees:02d}° {minutes:02d}' {seconds:05.2f}\""

# --- Main GUI Application ---

class AstroApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.d1_calculator = NatalChartCalculator()
        self.varga_calculator = VargaCalculator()
        self.title("AstroVighati Pro - Chart Calculator")
        self.geometry("950x650")

        self.d1_chart_data = None # To store D1 results

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(pady=10, padx=10, fill="both", expand=True)
        self.d1_tab = ttk.Frame(self.notebook)
        self.varga_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.d1_tab, text='Natal Chart (D1) Calculator')
        self.notebook.add(self.varga_tab, text='Divisional Chart (Varga) Calculator')

        self.create_d1_tab_widgets()
        self.varga_app_handler = VargaApp(self.varga_tab, self.varga_calculator, self)

    def create_d1_tab_widgets(self):
        frame = ttk.LabelFrame(self.d1_tab, text="Birth Details", padding=10)
        frame.pack(fill="x", padx=10, pady=10)
        # ... (Input fields setup is the same)
        ttk.Label(frame, text="Date (DD/MM/YYYY):").grid(row=0, column=0, sticky="w", padx=5); self.day_var = tk.StringVar(value="8"); self.month_var = tk.StringVar(value="10"); self.year_var = tk.StringVar(value="2003"); ttk.Entry(frame, textvariable=self.day_var, width=4).grid(row=0, column=1); ttk.Entry(frame, textvariable=self.month_var, width=4).grid(row=0, column=2); ttk.Entry(frame, textvariable=self.year_var, width=6).grid(row=0, column=3)
        ttk.Label(frame, text="Time (HH:MM 24hr):").grid(row=1, column=0, sticky="w", padx=5, pady=5); self.hour_var = tk.StringVar(value="19"); self.minute_var = tk.StringVar(value="30"); ttk.Entry(frame, textvariable=self.hour_var, width=4).grid(row=1, column=1); ttk.Entry(frame, textvariable=self.minute_var, width=4).grid(row=1, column=2)
        ttk.Label(frame, text="Latitude / Longitude:").grid(row=2, column=0, sticky="w", padx=5); self.lat_var = tk.StringVar(value="21.1702"); self.lon_var = tk.StringVar(value="72.8311"); ttk.Entry(frame, textvariable=self.lat_var, width=10).grid(row=2, column=1, columnspan=2); ttk.Entry(frame, textvariable=self.lon_var, width=10).grid(row=2, column=3, columnspan=2)
        ttk.Label(frame, text="Timezone Offset (UTC):").grid(row=3, column=0, sticky="w", padx=5, pady=5); self.tz_var = tk.StringVar(value="5.5"); ttk.Entry(frame, textvariable=self.tz_var, width=4).grid(row=3, column=1)
        ttk.Button(frame, text="Calculate D1 Chart", command=self.calculate_d1_chart).grid(row=4, column=0, columnspan=4, pady=10)
        
        output_frame = ttk.LabelFrame(self.d1_tab, text="D1 - Lagna Chart", padding=10)
        output_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.d1_tree = ttk.Treeview(output_frame, columns=("planet", "sign", "dms"), show="headings")
        self.d1_tree.heading("planet", text="Planet"); self.d1_tree.heading("sign", text="Sign"); self.d1_tree.heading("dms", text="Longitude (DMS)")
        self.d1_tree.pack(fill="both", expand=True)

    def calculate_d1_chart(self):
        try:
            year, month, day = int(self.year_var.get()), int(self.month_var.get()), int(self.day_var.get())
            hour, minute = int(self.hour_var.get()), int(self.minute_var.get())
            lat, lon, tz = float(self.lat_var.get()), float(self.lon_var.get()), float(self.tz_var.get())
        except ValueError:
            messagebox.showerror("Invalid Input", "Please ensure all fields contain valid numbers.")
            return

        self.d1_tree.delete(*self.d1_tree.get_children())
        self.d1_chart_data, raw_chart_data = self.d1_calculator.calculate_d1(year, month, day, hour, minute, lat, lon, tz)
        
        if raw_chart_data:
            for row in raw_chart_data:
                self.d1_tree.insert("", "end", values=row)
            messagebox.showinfo("Success", "D1 Chart calculated. You can now use this data in the 'Divisional Chart' tab.")
            self.varga_app_handler.update_d1_data()


class VargaApp: 
    def __init__(self, parent_tab, calculator, main_app):
        self.parent = parent_tab
        self.calculator = calculator
        self.main_app = main_app
        self.sign_name_to_num = {v: k for k, v in SIGNS.items()}
        self.varga_map = {"D2 - Hora": 2, "D3 - Drekkana": 3, "D5 - Panchamsa": 5, "D6 - Shashthamsa": 6, "D7 - Saptamsa": 7, "D9 - Navamsa": 9, "D10 - Dasamsa": 10, "D20 - Vimsamsa": 20, "D24 - Siddhamsa": 24, "D60 - Shashtyamsa": 60}
        
        self.create_widgets()
        self.toggle_input_mode() # Set initial state

    def create_widgets(self):
        # Input Source Selection
        source_frame = ttk.LabelFrame(self.parent, text="Input Source", padding=(10,5))
        source_frame.pack(fill="x", padx=10, pady=(10,0))
        self.input_mode = tk.StringVar(value="manual")
        ttk.Radiobutton(source_frame, text="Manual Entry", variable=self.input_mode, value="manual", command=self.toggle_input_mode).pack(side="left", padx=5)
        ttk.Radiobutton(source_frame, text="From Calculated D1 Chart", variable=self.input_mode, value="d1_chart", command=self.toggle_input_mode).pack(side="left", padx=5)

        # Manual Input Frame
        self.input_frame = ttk.LabelFrame(self.parent, text="Planet Input", padding=(10, 5))
        self.input_frame.pack(fill="x", padx=10, pady=10)

        # Chart and Planet selection
        ttk.Label(self.input_frame, text="Chart:").grid(row=0, column=0, sticky="w", padx=5); self.varga_var = tk.StringVar(); self.varga_combo = ttk.Combobox(self.input_frame, textvariable=self.varga_var, values=list(self.varga_map.keys()), state="readonly", width=15); self.varga_combo.grid(row=0, column=1, padx=5); self.varga_combo.set("D9 - Navamsa")
        ttk.Label(self.input_frame, text="Planet:").grid(row=0, column=2, sticky="w", padx=5); self.planet_var = tk.StringVar(); self.planet_combo = ttk.Combobox(self.input_frame, textvariable=self.planet_var, state="readonly", width=12); self.planet_combo.grid(row=0, column=3, padx=5)

        # Manual D1 position fields
        self.manual_widgets = []
        lbl_sign = ttk.Label(self.input_frame, text="Sign:"); lbl_sign.grid(row=0, column=4, sticky="w", padx=5); self.manual_widgets.append(lbl_sign)
        self.sign_var = tk.StringVar(); self.sign_combo = ttk.Combobox(self.input_frame, textvariable=self.sign_var, values=list(SIGNS.values()), state="readonly", width=12); self.sign_combo.grid(row=0, column=5, padx=5); self.sign_combo.set("Aries"); self.manual_widgets.append(self.sign_combo)
        lbl_lon = ttk.Label(self.input_frame, text="Longitude:"); lbl_lon.grid(row=0, column=6, sticky="w", padx=5); self.manual_widgets.append(lbl_lon)
        self.deg_var = tk.StringVar(); self.min_var = tk.StringVar(); self.sec_var = tk.StringVar()
        entry_deg = ttk.Entry(self.input_frame, textvariable=self.deg_var, width=4); entry_deg.grid(row=0, column=7); self.manual_widgets.append(entry_deg)
        lbl_deg = ttk.Label(self.input_frame, text="°"); lbl_deg.grid(row=0, column=8); self.manual_widgets.append(lbl_deg)
        entry_min = ttk.Entry(self.input_frame, textvariable=self.min_var, width=4); entry_min.grid(row=0, column=9); self.manual_widgets.append(entry_min)
        lbl_min = ttk.Label(self.input_frame, text="'"); lbl_min.grid(row=0, column=10); self.manual_widgets.append(lbl_min)
        entry_sec = ttk.Entry(self.input_frame, textvariable=self.sec_var, width=4); entry_sec.grid(row=0, column=11); self.manual_widgets.append(entry_sec)
        lbl_sec = ttk.Label(self.input_frame, text='"'); lbl_sec.grid(row=0, column=12); self.manual_widgets.append(lbl_sec)

        # Buttons and Output
        button_frame = ttk.Frame(self.parent); button_frame.pack(fill="x", padx=10, pady=(0, 10))
        ttk.Button(button_frame, text="Calculate & Add", command=self.add_planet).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Clear Chart", command=self.clear_chart).pack(side="left", padx=5)
        self.output_frame = ttk.LabelFrame(self.parent, text="Divisional Chart Results", padding=(10, 5)); self.output_frame.pack(fill="both", expand=True, padx=10, pady=10)
        columns = ("planet", "d1_pos", "varga_sign", "varga_lon", "details"); self.tree = ttk.Treeview(self.output_frame, columns=columns, show="headings")
        self.tree.heading("planet", text="Planet"); self.tree.heading("d1_pos", text="D1 Position"); self.tree.heading("varga_sign", text="Varga Sign"); self.tree.heading("varga_lon", text="Varga Longitude"); self.tree.heading("details", text="Details"); self.tree.pack(fill="both", expand=True)

    def toggle_input_mode(self):
        mode = self.input_mode.get()
        if mode == "manual":
            for widget in self.manual_widgets: widget.config(state="normal")
            self.planet_combo.config(values=["Ascendant", "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"])
            self.planet_combo.set("Sun")
        else: # d1_chart mode
            for widget in self.manual_widgets: widget.config(state="disabled")
            self.update_d1_data()

    def update_d1_data(self):
        if self.input_mode.get() == "d1_chart":
            if self.main_app.d1_chart_data:
                planet_names = list(self.main_app.d1_chart_data.keys())
                self.planet_combo.config(values=planet_names)
                if planet_names: self.planet_combo.set(planet_names[0])
            else:
                self.planet_combo.config(values=[])
                self.planet_combo.set("")
                messagebox.showwarning("No D1 Data", "Please calculate a D1 chart first in the 'Natal Chart' tab.")
                self.input_mode.set("manual")
                self.toggle_input_mode()

    def add_planet(self):
        try:
            varga_key = self.varga_var.get()
            if not varga_key: raise ValueError("Select a chart type.")
            varga_num = self.varga_map[varga_key]
            
            planet_name = self.planet_var.get()
            if not planet_name: raise ValueError("Select a planet.")

            if self.input_mode.get() == "manual":
                sign_name = self.sign_var.get()
                sign_num = self.sign_name_to_num[sign_name]
                deg, minute, sec = int(self.deg_var.get() or 0), int(self.min_var.get() or 0), float(self.sec_var.get() or 0.0)
                lon_decimal = dms_to_decimal(deg, minute, sec)
                d1_pos_str = f"{sign_name} {deg:02d}° {minute:02d}' {sec:05.2f}\""
            else: # From D1 Chart
                planet_data = self.main_app.d1_chart_data.get(planet_name)
                if not planet_data: raise ValueError("Planet data not found.")
                sign_num = planet_data["sign_num"]
                lon_decimal = planet_data["lon_decimal"]
                d1_pos_str = f"{planet_data['sign_name']} {planet_data['dms']}"
            
            varga_sign_num, varga_lon_dec, details = self.calculator.calculate(varga_num, lon_decimal, sign_num)
            varga_sign_name = SIGNS[varga_sign_num]
            varga_lon_dms = decimal_to_dms(varga_lon_dec)
            self.output_frame.config(text=f"{varga_key} Results")
            self.tree.insert("", "end", values=(planet_name, d1_pos_str, varga_sign_name, varga_lon_dms, details))
        except (ValueError, KeyError, tk.TclError) as e:
            messagebox.showerror("Calculation Error", f"An error occurred: {e}")

    def clear_chart(self):
        self.tree.delete(*self.tree.get_children())


if __name__ == "__main__":
    app = AstroApp()
    app.mainloop()