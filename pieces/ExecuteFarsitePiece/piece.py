import os
import shutil
import subprocess
import glob
from pathlib import Path

from domino.base_piece import BasePiece
from .models import InputModel, OutputModel


class ExecuteFarsitePiece(BasePiece):
    def _ensure_dir(self, p: str) -> None:
        os.makedirs(p, exist_ok=True)

    def _copy_file(self, src: str, dst_dir: str) -> str:
        self._ensure_dir(dst_dir)
        dst = os.path.join(dst_dir, os.path.basename(src))
        shutil.copy2(src, dst)
        return dst

    def _copy_shapefile_set(self, shp_path: str, dst_dir: str) -> str:
        self._ensure_dir(dst_dir)
        shp = Path(shp_path)
        if shp.suffix.lower() != ".shp":
            raise ValueError(f"Expected .shp, got: {shp_path}")

        stem = shp.with_suffix("")
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

        self.logger.info("Kopirujem vstupy do interneho kontajnera: %s", in_dir)

        lcp_local = self._copy_file(input_data.lcp_path, in_dir)
        inputs_local = self._copy_file(input_data.inputs_path, in_dir)
        ignition_local = self._copy_shapefile_set(input_data.ignition_shp_path, in_dir)

        barrier_arg = "0"
        if input_data.barrier_shp_path and input_data.barrier_shp_path != "0":
            barrier_arg = self._copy_shapefile_set(input_data.barrier_shp_path, in_dir)

        output_base = os.path.join(out_dir, input_data.output_basename)
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

        self.logger.info("Spustam FARSITE: %s", " ".join(cmd))

        proc = subprocess.run(
            cmd,
            cwd=work_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        fallback_log = os.path.join(work_root, f"{input_data.output_basename}_stdout.log")
        with open(fallback_log, "w", encoding="utf-8") as f:
            f.write(proc.stdout)

        runner_log = f"{output_base}_runner.log"
        runner_log_path = runner_log if os.path.exists(runner_log) else fallback_log

        # VYPISANIE LOGU DO AIRFLOW
        self.logger.info("=== FARSITE LOG VYPIS ===")
        if os.path.exists(runner_log_path):
            with open(runner_log_path, 'r', encoding='utf-8') as log_file:
                self.logger.info("\n" + log_file.read())
        else:
            self.logger.warning("Log subor sa nenasiel!")
        self.logger.info("==========================")

        if proc.returncode != 0:
            raise RuntimeError(f"FARSITE spadol (rc={proc.returncode}).")

        zip_base = os.path.join(work_root, input_data.output_basename + "_outputs")
        zip_path = shutil.make_archive(zip_base, "zip", out_dir)

        self.logger.info("Vypocet uspesny. ZIP vytvoreny lokalne (bez zdielaneho disku sa strati): %s", zip_path)

        return OutputModel(
            outputs_zip_path=zip_path,
            runner_log_path=runner_log_path,
        )
