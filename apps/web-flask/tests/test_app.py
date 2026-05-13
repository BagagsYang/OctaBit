import io
import json
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

import pretty_midi

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app as web_app


class WebFlaskSynthesiseTests(unittest.TestCase):
    def setUp(self):
        web_app.app.testing = True
        self._original_job_config = {
            "SYNTHESISE_JOB_ROOT": web_app.app.config.get("SYNTHESISE_JOB_ROOT"),
            "SYNTHESISE_JOBS_INLINE": web_app.app.config.get("SYNTHESISE_JOBS_INLINE"),
            "WEB_DOWNLOAD_TTL_SECONDS": web_app.app.config.get("WEB_DOWNLOAD_TTL_SECONDS"),
        }
        self.job_root = tempfile.TemporaryDirectory()
        self.addCleanup(self.job_root.cleanup)
        self.addCleanup(self._restore_job_config)
        web_app.app.config["SYNTHESISE_JOB_ROOT"] = self.job_root.name
        web_app.app.config["SYNTHESISE_JOBS_INLINE"] = True
        web_app.app.config["WEB_DOWNLOAD_TTL_SECONDS"] = 1800
        self.client = web_app.app.test_client()

    def _restore_job_config(self):
        for key, value in self._original_job_config.items():
            if value is None:
                web_app.app.config.pop(key, None)
            else:
                web_app.app.config[key] = value

    def test_index_falls_back_to_english(self):
        response = self.client.get("/", headers={"Accept-Language": "de-DE,de;q=0.9"})
        self.addCleanup(response.close)

        self.assertEqual(200, response.status_code)
        self.assertIn('<html lang="en"', response.get_data(as_text=True))
        self.assertIn("OctaBit", response.get_data(as_text=True))
        self.assertIn("Current File(s)", response.get_data(as_text=True))

    def test_index_uses_browser_language_for_french(self):
        response = self.client.get("/", headers={"Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8"})
        self.addCleanup(response.close)

        self.assertEqual(200, response.status_code)
        body = response.get_data(as_text=True)
        self.assertIn('<html lang="fr"', body)
        self.assertIn("Fichier(s) actuel(s)", body)
        self.assertIn("Traiter et télécharger", body)
        self.assertIn('value="fr" data-i18n="toolbar.language_option.fr" selected', body)
        self.assertIn("Français", body)

    def test_index_uses_browser_language_for_simplified_chinese(self):
        response = self.client.get("/", headers={"Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"})
        self.addCleanup(response.close)

        self.assertEqual(200, response.status_code)
        body = response.get_data(as_text=True)
        self.assertIn('<html lang="zh-CN"', body)
        self.assertIn("当前文件", body)
        self.assertIn("采样率", body)

    def test_index_query_parameter_overrides_browser_language(self):
        response = self.client.get("/?lang=fr", headers={"Accept-Language": "zh-CN,zh;q=0.9"})
        self.addCleanup(response.close)

        self.assertEqual(200, response.status_code)
        self.assertIn("Fichier(s) actuel(s)", response.get_data(as_text=True))
        self.assertIn("web_locale=fr", response.headers.get("Set-Cookie", ""))

    def test_index_renders_theme_select_with_language_select(self):
        response = self.client.get("/")
        self.addCleanup(response.close)

        body = response.get_data(as_text=True)
        self.assertIn("OctaBit", body)
        self.assertIn("OctaBit – MIDI to 8-bit Converter", body)
        self.assertIn("https://octabit.cc/", body)
        self.assertIn("Converted Files", body)
        self.assertIn('id="convertedList"', body)
        self.assertIn('id="themeSelect"', body)
        self.assertIn('class="theme-select-frame"', body)
        self.assertIn('id="themeSelectIcon"', body)
        self.assertLess(body.index('id="themeSelectIcon"'), body.index('id="themeSelect"'))
        self.assertIn('aria-label="Theme"', body)
        self.assertIn('id="languageSelect"', body)
        self.assertIn('class="language-select-frame"', body)
        self.assertIn('class="language-select-icon"', body)
        self.assertLess(body.index('class="language-select-icon"'), body.index('id="languageSelect"'))
        self.assertLess(body.index('id="themeSelect"'), body.index('id="languageSelect"'))
        self.assertIn('<option value="system" data-i18n="settings.theme_system">System</option>', body)
        self.assertIn('<option value="light" data-i18n="settings.theme_light">Light</option>', body)
        self.assertIn('<option value="dark" data-i18n="settings.theme_dark">Dark</option>', body)
        self.assertIn("Theme", body)
        self.assertIn("Light", body)
        self.assertIn("Dark", body)
        self.assertIn("System", body)
        self.assertIn('class="module output-module"', body)
        self.assertIn('id="octabit-config"', body)
        self.assertIn('"translationsByLocale"', body)
        self.assertIn('data-i18n="queue.title"', body)
        self.assertIn("/static/js/theme-init.js", body)
        self.assertIn("/static/css/app.css", body)
        self.assertIn("/static/js/lucide-icons.js", body)
        self.assertIn("/static/js/app.js", body)
        self.assertLess(body.index("/static/js/theme-init.js"), body.index("/static/css/app.css"))
        self.assertLess(body.index("/static/js/lucide-icons.js"), body.index("/static/js/app.js"))
        self.assertIn("Process &amp; Download", body)
        self.assertIn(
            "Clearing converted files deletes the temporary WAV files from the server, "
            "so they cannot be retained or downloaded again.",
            body,
        )
        self.assertNotIn("<style>", body)
        self.assertNotIn('class="action-rail"', body)
        self.assertNotIn('id="settingsPlaceholderBtn"', body)
        self.assertNotIn('id="settingsButton"', body)
        self.assertNotIn('id="settingsDialog"', body)
        self.assertNotIn('name="themeChoice"', body)
        self.assertNotIn('id="themeToggle"', body)
        self.assertNotIn('id="followSystemThemeToggle"', body)

    def test_static_browser_script_preserves_interaction_hooks(self):
        response = self.client.get("/static/js/app.js")
        self.addCleanup(response.close)

        body = response.get_data(as_text=True)
        self.assertEqual(200, response.status_code)
        self.assertIn("document.getElementById('octabit-config')", body)
        self.assertIn("translateStaticSurface", body)
        self.assertIn("TRANSLATIONS_BY_LOCALE[nextLocale]", body)
        self.assertIn("window.history.replaceState", body)
        self.assertNotIn("persistLanguageSwitchState", body)
        self.assertNotIn("restoreLanguageSwitchState", body)
        self.assertNotIn("pendingLanguageSwitchState", body)
        self.assertIn("SUPPORTED_LOCALES.includes(selectedLocale)", body)
        self.assertIn("window.confirm(t('converted.clear_confirm'))", body)
        self.assertIn("layer-control-grid", body)
        self.assertIn("document.getElementById('themeSelect')", body)
        self.assertIn("document.getElementById('themeSelectIcon')", body)
        self.assertIn("document.querySelector('.language-select-icon')", body)
        self.assertIn("window.octabitLucideIcons", body)
        self.assertIn("ICONS.svg('languages'", body)
        self.assertIn("ICONS.svg('x')", body)
        self.assertIn("ICONS.svg('play')", body)
        self.assertIn("ICONS.svg(selectedThemeIconName()", body)
        self.assertIn("'sun'", body)
        self.assertIn("'moon-star'", body)
        self.assertIn("activeThemeValue() === 'light' ? 'sun' : 'moon-star'", body)
        self.assertIn("octabitTheme", body)
        self.assertIn("localStorage.setItem(THEME_STORAGE_KEY, theme)", body)
        self.assertIn("localStorage.removeItem(THEME_STORAGE_KEY)", body)
        self.assertIn("themeSelect.value === 'system'", body)
        self.assertIn("prefers-color-scheme: dark", body)
        self.assertIn("prefers-color-scheme: light", body)
        self.assertIn("applyTheme();", body)
        self.assertNotIn("htmlElement.setAttribute('data-bs-theme', 'dark')", body)
        self.assertNotIn("themeToggle", body)
        self.assertNotIn("settingsButton", body)
        self.assertNotIn("settingsDialog", body)
        self.assertNotIn("themeChoice", body)
        self.assertNotIn("followSystemThemeToggle", body)
        self.assertNotIn("updateThemeIcon", body)
        self.assertNotIn("removeButton.textContent = 'x'", body)
        self.assertNotIn("play-icon", body)

    def test_lucide_icon_helper_exposes_vendored_inline_svgs(self):
        response = self.client.get("/static/js/lucide-icons.js")
        self.addCleanup(response.close)

        body = response.get_data(as_text=True)
        self.assertEqual(200, response.status_code)
        self.assertIn("window.octabitLucideIcons", body)
        self.assertIn("License: ISC License", body)
        self.assertIn("languages:", body)
        self.assertIn("'moon-star':", body)
        self.assertIn("play:", body)
        self.assertIn("sun:", body)
        self.assertIn("x:", body)
        self.assertIn('aria-hidden="true"', body)
        self.assertIn('focusable="false"', body)

    def test_app_css_uses_lucide_icon_rule_not_css_triangle(self):
        response = self.client.get("/static/css/app.css")
        self.addCleanup(response.close)

        body = response.get_data(as_text=True)
        self.assertEqual(200, response.status_code)
        self.assertIn(".lucide-icon", body)
        self.assertNotIn(".play-icon", body)
        self.assertNotIn("border-left: 10px solid currentColor", body)

    def test_toolbar_theme_and_language_selects_do_not_show_focus_halo(self):
        response = self.client.get("/static/css/app.css")
        self.addCleanup(response.close)

        body = response.get_data(as_text=True)
        self.assertEqual(200, response.status_code)
        self.assertIn(".theme-select:focus,\n.language-select:focus", body)
        self.assertIn("box-shadow: none;", body)
        self.assertIn(".theme-select:focus-visible,\n.language-select:focus-visible", body)
        self.assertIn("outline: none;", body)
        self.assertIn(".control-select:focus", body)
        self.assertIn("box-shadow: 0 0 0 2px var(--accent-ring);", body)

    def test_theme_select_icon_preserves_control_width(self):
        response = self.client.get("/static/css/app.css")
        self.addCleanup(response.close)

        body = response.get_data(as_text=True)
        self.assertEqual(200, response.status_code)
        self.assertIn(".theme-select-frame", body)
        self.assertIn("width: 136px;", body)
        self.assertIn("flex: 0 0 136px;", body)
        self.assertIn(".theme-select-icon", body)
        self.assertIn("position: absolute;", body)
        self.assertIn("pointer-events: none;", body)
        self.assertIn("padding-left: 36px;", body)

    def test_language_select_icon_matches_theme_icon_position(self):
        response = self.client.get("/static/css/app.css")
        self.addCleanup(response.close)

        body = response.get_data(as_text=True)
        self.assertEqual(200, response.status_code)
        self.assertIn(".theme-select-frame,\n.language-select-frame", body)
        self.assertIn(".theme-select,\n.language-select {\n    width: 100%;", body)
        self.assertIn(".theme-select-icon,\n.language-select-icon", body)
        self.assertIn(".theme-select-icon .lucide-icon,\n.language-select-icon .lucide-icon", body)
        self.assertIn("width: 136px;", body)
        self.assertIn("flex: 0 0 136px;", body)
        self.assertIn("left: 12px;", body)

    def test_theme_init_script_resolves_stored_or_system_theme(self):
        response = self.client.get("/static/js/theme-init.js")
        self.addCleanup(response.close)

        body = response.get_data(as_text=True)
        self.assertEqual(200, response.status_code)
        self.assertIn("octabitTheme", body)
        self.assertIn("THEME_STORAGE_KEY = 'octabitTheme'", body)
        self.assertIn("THEME_VALUES = ['light', 'dark']", body)
        self.assertIn("THEME_VALUES.includes(value)", body)
        self.assertIn("localStorage.getItem(THEME_STORAGE_KEY)", body)
        self.assertIn("prefers-color-scheme: dark", body)
        self.assertIn("prefers-color-scheme: light", body)
        self.assertIn("data-bs-theme", body)

    def test_supported_locale_catalogs_have_matching_keys(self):
        base_keys = set(self._load_catalog(web_app.DEFAULT_LOCALE))
        self.assertEqual(
            {"en", "fr", "zh-CN"},
            set(web_app.SUPPORTED_LOCALES),
        )

        for locale in web_app.SUPPORTED_LOCALES:
            with self.subTest(locale=locale):
                self.assertEqual(base_keys, set(self._load_catalog(locale)))

    def test_synthesise_localises_missing_file_error_from_cookie(self):
        self.client.set_cookie(web_app.LOCALE_COOKIE_NAME, "zh-CN")
        response = self.client.post(
            "/synthesise",
            data={},
            content_type="multipart/form-data",
        )
        self.addCleanup(response.close)

        self.assertEqual(400, response.status_code)
        self.assertEqual("未上传 MIDI 文件", response.get_json()["error"])

    def test_synthesise_localises_missing_file_error_from_french_cookie(self):
        self.client.set_cookie(web_app.LOCALE_COOKIE_NAME, "fr")
        response = self.client.post(
            "/synthesise",
            data={},
            content_type="multipart/form-data",
        )
        self.addCleanup(response.close)

        self.assertEqual(400, response.status_code)
        self.assertEqual("Aucun fichier MIDI envoyé", response.get_json()["error"])

    def test_synthesise_rejects_empty_midi_file(self):
        response = self.client.post(
            "/synthesise",
            data={
                "rate": "16000",
                "midi_file": (io.BytesIO(b""), "empty.mid"),
            },
            content_type="multipart/form-data",
        )
        self.addCleanup(response.close)

        self.assertEqual(400, response.status_code)
        self.assertEqual("Uploaded MIDI file is empty.", response.get_json()["error"])

    def test_synthesise_accepts_layers_json_and_returns_wav(self):
        response = self.client.post(
            "/synthesise",
            data={
                "rate": "16000",
                "layers_json": json.dumps([{
                    "type": "sine",
                    "duty": 0.5,
                    "volume": 1.0,
                    "frequency_curve": [],
                }]),
                "midi_file": (io.BytesIO(self._build_midi_bytes()), "lead.mid"),
            },
            content_type="multipart/form-data",
        )
        self.addCleanup(response.close)

        self.assertEqual(200, response.status_code)
        self.assertEqual(b"RIFF", response.data[:4])
        self.assertIn("attachment;", response.headers["Content-Disposition"])
        self.assertIn("lead_sine.wav", response.headers["Content-Disposition"])

    def test_synthesise_job_rejects_empty_midi_before_starting_job(self):
        response = self.client.post(
            "/synthesise/jobs?lang=zh-CN",
            data={
                "rate": "16000",
                "midi_file": (io.BytesIO(b""), "empty.mid"),
            },
            content_type="multipart/form-data",
        )
        self.addCleanup(response.close)

        self.assertEqual(400, response.status_code)
        self.assertEqual(
            "上传的 MIDI 文件为空。请重新添加原始文件后再试。",
            response.get_json()["error"],
        )
        self.assertEqual([], list(Path(self.job_root.name).iterdir()))

    def test_synthesise_job_returns_ready_status_and_download(self):
        response = self.client.post(
            "/synthesise/jobs",
            data={
                "rate": "16000",
                "layers_json": json.dumps([{
                    "type": "sine",
                    "duty": 0.5,
                    "volume": 1.0,
                    "frequency_curve": [],
                }]),
                "midi_file": (io.BytesIO(self._build_midi_bytes()), "lead.mid"),
            },
            content_type="multipart/form-data",
        )
        self.addCleanup(response.close)

        self.assertEqual(202, response.status_code)
        payload = response.get_json()
        self.assertEqual("ready", payload["status"])
        self.assertEqual("lead_sine.wav", payload["download_name"])
        self.assertGreater(payload["size_bytes"], 4)
        self.assertIn("/synthesise/jobs/", payload["download_url"])
        self.assertIn("/synthesise/jobs/", payload["delete_url"])

        status_response = self.client.get(f"/synthesise/jobs/{payload['job_id']}")
        self.addCleanup(status_response.close)
        self.assertEqual(200, status_response.status_code)
        self.assertEqual("ready", status_response.get_json()["status"])

        download_response = self.client.get(payload["download_url"])
        self.addCleanup(download_response.close)
        self.assertEqual(200, download_response.status_code)
        self.assertEqual(b"RIFF", download_response.data[:4])
        self.assertIn("attachment;", download_response.headers["Content-Disposition"])
        self.assertIn("lead_sine.wav", download_response.headers["Content-Disposition"])

    def test_synthesise_job_delete_removes_ready_download(self):
        response = self.client.post(
            "/synthesise/jobs",
            data={
                "rate": "16000",
                "layers_json": json.dumps([{
                    "type": "sine",
                    "duty": 0.5,
                    "volume": 1.0,
                    "frequency_curve": [],
                }]),
                "midi_file": (io.BytesIO(self._build_midi_bytes()), "lead.mid"),
            },
            content_type="multipart/form-data",
        )
        self.addCleanup(response.close)

        payload = response.get_json()
        output_path = Path(web_app._job_dir(payload["job_id"])) / "output.wav"
        self.assertTrue(output_path.exists())

        delete_response = self.client.delete(payload["delete_url"])
        self.addCleanup(delete_response.close)
        self.assertEqual(204, delete_response.status_code)
        self.assertFalse(output_path.exists())

        status_response = self.client.get(f"/synthesise/jobs/{payload['job_id']}")
        self.addCleanup(status_response.close)
        self.assertEqual(410, status_response.status_code)
        self.assertEqual("expired", status_response.get_json()["status"])

        download_response = self.client.get(payload["download_url"])
        self.addCleanup(download_response.close)
        self.assertEqual(410, download_response.status_code)
        self.assertEqual("expired", download_response.get_json()["status"])

    def test_synthesise_job_reports_failed_status(self):
        with self.assertLogs(web_app.app.logger.name, level="WARNING") as logs:
            response = self.client.post(
                "/synthesise/jobs",
                data={
                    "rate": "16000",
                    "layers_json": json.dumps([{
                        "type": "sine",
                        "duty": 0.5,
                        "volume": 1.0,
                        "frequency_curve": [
                            {"frequency_hz": 440.0, "gain_db": 0.0},
                            {"frequency_hz": 440.0, "gain_db": -6.0},
                        ],
                    }]),
                    "midi_file": (io.BytesIO(self._build_midi_bytes()), "lead.mid"),
                },
                content_type="multipart/form-data",
            )
            self.addCleanup(response.close)

        self.assertEqual(202, response.status_code)
        payload = response.get_json()
        self.assertEqual("failed", payload["status"])
        self.assertIn("strictly increasing", payload["error"])
        self.assertTrue(any("strictly increasing" in message for message in logs.output))

        download_response = self.client.get(f"/synthesise/jobs/{payload['job_id']}/download")
        self.addCleanup(download_response.close)
        self.assertEqual(400, download_response.status_code)
        self.assertEqual("failed", download_response.get_json()["status"])

    def test_synthesise_job_reports_exception_type_for_empty_error(self):
        with (
            mock.patch.object(web_app, "_render_uploaded_wav", side_effect=MemoryError()),
            self.assertLogs(web_app.app.logger.name, level="ERROR") as logs,
        ):
            response = self.client.post(
                "/synthesise/jobs",
                data={
                    "rate": "16000",
                    "layers_json": json.dumps([{
                        "type": "sine",
                        "duty": 0.5,
                        "volume": 1.0,
                        "frequency_curve": [],
                    }]),
                    "midi_file": (io.BytesIO(self._build_midi_bytes()), "lead.mid"),
                },
                content_type="multipart/form-data",
            )
            self.addCleanup(response.close)

        self.assertEqual(202, response.status_code)
        payload = response.get_json()
        self.assertEqual("failed", payload["status"])
        self.assertEqual("MemoryError: synthesis ran out of memory", payload["error"])
        self.assertTrue(any("Synthesis job" in message for message in logs.output))

    def test_synthesise_job_missing_or_expired_returns_expired(self):
        missing_response = self.client.get(f"/synthesise/jobs/{'0' * 32}")
        self.addCleanup(missing_response.close)
        self.assertEqual(410, missing_response.status_code)
        self.assertEqual("expired", missing_response.get_json()["status"])

        response = self.client.post(
            "/synthesise/jobs",
            data={
                "rate": "16000",
                "layers_json": json.dumps([{
                    "type": "sine",
                    "duty": 0.5,
                    "volume": 1.0,
                    "frequency_curve": [],
                }]),
                "midi_file": (io.BytesIO(self._build_midi_bytes()), "lead.mid"),
            },
            content_type="multipart/form-data",
        )
        self.addCleanup(response.close)
        payload = response.get_json()
        metadata = web_app._read_job_metadata(payload["job_id"])
        metadata["expires_at"] = time.time() - 1
        web_app._write_job_metadata(payload["job_id"], metadata)

        expired_response = self.client.get(f"/synthesise/jobs/{payload['job_id']}")
        self.addCleanup(expired_response.close)
        self.assertEqual(410, expired_response.status_code)
        self.assertEqual("expired", expired_response.get_json()["status"])

    def test_synthesise_rejects_invalid_curve_payload(self):
        response = self.client.post(
            "/synthesise",
            data={
                "rate": "16000",
                "layers_json": json.dumps([{
                    "type": "sine",
                    "duty": 0.5,
                    "volume": 1.0,
                    "frequency_curve": [
                        {"frequency_hz": 440.0, "gain_db": 0.0},
                        {"frequency_hz": 440.0, "gain_db": -6.0},
                    ],
                }]),
                "midi_file": (io.BytesIO(self._build_midi_bytes()), "lead.mid"),
            },
            content_type="multipart/form-data",
        )
        self.addCleanup(response.close)

        self.assertEqual(400, response.status_code)
        self.assertIn("strictly increasing", response.get_json()["error"])

    def test_synthesise_uses_curve_hash_in_download_name(self):
        layers = [{
            "type": "sine",
            "duty": 0.5,
            "volume": 1.0,
            "frequency_curve": [
                {"frequency_hz": 261.6255653006, "gain_db": -12.0},
                {"frequency_hz": 1046.5022612024, "gain_db": 0.0},
            ],
        }]
        runtime_layers = web_app.midi_to_wave.normalise_runtime_layers(
            web_app.midi_to_wave.parse_layers_json(json.dumps(layers))
        )
        expected_name = web_app.midi_to_wave.build_output_filename("lead", runtime_layers)

        response = self.client.post(
            "/synthesise",
            data={
                "rate": "16000",
                "layers_json": json.dumps(layers),
                "midi_file": (io.BytesIO(self._build_midi_bytes()), "lead.mid"),
            },
            content_type="multipart/form-data",
        )
        self.addCleanup(response.close)

        self.assertEqual(200, response.status_code)
        self.assertIn(expected_name, response.headers["Content-Disposition"])

    def test_synthesise_accepts_four_layer_mix(self):
        response = self.client.post(
            "/synthesise",
            data={
                "rate": "16000",
                "layers_json": json.dumps([
                    {
                        "type": "pulse",
                        "duty": 0.5,
                        "volume": 1.0,
                        "frequency_curve": [],
                    },
                    {
                        "type": "sine",
                        "duty": 0.5,
                        "volume": 0.5,
                        "frequency_curve": [],
                    },
                    {
                        "type": "triangle",
                        "duty": 0.5,
                        "volume": 0.5,
                        "frequency_curve": [],
                    },
                    {
                        "type": "sawtooth",
                        "duty": 0.5,
                        "volume": 0.5,
                        "frequency_curve": [],
                    },
                ]),
                "midi_file": (io.BytesIO(self._build_midi_bytes()), "lead.mid"),
            },
            content_type="multipart/form-data",
        )
        self.addCleanup(response.close)

        self.assertEqual(200, response.status_code)
        self.assertEqual(b"RIFF", response.data[:4])
        self.assertIn("lead_mix.wav", response.headers["Content-Disposition"])

    def test_synthesise_accepts_rounded_web_curve_endpoints(self):
        response = self.client.post(
            "/synthesise",
            data={
                "rate": "16000",
                "layers_json": json.dumps([{
                    "type": "sine",
                    "duty": 0.5,
                    "volume": 1.0,
                    "frequency_curve": [
                        {"frequency_hz": 8.1757989156, "gain_db": 0.0},
                        {"frequency_hz": 12543.8539514, "gain_db": 0.0},
                    ],
                }]),
                "midi_file": (io.BytesIO(self._build_midi_bytes()), "lead.mid"),
            },
            content_type="multipart/form-data",
        )
        self.addCleanup(response.close)

        self.assertEqual(200, response.status_code)
        self.assertEqual(b"RIFF", response.data[:4])

    def _build_midi_bytes(self):
        midi = pretty_midi.PrettyMIDI()
        instrument = pretty_midi.Instrument(program=0)
        instrument.notes.append(pretty_midi.Note(
            velocity=100,
            pitch=69,
            start=0.0,
            end=0.5,
        ))
        midi.instruments.append(instrument)

        with tempfile.TemporaryDirectory() as temp_dir:
            midi_path = Path(temp_dir) / "test.mid"
            midi.write(str(midi_path))
            return midi_path.read_bytes()

    def _load_catalog(self, locale):
        catalog_path = Path(web_app.I18N_DIR) / f"{locale}.json"
        with catalog_path.open(encoding="utf-8") as file:
            return json.load(file)


if __name__ == "__main__":
    unittest.main()
