export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

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
  const url = `${API_BASE_URL}/api/hardware${queryString ? `?${queryString}` : ""}`;

  const response = await fetch(url, {
    credentials: "include",
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch hardware: ${response.status}`);
  }

  return response.json() as Promise<HardwareListItem[]>;
}