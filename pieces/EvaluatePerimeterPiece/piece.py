import os
import glob
import re
import zipfile
import requests
import warnings
import pandas as pd
import geopandas as gpd
from datetime import datetime, timedelta

from domino.base_piece import BasePiece
from .models import InputModel, OutputModel

warnings.filterwarnings('ignore')
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class EvaluatePerimeterPiece(BasePiece):

    def zjednot_crs(self, gdf: gpd.GeoDataFrame, target_crs) -> gpd.GeoDataFrame:
        """Zjednotenie suradnicovych systemov (CRS)."""
        if gdf is None or gdf.empty:
            return gdf
        if gdf.crs is None:
            gdf.set_crs(target_crs, allow_override=True, inplace=True)
        elif gdf.crs != target_crs:
            gdf = gdf.to_crs(target_crs)
        return gdf

    def extract_start_time_from_txt(self, unzip_dir: str):
        """Prehlada textove vystupy Farsitu (napr. Timings.txt) pre cas zaciatku."""
        month, day, hour = 8, 1, 0  # Fallback
        
        txt_files = glob.glob(os.path.join(unzip_dir, "*.txt"))
        
        for txt_file in txt_files:
            try:
                with open(txt_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read().lower()
                    
                    m_match = re.search(r'startmonth\s*[:=]?\s*(\d+)', content)
                    d_match = re.search(r'startday\s*[:=]?\s*(\d+)', content)
                    h_match = re.search(r'starthour\s*[:=]?\s*(\d+)', content)
                    
                    if m_match and d_match and h_match:
                        month = int(m_match.group(1))
                        day = int(d_match.group(1))
                        hour = int(h_match.group(1))
                        self.logger.info(f"Uspesne nacitany cas zo suboru {os.path.basename(txt_file)}")
                        return month, day, hour
            except Exception:
                pass
                
        self.logger.warning("V .txt suboroch (Timings atd.) sa nenasiel cas startu. Pouzivam fallback 01.08. 00:00.")
        return month, day, hour

    def piece_function(self, input_data: InputModel):
        output_dir = self.results_path
        os.makedirs(output_dir, exist_ok=True)
        
        # --- 1. Rozbalenie ZIPu z FARSITE ---
        unzip_dir = os.path.join(output_dir, "farsite_outputs")
        os.makedirs(unzip_dir, exist_ok=True)
        self.logger.info("Rozbalujem ZIP s Farsite vysledkami...")
        
        with zipfile.ZipFile(input_data.outputs_zip_path, 'r') as zip_ref:
            zip_ref.extractall(unzip_dir)
            
        # Najdenie Shapefile Perimetrov
        perimeters_files = glob.glob(os.path.join(unzip_dir, "*Perimeters.shp"))
        if not perimeters_files:
            raise FileNotFoundError("V ZIPe sa nenasiel subor *Perimeters.shp!")
        lineshape_path = perimeters_files[0]

        # --- 2. Ziskanie startovacieho casu priamo z vystupov ---
        s_month, s_day, s_hour = self.extract_start_time_from_txt(unzip_dir)
        h_val = s_hour // 100
        m_val = s_hour % 100
        FIXED_YEAR = 2024
        dt_start = datetime(FIXED_YEAR, s_month, s_day, h_val, m_val)
        self.logger.info(f"Zaciatok simulacie nastaveny na: {dt_start.strftime('%d.%m. %H:%M')}")

        # --- 3. Nacitanie GIS dat ---
        buffer_gdf = gpd.read_file(input_data.buffer_shp_path)
        buffer_geom = buffer_gdf.geometry.unary_union
        lines_gdf = gpd.read_file(lineshape_path)
        ign_gdf = gpd.read_file(input_data.ignition_shp_path)

        # Zjednotenie CRS
        target_crs = buffer_gdf.crs
        lines_gdf = self.zjednot_crs(lines_gdf, target_crs)
        ign_gdf = self.zjednot_crs(ign_gdf, target_crs)

        # --- 4. Vyhodnotenie prieniku ---
        vysledok = {'RUN_ID': 1, 'CAS_RAW': "NO_INTERSECTION", 'HODINY_OD_STARTU': None, 'ZDROJ_V_BUFFRI': False, 'POZNAMKA': ''}

        if not ign_gdf.empty:
            vysledok['ZDROJ_V_BUFFRI'] = ign_gdf.geometry.iloc[0].within(buffer_geom)
        
        cols = [c.upper() for c in lines_gdf.columns]
        col_map = {c.upper(): c for c in lines_gdf.columns}
        month_key = next((c for c in cols if c in ['MONTH', 'MESIAC', 'MES']), None)
        day_key = next((c for c in cols if c in ['DAY', 'DEN']), None)
        hour_key = next((c for c in cols if c in ['HOUR', 'HODINA', 'HOD']), None)

        found_time_cols = all([month_key, day_key, hour_key])
        if found_time_cols:
            lines_gdf['SORT_M'] = lines_gdf[col_map[month_key]].astype(int)
            lines_gdf['SORT_D'] = lines_gdf[col_map[day_key]].astype(int)
            lines_gdf['SORT_H'] = lines_gdf[col_map[hour_key]].astype(int)
            lines_gdf = lines_gdf.sort_values(by=['SORT_M', 'SORT_D', 'SORT_H'])

        prienik_nasiel = False
        for idx, row in lines_gdf.iterrows():
            if row.geometry.intersects(buffer_geom):
                if found_time_cols:
                    m = int(row[col_map[month_key]])
                    d = int(row[col_map[day_key]])
                    h_raw = int(row[col_map[hour_key]])
                    
                    vysledok['CAS_RAW'] = f"{m}/{d}/{h_raw}"
                    dt_current = datetime(FIXED_YEAR, m, d) + timedelta(hours=h_raw//100, minutes=h_raw%100)
                    delta = dt_current - dt_start
                    vysledok['HODINY_OD_STARTU'] = int(delta.total_seconds() / 3600)
                else:
                    vysledok['POZNAMKA'] = "Chybaju stlpce casu v perimetri."
                prienik_nasiel = True
                break

        # --- 5. Urcenie statusu pre API ---
        status = "ok"
        hours = vysledok['HODINY_OD_STARTU']
        
        if vysledok['ZDROJ_V_BUFFRI']:
            status = "critical"
            self.logger.warning("Ignition je v buffri!")
        elif prienik_nasiel and hours is not None:
            if hours < 12: status = "critical"
            elif 12 <= hours <= 48: status = "warning"
            else: status = "moderate"
        
        self.logger.info(f"==> STATUS: {status.upper()} <==")

        # --- 6. Ulozenie CSV a odoslanie API ---
        csv_path = os.path.join(output_dir, "vyhodnotenie_perimetra.csv")
        pd.DataFrame([vysledok]).to_csv(csv_path, index=False, sep=';')
        
        try:
            requests.post("https://dicris.sk:8000/models", json={"name": input_data.api_model_name, "status": status}, verify=False, timeout=10)
            self.logger.info("API request uspesne odoslany.")
        except Exception as e:
            self.logger.error(f"Chyba pri odosielani na API: {e}")

        self.display_result = {"file_type": "csv", "file_path": csv_path}

        return OutputModel(csv_report_path=csv_path, alert_status=status)