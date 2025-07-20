import { useState } from "react";
import api, { setToken } from "../api";

export default function Login({ onLogin }) {
  const [email, setEmail] = useState("");
  const [pw, setPw] = useState("");

  async function submit(e) {
    e.preventDefault();
    const { data } = await api.post("/auth/token", new URLSearchParams({
      username: email,
      password: pw,
    }));
    setToken(data.access_token);
    onLogin();
  }

  return (
    <form onSubmit={submit}>
      <h2>Parent Login</h2>
      <input value={email} onChange={e=>setEmail(e.target.value)} placeholder="email" />
      <input type="password" value={pw} onChange={e=>setPw(e.target.value)} placeholder="password" />
      <button>Login</button>
    </form>
  );
}
