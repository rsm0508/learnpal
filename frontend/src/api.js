// frontend/src/api.js   – shared Axios instance + token helpers
import axios from "axios";

const api = axios.create({
  baseURL: "http://127.0.0.1:8000",
  withCredentials: false,          // we use Bearer token, not cookies
});

// ---- token helpers -------------------------------------------------
const TOKEN_KEY = "lp_jwt";

export function setToken(jwt) {
  localStorage.setItem(TOKEN_KEY, jwt);
  api.defaults.headers.common["Authorization"] = `Bearer ${jwt}`;
}

export function loadToken() {
  const jwt = localStorage.getItem(TOKEN_KEY);
  if (jwt) {
    api.defaults.headers.common["Authorization"] = `Bearer ${jwt}`;
  }
}

export default api;
