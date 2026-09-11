"""The source-language registry and the Flask language switcher."""

import json
from dataclasses import replace
from pathlib import Path

import pytest

pytest.importorskip("flask")

from language_ai.config import Settings
from language_ai.languages import DEFAULT_LANGUAGE, LANGUAGES, get, ordered
from language_ai.web import flask_app


def test_language_is_the_default():
    assert DEFAULT_LANGUAGE == "language"
    assert get(None).code == "language"
    assert ordered()[0].code == "language"


def test_an_unknown_language_falls_back_rather_than_failing():
    assert get("klingon").code == "language"
    assert get("").code == "language"


def test_language_codes_are_matched_case_insensitively():
    assert get("LUO").code == "luo"


def test_every_language_carries_a_distinct_nllb_tag():
    tags = [language.nllb_code for language in LANGUAGES.values()]
    assert len(tags) == len(set(tags))
    assert get("luo").nllb_code == "luo_Latn"
    assert get("language").nllb_code == "kik_Latn"


def test_language_keeps_the_top_level_corpus_folder(tmp_path: Path):
    """Existing installs keep working, so Language must not move into a subfolder."""
    assert get("language").bible_dir(tmp_path) == tmp_path
    assert get("luo").bible_dir(tmp_path) == tmp_path / "luo"


def test_luo_names_its_own_speech_model():
    """Luo cannot share the Language speech model, so it must name its own."""
    luo = get("luo")
    assert luo.speech is True
    assert luo.asr_backend == "mms"
    assert luo.asr_language == "luo"
    assert luo.asr_model


def test_settings_are_adjusted_per_language(tmp_path: Path):
    from language_ai.languages import settings_for

    base = replace(Settings.from_env(), root=tmp_path)
    language = settings_for(get("language"), base)
    luo = settings_for(get("luo"), base)

    assert language.translation_src_lang == "kik_Latn"
    assert luo.translation_src_lang == "luo_Latn"
    # Every language now uses MMS, each with its own adapter.
    assert language.asr_backend == "mms" and language.asr_language == "kik"
    assert luo.asr_backend == "mms" and luo.asr_language == "luo"


def test_language_can_be_put_back_on_its_whisper_model(tmp_path: Path, monkeypatch):
    """MMS transcribes Language better but needs far more memory, so both stay open."""
    from language_ai.languages import settings_for

    base = replace(Settings.from_env(), root=tmp_path)
    monkeypatch.setenv("LANGUAGE_ASR_ENGINE", "whisper")

    language = settings_for(get("language"), base)

    assert language.asr_backend == base.asr_backend
    assert language.asr_model == base.asr_model
    # Only Language has a second option; the rest stay on MMS.
    assert settings_for(get("luo"), base).asr_backend == "mms"


def test_the_six_supported_languages_are_all_present():
    assert set(LANGUAGES) == {"language", "luo", "kamba", "swahili", "somali", "oromo"}
    for language in LANGUAGES.values():
        assert language.nllb_code.endswith("_Latn")
        assert language.asr_language


def test_speech_is_offered_only_when_the_model_is_on_disk(tmp_path: Path):
    """A missing model must disable the upload form, not fail at run time."""
    from language_ai.languages import speech_available

    base = replace(Settings.from_env(), root=tmp_path)

    assert speech_available(get("luo"), base) is False

    installed = tmp_path / get("luo").asr_model
    installed.mkdir(parents=True)
    # The shared encoder alone is not enough; MMS needs this language's adapter.
    assert speech_available(get("luo"), base) is False

    (installed / "adapter.luo.safetensors").write_bytes(b"weights")
    assert speech_available(get("luo"), base) is True
    # Another language's adapter is still missing, so it stays unavailable.
    assert speech_available(get("somali"), base) is False


def install_fake_models(root: Path) -> None:
    """A stand-in MMS tree so the upload form is offered in tests."""
    from language_ai.languages import LANGUAGES, MMS_MODEL

    folder = root / MMS_MODEL
    folder.mkdir(parents=True, exist_ok=True)
    for language in LANGUAGES.values():
        if language.asr_language:
            (folder / f"adapter.{language.asr_language}.safetensors").write_bytes(b"weights")


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    base = Settings.from_env()
    install_fake_models(tmp_path)
    bible = tmp_path / "bible"
    (bible / "luo").mkdir(parents=True)
    (bible / "parallel.jsonl").write_text(
        json.dumps({"book": "GEN", "chapter": 1, "verse": 1,
                    "language": "Kĩambĩrĩria-inĩ", "english": "In the beginning"}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (bible / "luo" / "parallel.jsonl").write_text(
        json.dumps({"book": "GEN", "chapter": 1, "verse": 1,
                    "language": "Kar chakruok", "english": "In the beginning"}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    # Make the shared speech model look installed, so speech-enabled routes run.
    (tmp_path / get("language").asr_model).mkdir(parents=True, exist_ok=True)
    return replace(
        base, root=tmp_path, sessions=tmp_path / "sessions", bible=bible,
        corrections_db=tmp_path / "corrections.db", api_url=None, max_upload_mb=1,
    )


class RecordingTranslator:
    def __init__(self):
        self.src_lang = "kik_Latn"
        self.seen: list[tuple[str, str]] = []

    def translate(self, text: str):
        self.seen.append((text, self.src_lang))
        return "translated", 0.7

    def unload(self):
        pass


class StubPipeline:
    def __init__(self, *_args):
        self.translator = RecordingTranslator()


@pytest.fixture
def client(settings: Settings, monkeypatch):
    translator = RecordingTranslator()

    class Pipeline:
        def __init__(self, *_args):
            self.translator = translator

    monkeypatch.setattr(flask_app, "Pipeline", Pipeline)
    app = flask_app.create_app(settings)
    test_client = app.test_client()
    test_client.translator = translator
    return test_client


def wait_for(client, job_id: str) -> dict:
    import time

    for _ in range(200):
        job = client.get(f"/status/{job_id}").get_json()
        if job["state"] in {"done", "failed"}:
            return job
        time.sleep(0.02)
    raise AssertionError("job never finished")


def test_the_page_defaults_to_language(client):
    body = client.get("/").get_data(as_text=True)

    assert "Language <span>" in body
    assert 'aria-current="page">Language' in body


def test_the_navbar_switches_to_luo(client):
    body = client.get("/?lang=luo").get_data(as_text=True)

    assert "Luo <span>" in body
    assert 'aria-current="page">Luo' in body


def test_the_navbar_lists_every_language(client):
    body = client.get("/").get_data(as_text=True)

    for language in LANGUAGES.values():
        assert f">{language.name}</a>" in body


def test_luo_text_is_translated_with_the_luo_tag(client):
    response = client.post("/translate-text", data={"text": "Nyasaye ber", "lang": "luo"})
    job = wait_for(client, response.headers["Location"].rstrip("/").rsplit("/", 1)[-1])

    assert job["result"]["language"] == "luo"
    assert job["result"]["language_name"] == "Luo"
    # The model is multilingual; the source tag is what selects the language.
    assert client.translator.seen == [("Nyasaye ber", "luo_Latn")]


def test_the_source_tag_is_restored_after_a_luo_translation(client):
    client.post("/translate-text", data={"text": "Nyasaye ber", "lang": "luo"})
    response = client.post("/translate-text", data={"text": "Ngai nĩ mwega", "lang": "language"})
    wait_for(client, response.headers["Location"].rstrip("/").rsplit("/", 1)[-1])

    assert client.translator.seen[-1][1] == "kik_Latn"


def test_each_language_matches_verses_against_its_own_corpus(client):
    response = client.post("/translate-text", data={"text": "Kar chakruok", "lang": "luo"})
    job = wait_for(client, response.headers["Location"].rstrip("/").rsplit("/", 1)[-1])

    assert job["result"]["bible_match"]["book"] == "GEN"
    assert job["result"]["english"] == "In the beginning"
    # A published verse must not be sent to the model at all.
    assert client.translator.seen == []


def test_a_language_verse_does_not_match_the_luo_corpus(client):
    response = client.post("/translate-text", data={"text": "Kar chakruok", "lang": "language"})
    job = wait_for(client, response.headers["Location"].rstrip("/").rsplit("/", 1)[-1])

    assert job["result"]["bible_match"] is None


def test_audio_is_refused_when_the_language_model_is_missing(settings: Settings, monkeypatch, tmp_path: Path):
    """A language whose speech model is absent must say so, not fail mid-job."""
    import io
    import shutil

    shutil.rmtree(tmp_path / get("luo").asr_model)
    monkeypatch.setattr(flask_app, "Pipeline", lambda *_a: None)
    client = flask_app.create_app(settings).test_client()

    response = client.post(
        "/translate",
        data={"lang": "luo", "audio": (io.BytesIO(b"bytes"), "clip.ogg")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 400
    body = response.get_data(as_text=True)
    assert "not available for Luo" in body
    assert "not installed" in body


def test_language_still_accepts_audio(client, monkeypatch):
    body = client.get("/").get_data(as_text=True)

    assert 'name="audio"' in body
    assert "not supported" not in body
