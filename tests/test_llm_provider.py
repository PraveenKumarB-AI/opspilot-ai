"""The OpenAI-compatible provider (e.g. Groq's free tier) works through the same ask_json() call."""
import httpx

from opspilot import config, llm


def _use_openai(monkeypatch):
    monkeypatch.setattr(config, "MODE", "auto")
    monkeypatch.setattr(config, "LLM_PROVIDER", "openai")
    monkeypatch.setattr(config, "LLM_API_KEY", "test-key")
    monkeypatch.setattr(config, "LLM_BASE_URL", "https://api.groq.com/openai/v1")
    monkeypatch.setattr(config, "LLM_MODEL", "some-model")
    monkeypatch.delenv("OPSPILOT_LLM_DAILY_CAP", raising=False)


def test_openai_compatible_reply_is_parsed(monkeypatch):
    _use_openai(monkeypatch)
    seen = {}

    def fake_post(url, headers, json, timeout):
        seen.update(url=url, auth=headers["Authorization"], model=json["model"])
        content = '<think>{"not": "this"}</think> Here you go: {"category": "billing"}'
        return httpx.Response(200, json={"choices": [{"message": {"content": content}}]},
                              request=httpx.Request("POST", url))

    monkeypatch.setattr(httpx, "post", fake_post)
    assert llm.ask_json("sys", "user") == {"category": "billing"}
    assert seen == {"url": "https://api.groq.com/openai/v1/chat/completions",
                    "auth": "Bearer test-key", "model": "some-model"}


def test_provider_error_falls_back(monkeypatch):
    _use_openai(monkeypatch)
    monkeypatch.setattr(httpx, "post", lambda *a, **k: httpx.Response(
        429, request=httpx.Request("POST", "https://x")))
    assert llm.ask_json("sys", "user") is None  # rate limited -> caller uses the offline fallback


def test_label_names_the_provider(monkeypatch):
    _use_openai(monkeypatch)
    assert config.llm_label() == "some-model via Groq"
    monkeypatch.setattr(config, "LLM_API_KEY", "")
    assert config.llm_label() == "Fallback mode (no API key)"
