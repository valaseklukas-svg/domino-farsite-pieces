from pydantic import BaseModel, Field

class InputModel(BaseModel):
    gps_text: str = Field(
        default="48.18401806101684, 17.073830458190876", 
        description="Vlož GPS súradnice z Google Maps (napr. 48.184, 17.073)."
    )

class OutputModel(BaseModel):
    ignition_shp_path: str = Field(
        ..., 
        description="Cesta k vygenerovanému ignition shapefile v systéme S-JTSK"
    )
