import { useState } from "react";
import useSpeech from "./hooks/useSpeech";
import "./App.css";

export default function App() {
  const { transcript, listening, start, stop, setTranscript } = useSpeech();
  const [replyUrl, setReplyUrl] = useState("");
  const [replyText, setReplyText] = useState("");

  async function handleSubmit(e) {
    e.preventDefault();
    const text = transcript || e.target.elements.msg.value;
    if (!text) return;

    try {
      /* 1️⃣  Ask the tutor */
      const lessonRes = await fetch("http://127.0.0.1:8000/lesson", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          learner_id: 1, // ⬅ will be dynamic after auth UI lands
          user_text: text,
        }),
      });
      const { reply } = await lessonRes.json();
      setReplyText(reply);

      /* 2️⃣  Turn reply into speech */
      const ttsRes = await fetch(
        "http://127.0.0.1:8000/voice/tts?text=" + encodeURIComponent(reply)
      );
      const blob = await ttsRes.blob();
      setReplyUrl(URL.createObjectURL(blob));
    } catch (err) {
      console.error(err);
      alert("Something went wrong. Check the server logs.");
    }

    setTranscript("");
    e.target.reset();
  }

  return (
    <div className="container">
      <h1>LearnPal Voice Demo</h1>

      {/* input */}
      <form onSubmit={handleSubmit} style={{ marginBottom: "1rem" }}>
        <input name="msg" placeholder="Type answer…" />
        <button>Send</button>
      </form>

      {/* mic */}
      <p>
        <button onClick={listening ? stop : start}>
          {listening ? "Stop Mic" : "Speak"}
        </button>
        {transcript && <em> “{transcript}”</em>}
      </p>

      {/* GPT reply + audio */}
      {replyUrl && (
        <>
          <audio key={replyUrl} src={replyUrl} controls autoPlay />
          <p style={{ marginTop: "0.5rem" }}>{replyText}</p>
        </>
      )}
    </div>
  );
}
