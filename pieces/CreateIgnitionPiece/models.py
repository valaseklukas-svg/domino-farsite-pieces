from pydantic import BaseModel, Field

class InputModel(BaseModel):
    gps_text: str = Field(
        default="49.06565617666292, 18.49023988036085", 
        description="Vloz GPS suradnice z Google Maps (napr. 48.184, 17.073)."
    )

class OutputModel(BaseModel):
    ignition_shp_path: str = Field(
        ..., 
        description="Cesta k vygenerovanemu ignition shapefile v systeme S-JTSK"
    )

