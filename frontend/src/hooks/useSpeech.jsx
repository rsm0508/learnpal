import { useEffect, useRef, useState } from "react";
import { useUnmount } from "react-use";

export default function useSpeech() {
  const recRef = useRef(null);
  const [transcript, setTranscript] = useState("");
  const [listening, setListening] = useState(false);

  // start/stop helpers
  const start = () => {
    if (!recRef.current) {
      const SpeechRec =
        window.SpeechRecognition || window.webkitSpeechRecognition;
      if (!SpeechRec) return alert("SpeechRecognition not supported");
      recRef.current = new SpeechRec();
      recRef.current.continuous = false;
      recRef.current.onresult = (e) =>
        setTranscript(e.results[0][0].transcript);
    }
    recRef.current.start();
    setListening(true);
  };
  const stop = () => recRef.current && recRef.current.stop();

  useUnmount(stop);
  return { transcript, listening, start, stop, setTranscript };
}
