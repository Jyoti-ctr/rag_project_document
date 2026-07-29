/**
 * app.js
 * -------
 * Shared vanilla-JS utilities used across all pages:
 *   - Auth  : session storage of JWT + user profile
 *   - Api   : fetch wrapper that attaches the bearer token and
 *             normalizes error handling
 *   - Toast : lightweight toast notification system
 */

const Auth = {
  TOKEN_KEY: "rag_access_token",
  USER_KEY: "rag_user",

  getToken() {
    return localStorage.getItem(this.TOKEN_KEY);
  },

  getUser() {
    const raw = localStorage.getItem(this.USER_KEY);
    return raw ? JSON.parse(raw) : null;
  },

  setSession(token, user) {
    localStorage.setItem(this.TOKEN_KEY, token);
    localStorage.setItem(this.USER_KEY, JSON.stringify(user));
  },

  clearSession() {
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.USER_KEY);
  },
};

const Api = {
  async _request(method, path, body) {
    const headers = {};
    const token = Auth.getToken();
    if (token) headers["Authorization"] = `Bearer ${token}`;

    let requestBody = undefined;
    if (body !== undefined) {
      if (body instanceof FormData) {
        requestBody = body;
      } else {
        headers["Content-Type"] = "application/json";
        requestBody = JSON.stringify(body);
      }
    }

    const response = await fetch(path, {
      method,
      headers,
      body: requestBody,
    });

    if (response.status === 401) {
      Auth.clearSession();
      window.location.href = "/login";
      throw new Error("Session expired. Please sign in again.");
    }

    let data = null;
    const contentType = response.headers.get("content-type") || "";
    if (contentType.includes("application/json")) {
      data = await response.json();
    }

    if (!response.ok) {
      const message =
        (data && (data.detail || data.message)) ||
        `Request failed with status ${response.status}`;
      throw new Error(typeof message === "string" ? message : JSON.stringify(message));
    }

    return data;
  },

  get(path) {
    return this._request("GET", path);
  },
  post(path, body) {
    return this._request("POST", path, body);
  },
  upload(path, formData) {
    return this._request("POST", path, formData);
  },
  del(path) {
    return this._request("DELETE", path);
  },
};

const Toast = {
  show(message, type = "info", duration = 4000) {
    const stack = document.getElementById("toastStack");
    if (!stack) return;

    const el = document.createElement("div");
    el.className = `toast ${type}`;
    el.textContent = message;
    stack.appendChild(el);

    setTimeout(() => {
      el.style.opacity = "0";
      el.style.transition = "opacity 0.2s ease";
      setTimeout(() => el.remove(), 200);
    }, duration);
  },
};
