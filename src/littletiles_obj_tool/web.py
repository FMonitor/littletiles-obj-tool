from __future__ import annotations

from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
import sys
import zipfile

from littletiles_obj_tool.bootstrap import setup_local_deps


setup_local_deps()

from flask import Flask, current_app, flash, jsonify, redirect, render_template, request, send_file, url_for

from littletiles_obj_tool.converters import (
    convert_obj_to_snbt,
    convert_old_to_new,
    convert_old_to_obj,
    convert_snbt_to_obj,
)
from littletiles_obj_tool.utils import parse_color_value, rgba_to_signed_argb, rgb_triplet_to_signed_argb


MAX_UPLOAD_SIZE = 32 * 1024 * 1024
DEFAULT_WEB_BLOCK = "littletiles:colored_clean"
LITTLETILES_COLORED_BLOCKS = [
    {"id": "littletiles:colored_clean", "label": "Colored Clean"},
    {"id": "littletiles:colored_floor", "label": "Colored Floor"},
    {"id": "littletiles:colored_grainy_big", "label": "Colored Grainy Big"},
    {"id": "littletiles:colored_grainy", "label": "Colored Grainy"},
    {"id": "littletiles:colored_grainy_low", "label": "Colored Grainy Low"},
    {"id": "littletiles:colored_brick", "label": "Colored Brick"},
    {"id": "littletiles:colored_brick_big", "label": "Colored Brick Big"},
    {"id": "littletiles:colored_bordered", "label": "Colored Bordered"},
    {"id": "littletiles:colored_chiseled", "label": "Colored Chiseled"},
    {"id": "littletiles:colored_broken_brick_big", "label": "Colored Broken Brick Big"},
    {"id": "littletiles:colored_clay", "label": "Colored Clay"},
    {"id": "littletiles:colored_strips", "label": "Colored Strips"},
    {"id": "littletiles:colored_gravel", "label": "Colored Gravel"},
    {"id": "littletiles:colored_sand", "label": "Colored Sand"},
    {"id": "littletiles:colored_stone", "label": "Colored Stone"},
    {"id": "littletiles:colored_cork", "label": "Colored Cork"},
    {"id": "littletiles:colored_water", "label": "Colored Water"},
    {"id": "littletiles:colored_lava", "label": "Colored Lava"},
    {"id": "littletiles:colored_white_lava", "label": "Colored White Lava"},
]


def get_resource_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    return Path(__file__).resolve().parent


def create_app() -> Flask:
    resource_root = get_resource_root()
    app = Flask(
        __name__,
        template_folder=str(resource_root / "templates"),
        static_folder=str(resource_root / "static"),
    )
    app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_SIZE
    app.secret_key = "lt-obj-tool-local"

    @app.get("/")
    def index():
        return render_template(
            "index.html",
            block_options=LITTLETILES_COLORED_BLOCKS,
            default_block=DEFAULT_WEB_BLOCK,
            auto_exit_on_browser_close=bool(app.config.get("AUTO_EXIT_ON_BROWSER_CLOSE", False)),
        )

    @app.post("/convert")
    def convert():
        mode = request.form.get("mode", "")
        upload = request.files.get("input_file")
        if not upload or not upload.filename:
            flash("Missing input file.")
            return redirect(url_for("index"))

        try:
            return execute_conversion(mode, upload)
        except Exception as exc:  # pragma: no cover
            flash(str(exc))
            return redirect(url_for("index"))

    @app.post("/api/convert")
    def api_convert():
        mode = request.form.get("mode", "")
        upload = request.files.get("input_file")
        if not upload or not upload.filename:
            return jsonify({"error": "Missing input file."}), 400

        try:
            return execute_conversion(mode, upload)
        except Exception as exc:  # pragma: no cover
            return jsonify({"error": str(exc)}), 400

    @app.post("/preview")
    def preview():
        mode = request.form.get("mode", "")
        upload = request.files.get("input_file")
        if not upload or not upload.filename:
            return jsonify({"error": "Missing input file."}), 400

        with TemporaryDirectory() as tmp:
            tmpdir = Path(tmp)
            suffix = ".obj" if mode == "obj-to-snbt" else ".snbt"
            input_path = tmpdir / f"preview_input{suffix}"
            input_path.write_bytes(upload.read())

            try:
                payload = build_preview_payload(mode, input_path)
            except Exception as exc:  # pragma: no cover
                return jsonify({"error": str(exc)}), 400
            return jsonify(payload)

    @app.post("/api/client/heartbeat")
    def client_heartbeat():
        if current_app.config.get("AUTO_EXIT_ON_BROWSER_CLOSE"):
            session_monitor = current_app.extensions.get("desktop_session_monitor")
            if session_monitor is not None:
                session_monitor.note_heartbeat()
        return ("", 204)

    return app


def parse_form_color() -> int:
    color_hex = request.form.get("color_hex")
    alpha = request.form.get("color_a")
    if color_hex and alpha not in (None, ""):
        rgb = color_hex.lstrip("#")
        if len(rgb) != 6:
            raise ValueError(f"Invalid RGB hex color: {color_hex}")
        return rgba_to_signed_argb(int(rgb[0:2], 16), int(rgb[2:4], 16), int(rgb[4:6], 16), int(alpha))

    if color_hex:
        return parse_color_value(color_hex=color_hex)

    rgb_values = [request.form.get("color_r"), request.form.get("color_g"), request.form.get("color_b")]
    if all(value not in (None, "") for value in rgb_values):
        if alpha not in (None, ""):
            return rgba_to_signed_argb(int(rgb_values[0]), int(rgb_values[1]), int(rgb_values[2]), int(alpha))
        return rgb_triplet_to_signed_argb(int(rgb_values[0]), int(rgb_values[1]), int(rgb_values[2]))

    return parse_color_value(color=-1)


def execute_conversion(mode, upload):
    with TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        suffix = ".obj" if mode == "obj-to-snbt" else ".snbt"
        input_path = tmpdir / f"input{suffix}"
        input_path.write_bytes(upload.read())

        if mode == "old-to-new":
            output_path = tmpdir / "converted_1_20.snbt"
            convert_old_to_new(input_path, output_path)
            return send_download(output_path)

        if mode == "old-to-obj":
            output_obj = tmpdir / "converted.obj"
            convert_old_to_obj(input_path, output_obj)
            return send_file(build_zip([output_obj, output_obj.with_suffix(".mtl")]), as_attachment=True, download_name="converted_obj.zip")

        if mode == "snbt-to-obj":
            output_obj = tmpdir / "converted.obj"
            convert_snbt_to_obj(input_path, output_obj)
            return send_file(build_zip([output_obj, output_obj.with_suffix(".mtl")]), as_attachment=True, download_name="converted_obj.zip")

        if mode == "obj-to-snbt":
            output_path = tmpdir / "converted_1_20.snbt"
            color = parse_form_color()
            convert_obj_to_snbt(
                input_path,
                output_path,
                grid=int(request.form.get("grid", 16)),
                max_size=int(request.form.get("max_size", 16)),
                block=request.form.get("block", DEFAULT_WEB_BLOCK),
                color=color,
            )
            return send_download(output_path)

    raise ValueError(f"Unsupported mode: {mode}")


def build_preview_payload(mode: str, input_path: Path) -> dict[str, str]:
    if mode in {"old-to-new", "old-to-obj"}:
        return build_snbt_preview_payload(input_path, old=True)

    if mode == "snbt-to-obj":
        return build_snbt_preview_payload(input_path, old=False)

    if mode == "obj-to-snbt":
        color = parse_form_color()
        color_hex = request.form.get("color_hex", "#ffffff")
        return {
            "kind": "obj",
            "obj": input_path.read_text(encoding="utf-8", errors="replace"),
            "color_hex": color_hex,
            "color_value": str(color),
            "color_alpha": request.form.get("color_a", "255"),
        }

    raise ValueError(f"Unsupported preview mode: {mode}")


def build_snbt_preview_payload(input_path: Path, old: bool) -> dict[str, str]:
    with TemporaryDirectory() as preview_tmp:
        preview_dir = Path(preview_tmp)
        output_obj = preview_dir / "preview.obj"
        if old:
            convert_old_to_obj(input_path, output_obj)
        else:
            convert_snbt_to_obj(input_path, output_obj)

        output_mtl = output_obj.with_suffix(".mtl")
        return {
            "kind": "obj_mtl",
            "obj": output_obj.read_text(encoding="utf-8"),
            "mtl": output_mtl.read_text(encoding="utf-8"),
        }


def build_zip(paths: list[Path]) -> BytesIO:
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in paths:
            zf.write(path, arcname=path.name)
    buffer.seek(0)
    return buffer


def send_download(path: Path):
    return send_file(BytesIO(path.read_bytes()), as_attachment=True, download_name=path.name)


def main(host: str = "127.0.0.1", port: int = 8765, debug: bool = False) -> None:
    app = create_app()
    app.run(host=host, port=port, debug=debug)
