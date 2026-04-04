export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

const ACCESS_TOKEN_KEY = "hardware_hub_access_token";

export type LoginRequest = {
  email: string;
  password: string;
};

export type LoginResponse = {
  access_token: string;
  token_type: "bearer";
};

export type AuthUser = {
  id: number;
  email: string;
  is_admin: boolean;
};

export type HardwareListItem = {
  id: number;
  name: string;
  brand: string | null;
  purchase_date_raw: string | null;
  status_raw: string | null;
  notes: string | null;
  assigned_to: string | null;
  history_text: string | null;
};

export type HardwareQueryParams = {
  status?: string;
  brand?: string;
  sortBy?: "id" | "name" | "brand" | "purchase_date_raw" | "status_raw";
  sortDir?: "asc" | "desc";
};

export function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function setAccessToken(token: string): void {
  localStorage.setItem(ACCESS_TOKEN_KEY, token);
}

export function clearAccessToken(): void {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
}

async function readErrorMessage(
  response: Response,
  fallbackMessage: string,
): Promise<string> {
  try {
    const data = (await response.json()) as { detail?: string };
    if (typeof data.detail === "string" && data.detail.length > 0) {
      return data.detail;
    }
  } catch {
    // ignore json parse errors
  }

  return fallbackMessage;
}

async function apiFetch(path: string, init: RequestInit = {}): Promise<Response> {
  const headers = new Headers(init.headers);
  const token = getAccessToken();

  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  if (init.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  return fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers,
    credentials: "include",
  });
}

export async function login(payload: LoginRequest): Promise<LoginResponse> {
  const response = await apiFetch("/api/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(
      await readErrorMessage(response, "Login failed. Please try again."),
    );
  }

  const data = (await response.json()) as LoginResponse;
  setAccessToken(data.access_token);
  return data;
}

export async function getCurrentUser(): Promise<AuthUser> {
  const response = await apiFetch("/api/auth/me");

  if (!response.ok) {
    throw new Error(
      await readErrorMessage(response, "Failed to load current user."),
    );
  }

  return response.json() as Promise<AuthUser>;
}

export async function getHardware(
  params: HardwareQueryParams = {},
): Promise<HardwareListItem[]> {
  const searchParams = new URLSearchParams();

  if (params.status) {
    searchParams.set("status", params.status);
  }

  if (params.brand) {
    searchParams.set("brand", params.brand);
  }

  if (params.sortBy) {
    searchParams.set("sort_by", params.sortBy);
  }

  if (params.sortDir) {
    searchParams.set("sort_dir", params.sortDir);
  }

  const queryString = searchParams.toString();
  const url = `/api/hardware${queryString ? `?${queryString}` : ""}`;

  const response = await apiFetch(url);

  if (!response.ok) {
    throw new Error(
      await readErrorMessage(response, "Failed to fetch hardware inventory."),
    );
  }

  return response.json() as Promise<HardwareListItem[]>;
}