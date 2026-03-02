import os
import fiona
from fiona.crs import from_epsg
from domino.base_piece import BasePiece
from .models import InputModel, OutputModel

class CreateIgnitionPiece(BasePiece):
    
    def piece_function(self, input_data: InputModel):
        self.logger.info(f"Spúšťam FIKTÍVNE generovanie pre vstup: {input_data.gps_text}")
        
        # Získame cestu, kam môžeme ukladať výstupy tohto kroku
        output_dir = self.results_path 
        os.makedirs(output_dir, exist_ok=True)
        
        # Názov súboru (názov sa môže líšiť, ale prípona musí byť .shp)
        output_filename = os.path.join(output_dir, "ignition.shp")

        # Jednoduchá schéma len pre geometriu bodu a jedno ID
        schema = {
            'geometry': 'Point',
            'properties': {'id': 'int:10'},
        }

        # Natvrdo vygenerujeme jeden bod
        try:
            with fiona.open(
                output_filename,
                'w',
                driver='ESRI Shapefile',
                crs=from_epsg(4326),
                schema=schema
            ) as sink:
                
                point_feature = {
                    'geometry': {'type': 'Point', 'coordinates': (17.1077, 48.1486)}, # (Lon, Lat)
                    'properties': {'id': 1},
                }
                sink.write(point_feature)
                
            self.logger.info(f"Fiktívny Shapefile úspešne vytvorený: {output_filename}")
            
        except Exception as e:
            self.logger.error(f"Chyba pri zápise fiktívneho Shapefile: {e}")
            raise RuntimeError(f"Zlyhalo generovanie mock súboru: {e}")

        # Odovzdáme cestu ako výstup do ďalšieho kroku (Farsite)

        return OutputModel(ignition_shp_path=output_filename)

