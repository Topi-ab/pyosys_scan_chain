from pyosys import libyosys as ys

import argparse
import hashlib
import os
import tempfile

from cpp_interface import CppInterface
from scan_chain_core import ScanChainBuilder


class ScanChainApp:
    def _resolve_input(self, design_path: str | None, top: str | None):
        if design_path is not None:
            if top is None:
                raise ValueError("Top module name required when using --design.")
            return design_path, top
        raise ValueError("Design path required. Pass --design and --top.")

    def run(
        self,
        design_path: str | None = None,
        top: str | None = None,
        pre_script: str | None = None,
        post_script: str | None = None,
        log_dir: str | None = None,
        json_path: str | None = None,
    ):
        design = ys.Design()
        design_path, top_name = self._resolve_input(design_path, top)

        if pre_script is None:
            raise ValueError("Pre-scan script required. Pass --pre-script.")
        if post_script is None:
            raise ValueError("Post-scan script required. Pass --post-script.")

        if log_dir is None:
            log_dir = "generated/log"
        os.makedirs(log_dir, exist_ok=True)

        saved_stdout_fd = os.dup(1)
        saved_stderr_fd = os.dup(2)
        try:
            with open(f"{log_dir}/yosys_pre.log", "w") as log_f, \
                open(f"{log_dir}/yosys_pre.err.log", "w") as err_f:
                os.dup2(log_f.fileno(), 1)
                os.dup2(err_f.fileno(), 2)

                ys.run_pass(f"script {pre_script}", design)
        finally:
            os.dup2(saved_stdout_fd, 1)
            os.close(saved_stdout_fd)
            os.dup2(saved_stderr_fd, 2)
            os.close(saved_stderr_fd)

        top_module = design.top_module()

        builder = ScanChainBuilder(design, top_module)
        builder.processTop()

        top_module.check()

        os.makedirs("generated/rtl", exist_ok=True)
        os.makedirs("generated/tmp", exist_ok=True)

        def _hash_design_rtlil():
            fd, path = tempfile.mkstemp(prefix="scan_chain_", suffix=".rtlil", dir="generated/tmp")
            os.close(fd)

            saved_stdout_fd = os.dup(1)
            saved_stderr_fd = os.dup(2)
            try:
                with open(f"{log_dir}/yosys_hash.log", "w") as log_f, \
                    open(f"{log_dir}/yosys_hash.err.log", "w") as err_f:
                    os.dup2(log_f.fileno(), 1)
                    os.dup2(err_f.fileno(), 2)
                    ys.run_pass(f"write_rtlil {path}", design)
            finally:
                os.dup2(saved_stdout_fd, 1)
                os.close(saved_stdout_fd)
                os.dup2(saved_stderr_fd, 2)
                os.close(saved_stderr_fd)

            with open(path, "rb") as f:
                digest = hashlib.sha256(f.read()).digest()
            os.remove(path)
            return int.from_bytes(digest[:8], "big")

        dut_hash = _hash_design_rtlil()
        builder.processTopWrapper(dut_hash)

        saved_stdout_fd = os.dup(1)
        saved_stderr_fd = os.dup(2)
        try:
            with open(f"{log_dir}/yosys_post.log", "w") as log_f, \
                open(f"{log_dir}/yosys_post.err.log", "w") as err_f:
                os.dup2(log_f.fileno(), 1)
                os.dup2(err_f.fileno(), 2)
                ys.run_pass(f"script {post_script}", design)
        finally:
            os.dup2(saved_stdout_fd, 1)
            os.close(saved_stdout_fd)
            os.dup2(saved_stderr_fd, 2)
            os.close(saved_stderr_fd)

        json_data = builder.wrapper

        cpp_header = CppInterface.CreateCppInterface(json_data)
        callers_header = CppInterface.CreateFieldCallersHeader(json_data)

        if json_path is not None:
            os.makedirs(os.path.dirname(json_path) or ".", exist_ok=True)
            with open(json_path, "w") as f:
                f.write(builder.WrapperInfo())

        os.makedirs("generated/include", exist_ok=True)
        with open("generated/include/wrapper_interface.h", "w") as f:
            f.write(cpp_header)
        with open("generated/include/wrapper_field_callers.h", "w") as f:
            f.write(callers_header)


def _parse_args():
    parser = argparse.ArgumentParser(description="Generate scan-chain wrapper and headers.")
    parser.add_argument("--design", help="Path to a SystemVerilog design file.")
    parser.add_argument("--top", help="Top module name for --design.")
    parser.add_argument("--pre-script", help="Yosys script to run before scan-chain insertion.")
    parser.add_argument("--post-script", help="Yosys script to run after scan-chain insertion.")
    parser.add_argument("--log-dir", help="Directory for Yosys logs (defaults to generated/log).")
    parser.add_argument("--json", help="Write wrapper JSON to the given path.")
    return parser.parse_args()


def main():
    args = _parse_args()
    app = ScanChainApp()
    app.run(
        design_path=args.design,
        top=args.top,
        pre_script=args.pre_script,
        post_script=args.post_script,
        log_dir=args.log_dir,
        json_path=args.json,
    )


if __name__ == "__main__":
    main()
