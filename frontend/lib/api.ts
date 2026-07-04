import type { ReportResult } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function submitReport(
  file: File,
  jdText: string
): Promise<ReportResult> {
  const form = new FormData();
  form.append("file", file);
  form.append("jd_text", jdText);

  const res = await fetch(`${API_URL}/report`, {
    method: "POST",
    body: form,
  });

  if (!res.ok) {
    const detail = await res.text();
    throw new Error(detail || `Request failed (${res.status})`);
  }

  return res.json();
}
