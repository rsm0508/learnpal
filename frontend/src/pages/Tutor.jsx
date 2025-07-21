import { useState } from "react";
import useSpeech from "../hooks/useSpeech";
import api from "../api";

export default function Tutor({ learner }) {
  const { transcript, listening, start, stop, setTranscript } = useSpeech();
  const [replyUrl, setReplyUrl] = useState("");
  const [replyText, setReplyText] = useState("");

  async function handleSubmit(e) {
    e.preventDefault();
    const text = transcript || e.target.elements.msg.value;
    if (!text) return;

    try {
      // ask tutor
      const { data } = await api.post("/lesson", {
        learner_id: learner.id,
        user_text: text,
      });
      setReplyText(data.reply);

      // TTS
      const tts = await fetch(
        "http://127.0.0.1:8000/voice/tts?text=" + encodeURIComponent(data.reply)
      );
      setReplyUrl(URL.createObjectURL(await tts.blob()));
    } catch (err) {
      console.error(err);
      alert("Error: " + err);
    }

    setTranscript("");
    e.target.reset();
  }

  return (
    <div className="container">
      <h2>Talking to {learner.name}</h2>

      <form onSubmit={handleSubmit} style={{ marginBottom: 12 }}>
        <input name="msg" placeholder="Type answer…" />
        <button>Send</button>
      </form>

      <p>
        <button onClick={listening ? stop : start}>
          {listening ? "Stop Mic" : "Speak"}
        </button>
        {transcript && <em> “{transcript}”</em>}
      </p>

      {replyUrl && (
        <>
          <audio key={replyUrl} src={replyUrl} controls autoPlay />
          <p style={{ marginTop: 8 }}>{replyText}</p>
        </>
      )}
    </div>
  );
}
