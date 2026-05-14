import json
import os
import sys
import tempfile
import webbrowser
from functools import lru_cache
from threading import Timer

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
from werkzeug.exceptions import RequestEntityTooLarge

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
DEFAULT_MAX_UPLOAD_BYTES = 20 * 1024 * 1024
ALLOWED_MIDI_EXTENSIONS = {".mid", ".midi"}
ALLOWED_SAMPLE_RATES = {44100, 48000, 96000}

if PYTHON_RENDERER_DIR not in sys.path:
    sys.path.insert(0, PYTHON_RENDERER_DIR)

import midi_to_wave
import synthesis_jobs


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


def _get_default_max_upload_bytes():
    raw_limit = os.environ.get("WEB_MAX_UPLOAD_BYTES", DEFAULT_MAX_UPLOAD_BYTES)
    try:
        return max(1, int(raw_limit))
    except (TypeError, ValueError):
        return DEFAULT_MAX_UPLOAD_BYTES


app.config["MAX_CONTENT_LENGTH"] = _get_default_max_upload_bytes()


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


def _job_service():
    return synthesis_jobs.SynthesisJobService(
        job_root=_get_job_root(),
        download_ttl_seconds=_get_download_ttl_seconds(),
        run_inline=bool(app.config.get("SYNTHESISE_JOBS_INLINE")),
        logger=app.logger,
    )


def _json_success(payload=None, status_code=200):
    return jsonify(payload or {}), status_code


def _json_accepted(payload):
    return _json_success(payload, 202)


def _json_api_error(code, message, status_code):
    return jsonify({
        "error": {
            "code": code,
            "message": message,
        }
    }), status_code


def _json_legacy_error(message):
    return jsonify({"error": message})


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


def _load_all_translations():
    return {
        locale: _load_translations(locale)
        for locale in SUPPORTED_LOCALES
    }


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


def _parse_sample_rate(form):
    raw_rate = (form.get("rate") or "48000").strip()
    try:
        sample_rate = int(raw_rate)
    except (TypeError, ValueError) as exc:
        raise ValueError("Unsupported sample rate. Choose 44100, 48000, or 96000.") from exc

    if sample_rate not in ALLOWED_SAMPLE_RATES:
        raise ValueError("Unsupported sample rate. Choose 44100, 48000, or 96000.")

    return sample_rate


def _parse_synthesis_options(form):
    sample_rate = _parse_sample_rate(form)
    parsed_layers, runtime_layers = _parse_layers_from_request(form)
    return {
        "sample_rate": sample_rate,
        "parsed_layers": parsed_layers,
        "runtime_layers": runtime_layers,
    }


def _validate_midi_upload(translations):
    if "midi_file" not in request.files:
        return None, _json_legacy_error(translations["errors.no_midi_file_uploaded"]), 400

    uploaded_file = request.files["midi_file"]
    if uploaded_file.filename == "":
        return None, _json_legacy_error(translations["errors.no_selected_file"]), 400

    extension = os.path.splitext(uploaded_file.filename)[1].lower()
    if extension not in ALLOWED_MIDI_EXTENSIONS:
        return None, _json_legacy_error(
            "Unsupported file type. Upload a .mid or .midi file.",
        ), 400

    return uploaded_file, None, None


def _build_original_filename(uploaded_filename):
    if not uploaded_filename:
        return "output"

    return os.path.splitext(os.path.basename(uploaded_filename))[0] or "output"


def _render_uploaded_wav(uploaded_file, form, output_wav_path, options=None):
    options = options or _parse_synthesis_options(form)

    temp_midi = tempfile.NamedTemporaryFile(delete=False, suffix=".mid")
    temp_midi.close()
    try:
        uploaded_file.save(temp_midi.name)
        if os.path.getsize(temp_midi.name) == 0:
            raise ValueError("Uploaded MIDI file is empty.")
        midi_to_wave.midi_to_audio(
            temp_midi.name,
            output_wav_path,
            options["sample_rate"],
            options["parsed_layers"],
        )
    finally:
        try:
            os.unlink(temp_midi.name)
        except FileNotFoundError:
            pass

    original_filename = _build_original_filename(uploaded_file.filename)
    return midi_to_wave.build_output_filename(original_filename, options["runtime_layers"])


def _is_valid_job_id(job_id):
    return synthesis_jobs.is_valid_job_id(job_id)


def _job_dir(job_id):
    return _job_service().job_dir(job_id)


def _job_metadata_path(job_id):
    return _job_service().metadata_path(job_id)


def _write_job_metadata(job_id, metadata):
    _job_service().write_metadata(job_id, metadata)


def _read_job_metadata(job_id):
    return _job_service().read_metadata(job_id)


def _delete_job(job_id):
    _job_service().delete_job(job_id)


def _cleanup_expired_jobs():
    _job_service().cleanup_expired_jobs()


def _job_payload(metadata):
    return _job_service().job_payload(metadata)


def _initial_job_metadata(job_id, uploaded_filename):
    return _job_service().initial_metadata(job_id, uploaded_filename)


def _start_synthesise_job(job_id, input_path, form_payload, uploaded_filename):
    _job_service().start_job(
        job_id,
        input_path,
        form_payload,
        uploaded_filename,
        _render_uploaded_wav,
    )


@app.errorhandler(RequestEntityTooLarge)
def handle_request_entity_too_large(_error):
    message = "Uploaded file is too large."
    if request.path.startswith("/api/"):
        return _json_api_error("upload_too_large", message, 413)
    return _json_legacy_error(message), 413


@app.route("/api/health")
def api_health():
    return _json_success({
        "status": "ok",
        "service": "octabit-web",
    })


@app.route("/")
def index():
    locale, translations, is_explicit_override = _get_locale_context()
    response = make_response(render_template(
        "index.html",
        default_locale=DEFAULT_LOCALE,
        locale=locale,
        locale_cookie_name=LOCALE_COOKIE_NAME,
        supported_locales=SUPPORTED_LOCALES,
        translations_by_locale=_load_all_translations(),
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
    try:
        options = _parse_synthesis_options(request.form)
    except ValueError as exc:
        return _json_legacy_error(str(exc)), 400

    temp_paths = []
    try:
        temp_wav = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        temp_wav.close()
        temp_paths.append(temp_wav.name)
        download_name = _render_uploaded_wav(file, request.form, temp_wav.name, options)

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
        return _json_legacy_error(str(exc)), 400
    except Exception as exc:
        for temp_path in temp_paths:
            try:
                os.unlink(temp_path)
            except FileNotFoundError:
                pass
        return _json_legacy_error(str(exc)), 500


@app.route("/synthesise/jobs", methods=["POST"])
def create_synthesise_job():
    _locale, translations, _is_explicit_override = _get_locale_context()
    file, error_response, status_code = _validate_midi_upload(translations)
    if error_response is not None:
        return error_response, status_code
    try:
        _parse_synthesis_options(request.form)
    except ValueError as exc:
        return _json_legacy_error(str(exc)), 400

    _cleanup_expired_jobs()
    job_service = _job_service()
    job_id, input_path = job_service.prepare_job()

    try:
        file.save(input_path)
        if os.path.getsize(input_path) == 0:
            _delete_job(job_id)
            return _json_legacy_error(translations["errors.empty_midi_file"]), 400
        _write_job_metadata(job_id, _initial_job_metadata(job_id, file.filename))
        _start_synthesise_job(job_id, input_path, request.form.to_dict(flat=True), file.filename)
    except ValueError as exc:
        _delete_job(job_id)
        return _json_legacy_error(str(exc)), 400
    except Exception as exc:
        _delete_job(job_id)
        return _json_legacy_error(str(exc)), 500

    metadata = _read_job_metadata(job_id)
    return _json_accepted(_job_payload(metadata))


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
