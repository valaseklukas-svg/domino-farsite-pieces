import os
import fiona
from pyproj import Transformer
from domino.base_piece import BasePiece
from .models import InputModel, OutputModel

class CreateIgnitionPiece(BasePiece):
    
    def piece_function(self, input_data: InputModel):
        self.logger.info(f"Startujem generovanie Ignition bodu z GPS: {input_data.gps_text}")
        
        output_dir = self.results_path 
        os.makedirs(output_dir, exist_ok=True)
        output_filename = os.path.join(output_dir, "ignition.shp")

        # 1. Extrakcia cisel z textu
        try:
            coords = input_data.gps_text.split(',')
            val1 = float(coords[0].strip())
            val2 = float(coords[1].strip())
        except Exception as e:
            raise ValueError(f"Neplatny format suradnic: {input_data.gps_text}. Pouzi cisla oddelene ciarkou.")

        # Slovensko lezi na ~48 severne (Lat) a ~17-22 vychodne (Lon)
        if 45 < val1 < 50 and 16 < val2 < 23:
            lat, lon = val1, val2
        elif 45 < val2 < 50 and 16 < val1 < 23:
            lat, lon = val2, val1
        else:
            # Fallback ak nieco mimo SR - standard X, Y (Lon, Lat)
            lon, lat = val1, val2

        self.logger.info(f"Rozpoznané GPS - Longitude: {lon}, Latitude: {lat}")

        # 3. Transformacia z WGS84 (GPS) do S-JTSK (EPSG:5514)
        try:
            # always_xy=True pyproj - presne poradie Lon, Lat
            transformer = Transformer.from_crs("EPSG:4326", "EPSG:5514", always_xy=True)
            x_krovak, y_krovak = transformer.transform(lon, lat)
            self.logger.info(f"Uspesne prepocitane na S-JTSK - X: {x_krovak:.2f}, Y: {y_krovak:.2f}")
        except Exception as e:
            raise RuntimeError(f"Chyba pri transformacii suradníc: {e}")

        # 4. Zapis do Shapefile (metricky system 5514)
        schema = {'geometry': 'Point', 'properties': {'id': 'int:10'}}

        try:
            with fiona.open(
                output_filename, 'w',
                driver='ESRI Shapefile',
                crs="EPSG:5514", 
                schema=schema
            ) as sink:
                point_feature = {
                    'geometry': {'type': 'Point', 'coordinates': (x_krovak, y_krovak)},
                    'properties': {'id': 1},
                }
                sink.write(point_feature)
            
            self.logger.info(f"Shapefile uspesne zapisany na: {output_filename}")
            
        except Exception as e:
            raise RuntimeError(f"Zlyhal zapis do shapefile suboru: {e}")

        return OutputModel(ignition_shp_path=output_filename)

