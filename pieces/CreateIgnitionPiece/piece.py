import os
import fiona
from fiona.crs import from_epsg
from domino.base_piece import BasePiece
from .models import InputModel, OutputModel

class CreateIgnitionPiece(BasePiece):
    
    def piece_function(self, input_data: InputModel):
        self.logger.info(f"Spúšťam generovanie bodu pre súradnice: '{input_data.gps_text}' v EPSG:{input_data.epsg_code.value}")
        
        output_dir = self.results_path 
        os.makedirs(output_dir, exist_ok=True)
        
        output_filename = os.path.join(output_dir, "ignition.shp")

        # 1. Rozparsovanie súradníc z textu
        try:
            # Rozdelí text podľa čiarky a odstráni medzery
            coords = input_data.gps_text.split(',')
            x_coord = float(coords[0].strip())
            y_coord = float(coords[1].strip())
        except Exception as e:
            self.logger.error("Chyba pri čítaní súradníc. Uisti sa, že sú oddelené čiarkou a sú to čísla.")
            raise ValueError(f"Neplatný formát súradníc: {input_data.gps_text}")

        # 2. Načítanie EPSG z výberového menu
        target_epsg = int(input_data.epsg_code.value)

        # 3. Zápis Shapefile súboru
        schema = {
            'geometry': 'Point',
            'properties': {'id': 'int:10'},
        }

        try:
            with fiona.open(
                output_filename,
                'w',
                driver='ESRI Shapefile',
                crs=from_epsg(target_epsg),
                schema=schema
            ) as sink:
                
                point_feature = {
                    'geometry': {'type': 'Point', 'coordinates': (x_coord, y_coord)},
                    'properties': {'id': 1},
                }
                sink.write(point_feature)
                
            self.logger.info(f"Shapefile úspešne vytvorený s EPSG:{target_epsg} na ceste: {output_filename}")
            
        except Exception as e:
            self.logger.error(f"Chyba pri zápise Shapefile: {e}")
            raise RuntimeError(f"Zlyhalo generovanie shapefile súboru: {e}")

        return OutputModel(ignition_shp_path=output_filename)
