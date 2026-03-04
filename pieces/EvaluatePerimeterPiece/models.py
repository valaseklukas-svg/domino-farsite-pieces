from pydantic import BaseModel, Field

class InputModel(BaseModel):
    outputs_zip_path: str = Field(
        ..., 
        description="Automaticke prepojenie: ZIP archiv z ExecuteFarsitePiece."
    )
    ignition_shp_path: str = Field(
        ..., 
        description="Automaticke prepojenie: Cesta k ignition.shp z CreateIgnitionPiece."
    )
    buffer_shp_path: str = Field(
        ..., 
        description="MANUALNE ZADANIE: Cesta k buffer shapefile na disku (napr. /home/shared_storage/buffer.shp)."
    )
    api_model_name: str = Field(
        default="Model 1", 
        description="MANUALNE ZADANIE: Nazov modelu pre API dicris.sk."
    )

class OutputModel(BaseModel):
    csv_report_path: str = Field(..., description="Cesta k vygenerovanemu CSV reportu.")

    alert_status: str = Field(..., description="Vysledny status odoslany na API (ok, moderate, warning, critical).")
