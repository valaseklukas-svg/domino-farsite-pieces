from pydantic import BaseModel, Field

class InputModel(BaseModel):
    gps_text: str = Field(
        default="49.066, 18.490", 
        description="Vloz GPS suradnice z Google Maps (napr. 48.184, 17.073)."
    )
    lcp_path: str = Field(
        ..., 
        description="Cesta k .lcp suboru na disku pre kontrolu hranic uzemia (napr. /home/shared_storage/.../final.lcp)."
    )

class OutputModel(BaseModel):
    ignition_shp_path: str = Field(
        ..., 
        description="Cesta k vygenerovanemu ignition shapefile v systeme S-JTSK"
    )


