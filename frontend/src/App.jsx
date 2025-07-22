import { useEffect, useState } from "react";
import { loadToken } from "./api";
import api from "./api";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import LearnerSelect from "./pages/LearnerSelect";
import Tutor from "./pages/Tutor";
import ParentProgress from "./pages/ParentProgress";

// run once at startup
loadToken();

export default function App() {
  const [stage, setStage] = useState("login");   // login | signup | select | tutor | progress
  const [learner, setLearner] = useState(null);
  const [user, setUser] = useState(null);

  // after selecting a learner, move to tutor screen
  function pickLearner(l) {
    setLearner(l);
    setStage("tutor");
  }

  // show progress for selected learner
  function showProgress(l) {
    setLearner(l);
    setStage("progress");
  }

  // fetch user info after login/signup
  const fetchUser = async () => {
    try {
      const response = await api.get("/me");
      setUser(response.data);
    } catch (error) {
      console.error("Failed to fetch user:", error);
      // If token is invalid, force login
      localStorage.removeItem("lp_jwt");
      setStage("login");
    }
  };

  // check token and fetch user on startup
  useEffect(() => {
    const token = localStorage.getItem("lp_jwt");
    if (!token) {
      setStage("login");
    } else {
      fetchUser();
    }
  }, []);

  // handle successful login/signup
  const handleAuthSuccess = () => {
    fetchUser();
    setStage("select");
  };

  if (stage === "login") {
    return (
      <Login 
        onLogin={handleAuthSuccess}
        onSwitchToSignup={() => setStage("signup")}
      />
    );
  }

  if (stage === "signup") {
    return (
      <Signup 
        onSignup={handleAuthSuccess}
        onSwitchToLogin={() => setStage("login")}
      />
    );
  }

  if (stage === "select") {
    return <LearnerSelect onPick={pickLearner} onShowProgress={showProgress} user={user} />;
  }

  if (stage === "progress") {
    return <ParentProgress learner={learner} user={user} onBack={() => setStage("select")} />;
  }

  return <Tutor learner={learner} user={user} onBack={() => setStage("select")} onShowProgress={() => setStage("progress")} />;
}
