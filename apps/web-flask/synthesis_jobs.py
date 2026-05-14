import json
import os
import shutil
import time
import uuid
from threading import Thread


def is_valid_job_id(job_id):
    if not isinstance(job_id, str) or len(job_id) != 32:
        return False

    try:
        return uuid.UUID(hex=job_id).hex == job_id
    except ValueError:
        return False


def job_error_message(exc):
    if isinstance(exc, MemoryError):
        return "MemoryError: synthesis ran out of memory"
    if isinstance(exc, EOFError):
        return "Uploaded MIDI file is empty or incomplete."

    message = str(exc).strip()
    if message:
        return message
    return exc.__class__.__name__


class SynthesisJobService:
    def __init__(self, job_root, download_ttl_seconds, run_inline=False, logger=None):
        self.job_root = job_root
        self.download_ttl_seconds = download_ttl_seconds
        self.run_inline = run_inline
        self.logger = logger

    def job_dir(self, job_id):
        if not is_valid_job_id(job_id):
            return None
        return os.path.join(self.job_root, job_id)

    def metadata_path(self, job_id):
        job_dir = self.job_dir(job_id)
        if job_dir is None:
            return None
        return os.path.join(job_dir, "metadata.json")

    def input_path(self, job_id):
        job_dir = self.job_dir(job_id)
        if job_dir is None:
            return None
        return os.path.join(job_dir, "input.mid")

    def output_path(self, job_id):
        job_dir = self.job_dir(job_id)
        if job_dir is None:
            return None
        return os.path.join(job_dir, "output.wav")

    def prepare_job(self):
        job_id = uuid.uuid4().hex
        job_dir = self.job_dir(job_id)
        os.makedirs(job_dir, exist_ok=True)
        return job_id, self.input_path(job_id)

    def write_metadata(self, job_id, metadata):
        job_dir = self.job_dir(job_id)
        if job_dir is None:
            raise ValueError("Invalid job id")

        os.makedirs(job_dir, exist_ok=True)
        metadata_path = self.metadata_path(job_id)
        temp_path = os.path.join(job_dir, f"metadata.{uuid.uuid4().hex}.tmp")
        with open(temp_path, "w", encoding="utf-8") as file:
            json.dump(metadata, file, sort_keys=True)
        os.replace(temp_path, metadata_path)

    def read_metadata(self, job_id):
        metadata_path = self.metadata_path(job_id)
        if metadata_path is None or not os.path.exists(metadata_path):
            return None

        with open(metadata_path, encoding="utf-8") as file:
            metadata = json.load(file)

        expires_at = metadata.get("expires_at")
        if expires_at is not None and time.time() > expires_at:
            self.delete_job(job_id)
            return {
                "job_id": job_id,
                "status": "expired",
            }

        return metadata

    def delete_job(self, job_id):
        job_dir = self.job_dir(job_id)
        if job_dir:
            shutil.rmtree(job_dir, ignore_errors=True)

    def cleanup_expired_jobs(self):
        if not os.path.isdir(self.job_root):
            return

        for job_id in os.listdir(self.job_root):
            if is_valid_job_id(job_id):
                self.read_metadata(job_id)

    def initial_metadata(self, job_id, uploaded_filename):
        now = time.time()
        return {
            "job_id": job_id,
            "status": "queued",
            "source_name": os.path.basename(uploaded_filename or ""),
            "created_at": now,
            "updated_at": now,
            "expires_at": now + self.download_ttl_seconds,
        }

    def update_status(self, job_id, **updates):
        metadata = self.read_metadata(job_id)
        if metadata is None or metadata.get("status") == "expired":
            return

        metadata.update(updates)
        metadata["updated_at"] = time.time()
        self.write_metadata(job_id, metadata)

    def job_payload(self, metadata, route_base="/synthesise/jobs"):
        status = metadata.get("status", "expired")
        payload = {
            "job_id": metadata.get("job_id"),
            "status": status,
        }
        for key in ("created_at", "updated_at", "expires_at", "download_name", "size_bytes", "error"):
            if key in metadata:
                payload[key] = metadata[key]

        if status == "ready":
            job_id = metadata["job_id"]
            payload["download_url"] = f"{route_base}/{job_id}/download"
            payload["delete_url"] = f"{route_base}/{job_id}"

        return payload

    def start_job(self, job_id, input_path, form_payload, uploaded_filename, render_uploaded_wav):
        if self.run_inline:
            self.run_job(job_id, input_path, form_payload, uploaded_filename, render_uploaded_wav)
            return

        thread = Thread(
            target=self.run_job,
            args=(job_id, input_path, form_payload, uploaded_filename, render_uploaded_wav),
            daemon=True,
        )
        thread.start()

    def run_job(self, job_id, input_path, form_payload, uploaded_filename, render_uploaded_wav):
        output_path = self.output_path(job_id)
        self.update_status(job_id, status="rendering")
        try:
            class SavedUpload:
                filename = uploaded_filename

                def save(self, destination):
                    shutil.copyfile(input_path, destination)

            download_name = render_uploaded_wav(SavedUpload(), form_payload, output_path)
            now = time.time()
            self.update_status(
                job_id,
                status="ready",
                download_name=download_name,
                size_bytes=os.path.getsize(output_path),
                expires_at=now + self.download_ttl_seconds,
            )
        except Exception as exc:
            if self.logger is not None:
                if isinstance(exc, (EOFError, ValueError)):
                    self.logger.warning("Synthesis job %s failed: %s", job_id, exc)
                else:
                    self.logger.exception("Synthesis job %s failed", job_id)
            now = time.time()
            self.update_status(
                job_id,
                status="failed",
                error=job_error_message(exc),
                expires_at=now + self.download_ttl_seconds,
            )
        finally:
            try:
                os.unlink(input_path)
            except FileNotFoundError:
                pass
