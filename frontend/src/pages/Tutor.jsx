import { useState, useEffect, useRef } from "react";
import api from "../api";

export default function Tutor({ learner, user, onBack }) {
  const [text, setText] = useState("");
  const [thread, setThread] = useState([]);
  const [lastLatency, setLastLatency] = useState(0);
  const [sending, setSending] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  
  const audioRef = useRef(null);

  // Initialize conversation when learner enters
  useEffect(() => {
    if (learner && thread.length === 0) {
      initializeConversation();
    }
  }, [learner]);

  const initializeConversation = async () => {
    const greeting = `Hi ${learner.name}! I'm your AI tutor. Ready to learn something new today?`;
    setThread([{ you: null, bot: greeting, isGreeting: true }]);
    
    // Play greeting audio
    playAudio(greeting);
  };

  const playAudio = async (text) => {
    try {
      setIsPlaying(true);
      // Clean text for TTS - remove emoticons and symbols
      const cleanText = text
        .replace(/[👍👎🎉🔥💪✨🌟⭐️🎯🏆🎊🎈😊😄😃🙂]/g, '') // Remove emoticons
        .replace(/:\)/g, '') // Remove text emoticons
        .replace(/:\(/g, '')
        .replace(/:\D/g, '') // Remove other emoticons
        .trim();
      
      if (cleanText && audioRef.current) {
        const url = `http://localhost:8000/voice/tts?text=${encodeURIComponent(cleanText)}`;
        audioRef.current.src = url;
        await audioRef.current.play();
      }
    } catch (error) {
      console.error("Audio playback failed:", error);
    } finally {
      setIsPlaying(false);
    }
  };

  const send = async () => {
    if (!text.trim() || sending) return;
    
    setSending(true);
    const userMessage = text;
    setText("");
    
    setThread(prev => [...prev, { you: userMessage, bot: null, loading: true }]);
    
    try {
      const t0 = performance.now();
      const res = await api.post("/lesson", {
        learner_id: learner.id,
        user_text: userMessage,
      });
      const latency = res.data.latency_ms || Math.round(performance.now() - t0);
      setLastLatency(latency);
      
      const botResponse = res.data.content;
      setThread(prev => {
        const updated = [...prev];
        updated[updated.length - 1] = { 
          you: userMessage, 
          bot: botResponse, 
          loading: false 
        };
        return updated;
      });

      // Play bot response audio with cleaned text
      playAudio(botResponse);
      
    } catch (error) {
      console.error("Failed to send message:", error);
      setThread(prev => {
        const updated = [...prev];
        updated[updated.length - 1] = { 
          you: userMessage, 
          bot: "Sorry, I'm having trouble right now. Please try again.", 
          loading: false,
          error: true
        };
        return updated;
      });
    } finally {
      setSending(false);
    }
  };

  const rate = async (val) => {
    try {
      await api.post("/feedback", {
        learner_id: learner.id,
        rating: val,
        latency_ms: lastLatency,
      });
    } catch (err) {
      console.error("Failed to send feedback:", err);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  const handleBack = () => {
    if (onBack) {
      onBack();
    } else {
      window.location.reload();
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div>
                <h1 className="text-lg font-semibold">{learner.name}'s Session</h1>
                <p className="text-sm text-gray-500">AI Tutor</p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => window.open(`/progress/${learner.id}`, '_blank')}
                className="btn-secondary text-sm"
              >
                Progress
              </button>
              <button
                onClick={handleBack}
                className="btn-secondary text-sm"
              >
                Back
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Chat Area */}
      <div className="max-w-4xl mx-auto p-4">
        <div className="card">
          <div className="h-96 overflow-y-auto p-4 space-y-3">
            {thread.map((message, i) => (
              <div key={i}>
                {message.you && (
                  <div className="flex justify-end mb-2">
                    <div className="bg-blue-600 text-white px-3 py-2 rounded-lg max-w-xs text-sm">
                      {message.you}
                    </div>
                  </div>
                )}
                <div className="flex justify-start">
                  <div className="bg-gray-100 px-3 py-2 rounded-lg max-w-xs text-sm">
                    {message.loading ? (
                      <div className="flex items-center space-x-2">
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                      </div>
                    ) : (
                      message.bot
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Input Area */}
          <div className="border-t border-gray-200 p-4">
            <div className="flex items-center space-x-2">
              <input
                type="text"
                value={text}
                onChange={(e) => setText(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Type your message..."
                className="input flex-1"
              />
              
              <button
                onClick={send}
                disabled={!text.trim() || sending}
                className="btn-primary"
              >
                {sending ? "..." : "Send"}
              </button>
            </div>
            
            {/* Feedback */}
            {thread.length > 1 && (
              <div className="flex justify-center space-x-2 mt-3">
                <button onClick={() => rate(1)} className="btn-sm btn-success">
                  👍
                </button>
                <button onClick={() => rate(-1)} className="btn-sm btn-secondary">
                  👎
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Audio element for TTS */}
      <audio
        ref={audioRef}
        onEnded={() => setIsPlaying(false)}
        style={{ display: 'none' }}
      />
      
      {/* Audio indicator */}
      {isPlaying && (
        <div className="fixed bottom-4 right-4 bg-blue-600 text-white px-3 py-2 rounded-lg text-sm">
          🔊 Playing...
        </div>
      )}
    </div>
  );
}
