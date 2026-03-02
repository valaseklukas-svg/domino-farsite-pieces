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
        in_dir = os.path.join(work_root, "test")
        out_dir = os.path.join(work_root, "out")

        self._ensure_dir(in_dir)
        self._ensure_dir(out_dir)

        self.logger.info("=== STAHUJEM TESTOVACIE DATA Z GITHUB ===")
        import urllib.request
        
        # Zoznam suborov, ktore treba stiahnut z tvojho GitHubu (raw obsah)
        base_url = "https://raw.githubusercontent.com/valaseklukas-svg/domino-farsite-pieces/main/pieces/ExecuteFarsitePiece/assets/test/"
        
        files_to_download = ["final.lcp", "Zavada.input", "ignition.shp", "ignition.dbf", "ignition.shx", "ignition.prj"]
        
        for filename in files_to_download:
            url = base_url + filename
            dest_path = os.path.join(in_dir, filename)
            self.logger.info(f"Stahujem {filename} do {dest_path}")
            try:
                urllib.request.urlretrieve(url, dest_path)
            except Exception as e:
                self.logger.error(f"Nepodarilo sa stiahnut {filename}: {e}")

        # Ostatok tvojho kodu ostava takmer rovnaky, len prisposobime argumnety...
        # lcp_local, inputs_local, ignition_local už nie je potrebné kopírovať z "input_data", 
        # rovno im priradíme tie cesty, kam sme to práve stiahli.

        lcp_local = os.path.join(in_dir, "final.lcp")
        inputs_local = os.path.join(in_dir, "Zavada.input")
        ignition_local = os.path.join(in_dir, "ignition.shp")
        barrier_arg = "0"
        
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

        return OutputModel(
            outputs_zip_path=zip_path,
            runner_log_path=runner_log_path,
        )
