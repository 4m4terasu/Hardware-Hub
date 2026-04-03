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

export async function getHardware(): Promise<HardwareListItem[]> {
  const response = await fetch(`${API_BASE_URL}/api/hardware`, {
    credentials: "include",
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch hardware: ${response.status}`);
  }

  return response.json() as Promise<HardwareListItem[]>;
}