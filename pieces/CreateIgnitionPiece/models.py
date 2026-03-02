from pydantic import BaseModel, Field

class InputModel(BaseModel):
    """
    Input model pre fiktívne generovanie Ignition Shapefile
    """
    gps_text: str = Field(
        default="48.1486, 17.1077", 
        description="Fiktívne GPS súradnice na otestovanie workflowu (Lat, Lon)"
    )

class OutputModel(BaseModel):
    """
    Output model pre fiktívne generovanie Ignition Shapefile
    """
    ignition_shp_path: str = Field(
        ..., 
        description="Cesta k vygenerovanému (fiktívnemu) ignition shapefile (.shp)"
    )