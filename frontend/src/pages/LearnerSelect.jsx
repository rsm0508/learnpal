import { useEffect, useState } from "react";
import api from "../api";

export default function LearnerSelect({ onChoose }) {
  const [list, setList] = useState([]);
  useEffect(()=>{ api.get("/learners").then(r=>setList(r.data)); }, []);

  return (
    <>
      <h2>Who’s learning today?</h2>
      {list.map(l => (
        <button key={l.id} onClick={()=>onChoose(l)}>
          {l.name}
        </button>
      ))}
    </>
  );
}
