from pydantic import BaseModel, Field
from typing import Optional


class InputModel(BaseModel):
    """
    ExecuteFarsitePiece Input Model
    """

    lcp_path: str = Field(..., description="Path to .lcp landscape file")
    inputs_path: str = Field(..., description="Path to FARSITE inputs file (*.input, ASCII format)")
    ignition_shp_path: str = Field(..., description="Path to ignition shapefile (.shp)")
    barrier_shp_path: Optional[str] = Field(
        default="0",
        description="Path to barrier shapefile (.shp) or '0' for no barrier",
    )

    output_basename: str = Field(
        default="farsite_run",
        description="Base name for outputs (no extension). Outputs will be written under /work/out/<output_basename>_*",
    )

    outputs_type: int = Field(
        default=1,
        description="0=both, 1=ASCII grid (recommended baseline), 2=FlamMap binary grid",
    )


class OutputModel(BaseModel):
    """
    ExecuteFarsitePiece Output Model
    """

    outputs_zip_path: str = Field(..., description="ZIP archive containing all output files under /work/out")
    runner_log_path: str = Field(..., description="Runner log path produced by run_farsite.sh (or fallback log)")
