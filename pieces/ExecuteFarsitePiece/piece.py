import os
import shutil
import subprocess
import glob
from pathlib import Path

from domino.base_piece import BasePiece
from .models import InputModel, OutputModel


class ExecuteFarsitePiece(BasePiece):
    """
    Runs FARSITE via /usr/local/bin/run_farsite.sh inside the configured runtime image.

    Expectations (based on our validated docker image):
      - /usr/local/bin/run_farsite.sh exists and is executable
      - it calls TestFARSITE internally and writes <output_base>_runner.log
      - working directory /work exists (we use /work/in and /work/out)
    """

    def _ensure_dir(self, p: str) -> None:
        os.makedirs(p, exist_ok=True)

    def _copy_file(self, src: str, dst_dir: str) -> str:
        self._ensure_dir(dst_dir)
        dst = os.path.join(dst_dir, os.path.basename(src))
        shutil.copy2(src, dst)
        return dst

    def _copy_shapefile_set(self, shp_path: str, dst_dir: str) -> str:
        """
        Copy .shp plus sidecar files sharing the same stem: .dbf, .shx, .prj, .cpg, etc.
        Returns path to copied .shp in dst_dir.
        """
        self._ensure_dir(dst_dir)
        shp = Path(shp_path)
        if shp.suffix.lower() != ".shp":
            raise ValueError(f"Expected .shp, got: {shp_path}")

        stem = shp.with_suffix("")  # remove .shp
        matched = glob.glob(str(stem) + ".*")
        if not matched:
            raise FileNotFoundError(f"No shapefile set found for: {shp_path}")

        for f in matched:
            shutil.copy2(f, os.path.join(dst_dir, os.path.basename(f)))

        return os.path.join(dst_dir, shp.name)

    def piece_function(self, input_data: InputModel):
        work_root = "/work"
        in_dir = os.path.join(work_root, "in")
        out_dir = os.path.join(work_root, "out")

        self._ensure_dir(in_dir)
        self._ensure_dir(out_dir)

        self.logger.info("Copying inputs to /work/in")

        # Mandatory inputs
        lcp_local = self._copy_file(input_data.lcp_path, in_dir)
        inputs_local = self._copy_file(input_data.inputs_path, in_dir)
        ignition_local = self._copy_shapefile_set(input_data.ignition_shp_path, in_dir)

        # Barrier: either "0" or shapefile set
        barrier_arg = "0"
        if input_data.barrier_shp_path and input_data.barrier_shp_path != "0":
            barrier_arg = self._copy_shapefile_set(input_data.barrier_shp_path, in_dir)

        #output_base = os.path.join(out_dir, input_data.output_basename)
        output_base = /work/out/run1
        wrapper = "/usr/local/bin/run_farsite.sh"

        cmd = [
            wrapper,
            lcp_local,
            inputs_local,
            ignition_local,
            barrier_arg,
            output_base,
            str(int(input_data.outputs_type)),
        ]

        self.logger.info("Running wrapper: %s", " ".join(cmd))

        proc = subprocess.run(
            cmd,
            cwd=work_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        # Always persist stdout
        fallback_log = os.path.join(work_root, f"{input_data.output_basename}_stdout.log")
        with open(fallback_log, "w", encoding="utf-8") as f:
            f.write(proc.stdout)

        runner_log = f"{output_base}_runner.log"
        runner_log_path = runner_log if os.path.exists(runner_log) else fallback_log

        if proc.returncode != 0:
            self.logger.error("FARSITE failed. Return code=%s", proc.returncode)
            self.logger.error("See logs: %s and %s", runner_log, fallback_log)
            raise RuntimeError(
                f"FARSITE run failed (rc={proc.returncode}). "
                f"See logs: {runner_log_path} (and {fallback_log})."
            )

        # Zip outputs
        zip_base = os.path.join(work_root, input_data.output_basename + "_outputs")
        zip_path = shutil.make_archive(zip_base, "zip", out_dir)

        self.logger.info("Outputs zipped: %s", zip_path)
        self.logger.info("Runner log: %s", runner_log_path)

        return OutputModel(
            outputs_zip_path=zip_path,
            runner_log_path=runner_log_path,
        )


