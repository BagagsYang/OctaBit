import json
import os
import shutil
import sys
import tempfile
import time
import uuid
import webbrowser
from functools import lru_cache
from threading import Thread, Timer

from flask import (
    Flask,
    after_this_request,
    jsonify,
    make_response,
    render_template,
    request,
    send_file,
    send_from_directory,
)

APP_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(APP_DIR))
PYTHON_RENDERER_DIR = os.path.join(REPO_ROOT, "core", "python-renderer")
PREVIEW_ASSETS_DIR = os.path.join(REPO_ROOT, "assets", "previews")
I18N_DIR = os.path.join(APP_DIR, "i18n")
SUPPORTED_LOCALES = ("en", "fr", "zh-CN")
DEFAULT_LOCALE = "en"
LOCALE_COOKIE_NAME = "web_locale"
SUPPORTED_LOCALE_LOOKUP = {
    locale.lower(): locale for locale in SUPPORTED_LOCALES
}
LANGUAGE_FALLBACKS = {
    "zh": "zh-CN",
}
DEFAULT_DOWNLOAD_TTL_SECONDS = 30 * 60
DEFAULT_JOB_ROOT = os.path.join(tempfile.gettempdir(), "octabit-jobs")

if PYTHON_RENDERER_DIR not in sys.path:
    sys.path.insert(0, PYTHON_RENDERER_DIR)

import midi_to_wave


if getattr(sys, "frozen", False):
    template_folder = os.path.join(sys._MEIPASS, "templates")
    static_folder = os.path.join(sys._MEIPASS, "static")
    preview_assets_dir = os.path.join(static_folder, "previews")
    app = Flask(
        __name__,
        template_folder=template_folder,
        static_folder=static_folder,
    )
else:
    preview_assets_dir = PREVIEW_ASSETS_DIR
    app = Flask(
        __name__,
        template_folder=os.path.join(APP_DIR, "templates"),
        static_folder=os.path.join(APP_DIR, "static"),
    )


def open_browser(port=5002):
    webbrowser.open_new(f"http://127.0.0.1:{port}")


def _get_server_port(default=5002):
    try:
        return int(os.environ.get("PORT", default))
    except ValueError:
        return default


def _get_download_ttl_seconds():
    raw_ttl = app.config.get(
        "WEB_DOWNLOAD_TTL_SECONDS",
        os.environ.get("WEB_DOWNLOAD_TTL_SECONDS", DEFAULT_DOWNLOAD_TTL_SECONDS),
    )
    try:
        return max(1, int(raw_ttl))
    except (TypeError, ValueError):
        return DEFAULT_DOWNLOAD_TTL_SECONDS


def _get_job_root():
    return app.config.get(
        "SYNTHESISE_JOB_ROOT",
        os.environ.get("WEB_SYNTHESISE_JOB_ROOT", DEFAULT_JOB_ROOT),
    )


def _normalise_locale(raw_locale):
    if not raw_locale:
        return None

    locale = raw_locale.strip()
    if not locale:
        return None

    lowered = locale.replace("_", "-").lower()
    if lowered in SUPPORTED_LOCALE_LOOKUP:
        return SUPPORTED_LOCALE_LOOKUP[lowered]

    base_language = lowered.split("-", maxsplit=1)[0]
    if base_language in SUPPORTED_LOCALE_LOOKUP:
        return SUPPORTED_LOCALE_LOOKUP[base_language]
    if base_language in LANGUAGE_FALLBACKS:
        return LANGUAGE_FALLBACKS[base_language]

    return None


@lru_cache(maxsize=None)
def _load_translations(locale):
    with open(os.path.join(I18N_DIR, "en.json"), encoding="utf-8") as file:
        translations = json.load(file)

    if locale != DEFAULT_LOCALE:
        locale_path = os.path.join(I18N_DIR, f"{locale}.json")
        if os.path.exists(locale_path):
            with open(locale_path, encoding="utf-8") as file:
                translations.update(json.load(file))

    return translations


def _resolve_locale():
    requested_locale = _normalise_locale(request.args.get("lang"))
    if requested_locale:
        return requested_locale, True

    cookie_locale = _normalise_locale(request.cookies.get(LOCALE_COOKIE_NAME))
    if cookie_locale:
        return cookie_locale, False

    for accepted_locale, _quality in request.accept_languages:
        matched_locale = _normalise_locale(accepted_locale)
        if matched_locale:
            return matched_locale, False

    return DEFAULT_LOCALE, False


def _get_locale_context():
    locale, is_explicit_override = _resolve_locale()
    return locale, _load_translations(locale), is_explicit_override


def _parse_layers_from_request(form):
    layers_json = (form.get("layers_json") or "").strip()
    if not layers_json:
        layers_json = "[]"

    parsed_layers = midi_to_wave.parse_layers_json(layers_json)
    runtime_layers = midi_to_wave.normalise_runtime_layers(parsed_layers)
    return parsed_layers, runtime_layers


def _validate_midi_upload(translations):
    if "midi_file" not in request.files:
        return None, jsonify({"error": translations["errors.no_midi_file_uploaded"]}), 400

    uploaded_file = request.files["midi_file"]
    if uploaded_file.filename == "":
        return None, jsonify({"error": translations["errors.no_selected_file"]}), 400

    return uploaded_file, None, None


def _build_original_filename(uploaded_filename):
    if not uploaded_filename:
        return "output"

    return os.path.splitext(os.path.basename(uploaded_filename))[0] or "output"


def _render_uploaded_wav(uploaded_file, form, output_wav_path):
    sample_rate = int(form.get("rate", 48000))
    parsed_layers, runtime_layers = _parse_layers_from_request(form)

    temp_midi = tempfile.NamedTemporaryFile(delete=False, suffix=".mid")
    temp_midi.close()
    try:
        uploaded_file.save(temp_midi.name)
        midi_to_wave.midi_to_audio(
            temp_midi.name,
            output_wav_path,
            sample_rate,
            parsed_layers,
        )
    finally:
        try:
            os.unlink(temp_midi.name)
        except FileNotFoundError:
            pass

    original_filename = _build_original_filename(uploaded_file.filename)
    return midi_to_wave.build_output_filename(original_filename, runtime_layers)


def _is_valid_job_id(job_id):
    if not isinstance(job_id, str) or len(job_id) != 32:
        return False

    try:
        return uuid.UUID(hex=job_id).hex == job_id
    except ValueError:
        return False


def _job_dir(job_id):
    if not _is_valid_job_id(job_id):
        return None
    return os.path.join(_get_job_root(), job_id)


def _job_metadata_path(job_id):
    job_dir = _job_dir(job_id)
    if job_dir is None:
        return None
    return os.path.join(job_dir, "metadata.json")


def _write_job_metadata(job_id, metadata):
    job_dir = _job_dir(job_id)
    if job_dir is None:
        raise ValueError("Invalid job id")

    os.makedirs(job_dir, exist_ok=True)
    metadata_path = _job_metadata_path(job_id)
    temp_path = os.path.join(job_dir, f"metadata.{uuid.uuid4().hex}.tmp")
    with open(temp_path, "w", encoding="utf-8") as file:
        json.dump(metadata, file, sort_keys=True)
    os.replace(temp_path, metadata_path)


def _read_job_metadata(job_id):
    metadata_path = _job_metadata_path(job_id)
    if metadata_path is None or not os.path.exists(metadata_path):
        return None

    with open(metadata_path, encoding="utf-8") as file:
        metadata = json.load(file)

    expires_at = metadata.get("expires_at")
    if expires_at is not None and time.time() > expires_at:
        _delete_job(job_id)
        return {
            "job_id": job_id,
            "status": "expired",
        }

    return metadata


def _delete_job(job_id):
    job_dir = _job_dir(job_id)
    if job_dir:
        shutil.rmtree(job_dir, ignore_errors=True)


def _cleanup_expired_jobs():
    job_root = _get_job_root()
    if not os.path.isdir(job_root):
        return

    for job_id in os.listdir(job_root):
        if _is_valid_job_id(job_id):
            _read_job_metadata(job_id)


def _job_payload(metadata):
    status = metadata.get("status", "expired")
    payload = {
        "job_id": metadata.get("job_id"),
        "status": status,
    }
    for key in ("created_at", "updated_at", "expires_at", "download_name", "size_bytes", "error"):
        if key in metadata:
            payload[key] = metadata[key]

    if status == "ready":
        payload["download_url"] = f"/synthesise/jobs/{metadata['job_id']}/download"
        payload["delete_url"] = f"/synthesise/jobs/{metadata['job_id']}"

    return payload


def _initial_job_metadata(job_id, uploaded_filename):
    now = time.time()
    return {
        "job_id": job_id,
        "status": "queued",
        "source_name": os.path.basename(uploaded_filename or ""),
        "created_at": now,
        "updated_at": now,
        "expires_at": now + _get_download_ttl_seconds(),
    }


def _update_job_status(job_id, **updates):
    metadata = _read_job_metadata(job_id)
    if metadata is None or metadata.get("status") == "expired":
        return

    metadata.update(updates)
    metadata["updated_at"] = time.time()
    _write_job_metadata(job_id, metadata)


def _run_synthesise_job(job_id, input_path, form_payload, uploaded_filename):
    output_path = os.path.join(_job_dir(job_id), "output.wav")
    _update_job_status(job_id, status="rendering")
    try:
        class SavedUpload:
            filename = uploaded_filename

            def save(self, destination):
                shutil.copyfile(input_path, destination)

        download_name = _render_uploaded_wav(SavedUpload(), form_payload, output_path)
        now = time.time()
        _update_job_status(
            job_id,
            status="ready",
            download_name=download_name,
            size_bytes=os.path.getsize(output_path),
            expires_at=now + _get_download_ttl_seconds(),
        )
    except Exception as exc:
        now = time.time()
        _update_job_status(
            job_id,
            status="failed",
            error=str(exc),
            expires_at=now + _get_download_ttl_seconds(),
        )
    finally:
        try:
            os.unlink(input_path)
        except FileNotFoundError:
            pass


def _start_synthesise_job(job_id, input_path, form_payload, uploaded_filename):
    if app.config.get("SYNTHESISE_JOBS_INLINE"):
        _run_synthesise_job(job_id, input_path, form_payload, uploaded_filename)
        return

    thread = Thread(
        target=_run_synthesise_job,
        args=(job_id, input_path, form_payload, uploaded_filename),
        daemon=True,
    )
    thread.start()


@app.route("/")
def index():
    locale, translations, is_explicit_override = _get_locale_context()
    response = make_response(render_template(
        "index.html",
        default_locale=DEFAULT_LOCALE,
        locale=locale,
        locale_cookie_name=LOCALE_COOKIE_NAME,
        supported_locales=SUPPORTED_LOCALES,
        translations=translations,
    ))

    if is_explicit_override:
        response.set_cookie(
            LOCALE_COOKIE_NAME,
            locale,
            max_age=60 * 60 * 24 * 365,
            samesite="Lax",
        )

    return response


@app.route("/static/previews/<path:filename>")
def preview_asset(filename):
    return send_from_directory(preview_assets_dir, filename)


@app.route("/synthesise", methods=["POST"])
def synthesise():
    _locale, translations, _is_explicit_override = _get_locale_context()

    file, error_response, status_code = _validate_midi_upload(translations)
    if error_response is not None:
        return error_response, status_code

    temp_paths = []
    try:
        temp_wav = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        temp_wav.close()
        temp_paths.append(temp_wav.name)
        download_name = _render_uploaded_wav(file, request.form, temp_wav.name)

        @after_this_request
        def _cleanup_temp_files(response):
            for temp_path in temp_paths:
                try:
                    os.unlink(temp_path)
                except FileNotFoundError:
                    pass
            return response

        return send_file(
            temp_wav.name,
            as_attachment=True,
            download_name=download_name,
        )
    except ValueError as exc:
        for temp_path in temp_paths:
            try:
                os.unlink(temp_path)
            except FileNotFoundError:
                pass
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        for temp_path in temp_paths:
            try:
                os.unlink(temp_path)
            except FileNotFoundError:
                pass
        return jsonify({"error": str(exc)}), 500


@app.route("/synthesise/jobs", methods=["POST"])
def create_synthesise_job():
    _locale, translations, _is_explicit_override = _get_locale_context()
    file, error_response, status_code = _validate_midi_upload(translations)
    if error_response is not None:
        return error_response, status_code

    _cleanup_expired_jobs()
    job_id = uuid.uuid4().hex
    job_dir = _job_dir(job_id)
    os.makedirs(job_dir, exist_ok=True)
    input_path = os.path.join(job_dir, "input.mid")

    try:
        file.save(input_path)
        _write_job_metadata(job_id, _initial_job_metadata(job_id, file.filename))
        _start_synthesise_job(job_id, input_path, request.form.to_dict(flat=True), file.filename)
    except ValueError as exc:
        _delete_job(job_id)
        return jsonify({"error": str(exc)}), 400
    except Exception as exc:
        _delete_job(job_id)
        return jsonify({"error": str(exc)}), 500

    metadata = _read_job_metadata(job_id)
    return jsonify(_job_payload(metadata)), 202


@app.route("/synthesise/jobs/<job_id>", methods=["GET"])
def get_synthesise_job(job_id):
    metadata = _read_job_metadata(job_id)
    if metadata is None:
        return jsonify({"job_id": job_id, "status": "expired"}), 410

    payload = _job_payload(metadata)
    if payload["status"] == "expired":
        return jsonify(payload), 410

    return jsonify(payload)


@app.route("/synthesise/jobs/<job_id>", methods=["DELETE"])
def delete_synthesise_job(job_id):
    _delete_job(job_id)
    return "", 204


@app.route("/synthesise/jobs/<job_id>/download", methods=["GET"])
def download_synthesise_job(job_id):
    metadata = _read_job_metadata(job_id)
    if metadata is None or metadata.get("status") == "expired":
        return jsonify({"job_id": job_id, "status": "expired"}), 410
    if metadata.get("status") == "failed":
        return jsonify(_job_payload(metadata)), 400
    if metadata.get("status") != "ready":
        return jsonify(_job_payload(metadata)), 409

    output_path = os.path.join(_job_dir(job_id), "output.wav")
    if not os.path.exists(output_path):
        _delete_job(job_id)
        return jsonify({"job_id": job_id, "status": "expired"}), 410

    return send_file(
        output_path,
        as_attachment=True,
        download_name=metadata.get("download_name", "output.wav"),
    )


if __name__ == "__main__":
    server_host = os.environ.get("HOST", "127.0.0.1")
    server_port = _get_server_port()
    should_open_browser = os.environ.get("WEB_FLASK_OPEN_BROWSER", "1") != "0"

    if should_open_browser and server_host in ("127.0.0.1", "localhost"):
        Timer(1, lambda: open_browser(server_port)).start()

    print(f"DEBUG: SERVER RUNNING ON {server_host}:{server_port}")
    app.run(host=server_host, port=server_port, debug=False)
