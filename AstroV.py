import swisseph as swe
import math
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Tuple

# --- Pre-requisites and Mock Data ---
# This is a mock class for the VargaCalculator.
class EnhancedAstrologicalData:
    """Mock class to provide data needed by VargaCalculator."""
    SIGN_NATURE = {
        1: 'Odd', 2: 'Even', 3: 'Odd', 4: 'Even',
        5: 'Odd', 6: 'Even', 7: 'Odd', 8: 'Even',
        9: 'Odd', 10: 'Even', 11: 'Odd', 12: 'Even'
    }

# Mocking messagebox for a console app. We'll just print errors.
class MockMessageBox:
    def showerror(self, title, message):
        print(f"--- ERROR: {title} ---")
        print(message)
messagebox = MockMessageBox()

# This is assumed to be True if the 'import swe' succeeded
SWISSEPH_AVAILABLE = True

# List of sign names for printing
SIGN_NAMES = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]


# --- A) YOUR VargaCalculator CLASS (Known to be Correct) ---
class VargaCalculator:
    """
    Calculates all Divisional (Varga) charts based on mathematical
    rules from classical Vedic astrology (Parashari system).
    """
    def __init__(self) -> None:
        pass # Removed D60 deities for this test to keep it simple

    def calculate_varga_position(self, varga_num: int, d1_longitude_in_sign: float, d1_sign_num: int) -> Tuple[int, float, str]:
        """
        Main dispatcher function for Varga calculations.
        """
        lon_in_sign = d1_longitude_in_sign
        sign = d1_sign_num
        new_sign: int = 1
        new_lon: float = 0.0

        if varga_num == 9: # D9 Navamsa (Spouse, Dharma)
            division_size = 30 / 9 # 3° 20'
            amsa = math.floor(lon_in_sign / division_size) # 0-8
            new_lon = (lon_in_sign % division_size) * 9
            rashi_type = (sign - 1) % 4
            start_sign = [1, 10, 7, 4][rashi_type]
            new_sign = (start_sign + amsa - 1) % 12 + 1
            return new_sign, new_lon, ""
        
        # Add other vargas here if needed
        
        # Fallback for other Vargas
        division_size = 30 / varga_num
        amsa = math.floor(lon_in_sign / division_size)
        new_lon = (lon_in_sign % division_size) * varga_num
        new_sign = (sign + amsa - 1) % 12 + 1
        return new_sign, new_lon, ""


# --- B) The MAIN CALCULATION ENGINE ---
class AstroTester:
    """
    This class holds the rectified calculation functions
    and the helper functions needed to run this test.
    """
    def __init__(self):
        self.varga_calculator = VargaCalculator()
        
        # --- This is the helper function your main app has ---
    def _process_longitude(self, longitude: float) -> Dict[str, Any]:
        """
        A simple version of your helper function.
        It converts a raw longitude (0-360) into the data
        needed for calculation and display.
        """
        # Get the sign number (1-12)
        rashi_num = int(longitude // 30) + 1
        # Get the longitude within that sign (0-30)
        degree_in_rashi = longitude % 30
        
        # Format for printing
        deg = int(degree_in_rashi)
        minutes = int((degree_in_rashi * 60) % 60)
        seconds = int((degree_in_rashi * 3600) % 60)

        return {
            "longitude": longitude,       # Raw longitude (0-360)
            "rashi_num": rashi_num,         # Sign number (1-12)
            "degree_in_rashi": degree_in_rashi, # Longitude in sign (0.0-30.0)
            "sign_name": SIGN_NAMES[rashi_num - 1],
            "dms_str": f"{deg:02}° {minutes:02}' {seconds:02}\""
        }

    # --- C) THE RECTIFIED `calculate_planet_positions` FUNCTION ---
    def calculate_planet_positions(self, dt_local: datetime, lat: float, lon: float, timezone_offset: float) -> Optional[Dict[str, Dict[str, Any]]]:
        """
        This is the FULLY RECTIFIED function from our discussion.
        """
        
        if not SWISSEPH_AVAILABLE:
            messagebox.showerror("Dependency Missing", "The 'pyswisseph' library is required.")
            return None
            
        try:
            # --- Step 1: Set Global Ephemeris Mode (CRITICAL FIX) ---
            # This sets the mode to Lahiri for swe.houses()
            swe.set_sid_mode(swe.SIDM_LAHIRI)

            # --- Step 2: Robust Timezone Conversion ---
            tz_info = timezone(timedelta(hours=timezone_offset))
            dt_aware = dt_local.replace(tzinfo=tz_info)
            dt_utc = dt_aware.astimezone(timezone.utc)

            # --- Step 3: Convert UTC to Julian Day ---
            jd_utc_tuple = swe.utc_to_jd(
                dt_utc.year, dt_utc.month, dt_utc.day,
                dt_utc.hour, dt_utc.minute, dt_utc.second,
                1  # Gregorian calendar
            )
            jd_et = jd_utc_tuple[0]  # Ephemeris Time (for Ayanamsa check)
            jd_utc = jd_utc_tuple[1] # Universal Time (for calculations)

            # --- 4. DEBUG TEST ---
            # This will print to your console and PROVE the mode is set.
            current_ayanamsa = swe.get_ayanamsa(jd_et)
            print(f"\n--- DEBUG: Current Ayanamsa is: {current_ayanamsa:.6f} ---")
            print("(This value MUST be ~24.0, not 0.0)\n")

            # --- 5. Define Planets (Using True Node) ---
            planet_codes: Dict[str, int] = {
                "Sun": swe.SUN, "Moon": swe.MOON, "Mercury": swe.MERCURY,
                "Venus": swe.VENUS, "Mars": swe.MARS, "Jupiter": swe.JUPITER,
                "Saturn": swe.SATURN, "Rahu": swe.TRUE_NODE,
            }
            positions: Dict[str, Dict[str, Any]] = {}

            # --- 6. Calculate the Ascendant (Lagna) ---
            # This now correctly calculates the SIDEREAL ascendant
            _, ascmc = swe.houses(jd_utc, lat, lon, b'S') # 'S' = Sripathi
            asc_longitude = ascmc[0] 
            positions['Ascendant'] = self._process_longitude(asc_longitude) 
            positions['Ascendant']['speed'] = 0.0

            # --- 7. Calculate Positions for all Planets ---
            for name, code in planet_codes.items():
                planet_pos_data = swe.calc_ut(
                    jd_utc, code, swe.FLG_SWIEPH | swe.FLG_SIDEREAL
                )[0]
                planet_longitude = planet_pos_data[0]
                planet_speed = planet_pos_data[3]
                positions[name] = self._process_longitude(planet_longitude)
                positions[name]['speed'] = planet_speed

            # --- 8. Calculate Ketu (South Node) ---
            rahu_longitude = positions['Rahu']['longitude']
            ketu_longitude = (rahu_longitude + 180) % 360
            positions['Ketu'] = self._process_longitude(ketu_longitude)
            positions['Ketu']['speed'] = positions['Rahu'].get('speed', 0) * -1

            # --- 9. Return Final Results ---
            return positions

        except swe.Error as e:
            messagebox.showerror("Swiss Ephemeris Error", f"A calculation error occurred:\n\n{e}")
            return None
        except Exception as e:
            messagebox.showerror("Calculation Error", f"An unexpected error occurred:\n\n{e}")
            return None

# --- D) TEST RUNNER ---
if __name__ == "__main__":
    """
    This block runs ONLY when you execute this file directly.
    """
    
    # --- 1. SET BIRTH DATA ---
    # Based on the JHora screenshot (image_b810a2.png), the birth data is
    # approximately June 14, 2000, 5:30 AM, in India.
    # We'll use a standard location like Mumbai for this test.
    
    # (Year, Month, Day, Hour, Minute, Second)
    birth_dt_local = datetime(2003, 11, 14, 19, 41, 46) 
    birth_lat = 28.842490    # Mumbai Latitude
    birth_lon = 77.580878    # Mumbai Longitude
    birth_tz_offset = 5.5  # India Standard Time (IST)

    print(f"--- Independent Test Runner ---")
    print(f"Calculating for: {birth_dt_local.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Location: Lat {birth_lat}, Lon {birth_lon}, TZ {birth_tz_offset}")

    # --- 2. INITIALIZE AND RUN ---
    tester = AstroTester()
    d1_positions = tester.calculate_planet_positions(
        birth_dt_local, birth_lat, birth_lon, birth_tz_offset
    )

    if d1_positions:
        print("\n--- D1 RASHI CHART (RECTIFIED) ---")
        print(f"{'Body':<10} | {'Sign':<11} | {'Longitude':<16} | {'(Raw Long)':<10}")
        print("-" * 54)
        
        # We need to print in the same order as JHora
        planet_order = ["Ascendant", "Sun", "Moon", "Mars", "Mercury", 
                        "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
        
        for name in planet_order:
            if name in d1_positions:
                pos = d1_positions[name]
                print(f"{name:<10} | {pos['sign_name']:<11} | {pos['dms_str']:<16} | ({pos['longitude']:.4f})")
        
        # --- 3. CALCULATE D9 ASCENDANT ---
        print("\n--- D9 NAVAMSA CALCULATION ---")
        
        # Get the D1 Ascendant's data
        d1_asc_data = d1_positions['Ascendant']
        d1_sign = d1_asc_data['rashi_num']
        d1_lon_in_sign = d1_asc_data['degree_in_rashi']

        print(f"Feeding D1 Ascendant into VargaCalculator:")
        print(f"  -> D1 Sign Num: {d1_sign} ({d1_asc_data['sign_name']})")
        print(f"  -> D1 Long in Sign: {d1_lon_in_sign:.4f} degrees")
        
        # Run the (correct) VargaCalculator
        d9_sign_num, _, _ = tester.varga_calculator.calculate_varga_position(
            varga_num=9,
            d1_longitude_in_sign=d1_lon_in_sign,
            d1_sign_num=d1_sign
        )
        
        print("\n--- D9 ASCENDANT (RESULT) ---")
        print(f"The D9 Ascendant is in: {SIGN_NAMES[d9_sign_num - 1]}")
        print("\nCompare this output to Jagannath Hora. It should now match.")

    else:
        print("Calculation failed. Check error messages.")
