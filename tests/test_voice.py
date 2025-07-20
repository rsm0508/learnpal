import io
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_stt_endpoint():
    # 1-second silent WAV header
    wav_header = (
        b"RIFF$\x00\x00\x00WAVEfmt "
        b"\x10\x00\x00\x00\x01\x00\x01\x00D\xac\x00\x00"
        b"\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00"
    )
    r = client.post(
        "/voice/stt",
        files={"file": ("test.wav", io.BytesIO(wav_header), "audio/wav")},
    )
    assert r.status_code == 200
    assert "text" in r.json()
