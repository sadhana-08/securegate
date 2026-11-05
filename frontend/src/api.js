const API_BASE_URL = "http://127.0.0.1:5000/api";

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
    return responseMessage || "Please sign in to continue.";
  }
  if (status === 403) {
    return "Your security token expired or is invalid. Please try again.";
  }
  if (status === 429) {
    return "Too many sign-in attempts. Please wait 15 minutes and try again.";
  }
  if (status >= 500) {
    return "The server could not complete your request. Please try again later.";
  }
  return responseMessage || "Please check your information and try again.";
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
    try {
      const csrfResponse = await fetch(`${API_BASE_URL}/csrf-token`, {
        credentials: "include",
        headers: { Accept: "application/json" },
      });
      const csrfPayload = await csrfResponse.json();
      if (!csrfResponse.ok || typeof csrfPayload.csrf_token !== "string") {
        throw new ApiError(
          "Could not start a secure request. Refresh the page and try again.",
          csrfResponse.status,
        );
      }
      requestHeaders["X-CSRF-Token"] = csrfPayload.csrf_token;
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }
      throw new ApiError(
        "Cannot reach SecureGate. Check that the backend is running.",
      );
    }
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
  login: (identifier, password) =>
    request("/auth/login", {
      method: "POST",
      body: { identifier, password },
    }),
  logout: () => request("/auth/logout", { method: "POST" }),
  me: () => request("/me"),
  profile: () => request("/profile"),
  updateProfile: (data) =>
    request("/profile", { method: "PUT", body: data }),
};
