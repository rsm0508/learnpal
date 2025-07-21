import { useEffect, useState } from "react";
import api, { loadToken } from "./api";
import Login from "./pages/Login";
import LearnerSelect from "./pages/LearnerSelect";
import Tutor from "./pages/Tutor";

export default function App() {
  const [stage, setStage] = useState("boot"); // boot | login | pick | tutor
  const [learner, setLearner] = useState(null);

  // try existing JWT once on mount
  useEffect(() => {
    loadToken();
    api.get("/me")
      .then(() => setStage("pick"))
      .catch(() => setStage("login"));
  }, []);

  if (stage === "login")
    return <Login onLogin={() => setStage("pick")} />;

  if (stage === "pick")
    return (
      <LearnerSelect
        onChoose={(l) => {
          setLearner(l);
          setStage("tutor");
        }}
      />
    );

  if (stage === "tutor" && learner)
    return <Tutor learner={learner} />;

  return <p>Loading…</p>;
}
