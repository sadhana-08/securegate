const API_HOST = window.location.hostname === "localhost" ? "localhost" : "127.0.0.1";
const API_BASE_URL = `http://${API_HOST}:5000/api`;

export class ApiError extends Error {
  constructor(message, status = 0, details = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.details = details;
  }
}

function friendlyMessage(status, responseMessage) {
  if (status === 401) {
    if (responseMessage === "Invalid username/email or password.") {
      return "Sign-in failed. Check your username/email and password.";
    }
    if (responseMessage === "Authentication required.") {
      return "Your session has expired. Please sign in again.";
    }
    return responseMessage || "Please sign in to continue.";
  }
  if (status === 403) {
    return "The security token is missing or expired. Refresh the page and try again.";
  }
  if (status === 429) {
    return "Too many sign-in attempts. Please wait 15 minutes and try again.";
  }
  if (status >= 500) {
    return "The server could not complete your request. Please try again later.";
  }
  return responseMessage || "Please check your information and try again.";
}

async function fetchCsrfToken() {
  let response;
  try {
    response = await fetch(`${API_BASE_URL}/csrf-token`, {
      credentials: "include",
      headers: { Accept: "application/json" },
    });
  } catch {
    throw new ApiError("Cannot reach SecureGate. Check that the backend is running.");
  }

  let payload;
  try {
    payload = await response.json();
  } catch {
    throw new ApiError(
      "The server could not provide a security token. Please try again.",
      response.status,
    );
  }
  if (!response.ok || typeof payload.csrf_token !== "string") {
    throw new ApiError(
      "The server could not provide a security token. Please try again.",
      response.status,
    );
  }
  return payload.csrf_token;
}

async function request(path, { method = "GET", body, headers = {} } = {}) {
  const requestHeaders = { Accept: "application/json", ...headers };
  const options = {
    method,
    headers: requestHeaders,
    credentials: "include",
  };

  if (body !== undefined) {
    requestHeaders["Content-Type"] = "application/json";
    options.body = JSON.stringify(body);
  }

  if (["POST", "PUT", "PATCH", "DELETE"].includes(method)) {
    requestHeaders["X-CSRF-Token"] = await fetchCsrfToken();
  }

  let response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, options);
  } catch {
    throw new ApiError(
      "Cannot reach SecureGate. Check that the backend is running.",
    );
  }

  let payload = {};
  try {
    payload = await response.json();
  } catch {
    if (response.ok) {
      throw new ApiError("The server returned an unexpected response.");
    }
  }

  if (!response.ok) {
    if (
      response.status === 401 &&
      ["/me", "/profile"].includes(path)
    ) {
      window.dispatchEvent(new Event("securegate:unauthorized"));
    }
    throw new ApiError(
      friendlyMessage(response.status, payload.error),
      response.status,
      payload.details || null,
    );
  }
  return payload;
}

export const api = {
  register: (data) => request("/auth/register", { method: "POST", body: data }),
  login: async (identifier, password) => {
    const result = await request("/auth/login", {
      method: "POST",
      body: { identifier, password },
    });
    await fetchCsrfToken();
    return result;
  },
  logout: async () => {
    const result = await request("/auth/logout", { method: "POST" });
    try {
      await fetchCsrfToken();
    } catch (error) {
      error.sessionEnded = true;
      throw error;
    }
    return result;
  },
  me: () => request("/me"),
  profile: () => request("/profile"),
  updateProfile: (data) =>
    request("/profile", { method: "PUT", body: data }),
};
