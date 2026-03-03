from pydantic import BaseModel, Field
from enum import Enum

# Definícia možností pre rolovacie menu
class EpsgCode(str, Enum):
    wgs84 = "4326"
    sjtsk = "5514"

class InputModel(BaseModel):
    """
    Input model pre fiktívne generovanie Ignition Shapefile
    """
    gps_text: str = Field(
        default="17.1077, 48.1486", 
        description="Súradnice oddelené čiarkou vo formáte X, Y (Lon, Lat pre WGS84 alebo Východ, Sever pre S-JTSK)."
    )
    
    epsg_code: EpsgCode = Field(
        default=EpsgCode.wgs84,
        description="Súradnicový systém (EPSG kód) pre vygenerovaný shapefile."
    )

class OutputModel(BaseModel):
    """
    Output model pre fiktívne generovanie Ignition Shapefile
    """
    ignition_shp_path: str = Field(
        ..., 
        description="Cesta k vygenerovanému (fiktívnemu) ignition shapefile (.shp)"
    )
