import axios from "axios";
const api = axios.create({ baseURL: "http://127.0.0.1:8000" });

export function setToken(jwt) {
  api.defaults.headers.common["Authorization"] = `Bearer ${jwt}`;
  localStorage.setItem("lp_jwt", jwt);
}

export function loadToken() {
  const t = localStorage.getItem("lp_jwt");
  if (t) api.defaults.headers.common["Authorization"] = `Bearer ${t}`;
}
export default api;
