"use client";

import { useCallback, useRef, useState } from "react";
import { submitReport } from "@/lib/api";
import type { ReportResult } from "@/lib/types";
import { ReportView } from "@/components/ReportView";

export default function HomePage() {
  const [file, setFile] = useState<File | null>(null);
  const [jdText, setJdText] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<ReportResult | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const onFile = useCallback((f: File | null) => {
    if (!f) return;
    const ext = f.name.split(".").pop()?.toLowerCase();
    if (ext !== "pdf" && ext !== "docx") {
      setError("Please upload a PDF or DOCX file.");
      return;
    }
    setError(null);
    setFile(f);
  }, []);

  const handleAnalyze = async () => {
    if (!file) {
      setError("Upload a resume first.");
      return;
    }
    if (!jdText.trim()) {
      setError("Paste a job description.");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const result = await submitReport(file, jdText);
      setReport(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed.");
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    setReport(null);
    setFile(null);
    setJdText("");
    setError(null);
  };

  if (report) {
    return (
      <main>
        <ReportView report={report} onReset={reset} />
      </main>
    );
  }

  return (
    <main>
      <h1>ATS Resume Scorer</h1>
      <p className="subtitle">
        Upload your resume and paste a job description to get a match score,
        keyword gaps, formatting flags, and improvement suggestions.
      </p>

      {error && <div className="error">{error}</div>}

      <div className="card">
        <h2>Resume</h2>
        <div
          className={`dropzone ${dragActive ? "active" : ""}`}
          onClick={() => inputRef.current?.click()}
          onDragOver={(e) => {
            e.preventDefault();
            setDragActive(true);
          }}
          onDragLeave={() => setDragActive(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragActive(false);
            onFile(e.dataTransfer.files[0] ?? null);
          }}
        >
          <input
            ref={inputRef}
            type="file"
            accept=".pdf,.docx"
            onChange={(e) => onFile(e.target.files?.[0] ?? null)}
          />
          {file ? (
            <p>
              <strong>{file.name}</strong>
              <br />
              <span style={{ color: "var(--muted)", fontSize: "0.9rem" }}>
                Click or drop to replace
              </span>
            </p>
          ) : (
            <p>
              Drag & drop your resume here
              <br />
              <span style={{ color: "var(--muted)", fontSize: "0.9rem" }}>
                PDF or DOCX
              </span>
            </p>
          )}
        </div>
      </div>

      <div className="card">
        <h2>Job Description</h2>
        <textarea
          placeholder="Paste the full job description here..."
          value={jdText}
          onChange={(e) => setJdText(e.target.value)}
        />
      </div>

      <button className="btn" onClick={handleAnalyze} disabled={loading}>
        {loading ? "Analyzing…" : "Analyze Resume"}
      </button>
    </main>
  );
}
