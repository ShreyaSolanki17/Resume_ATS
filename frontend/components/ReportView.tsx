"use client";

import type { ReportResult } from "@/lib/types";

function severityClass(severity: string) {
  if (severity === "high") return "chip danger";
  if (severity === "medium") return "chip warning";
  return "chip";
}

interface Props {
  report: ReportResult;
  onReset: () => void;
}

export function ReportView({ report, onReset }: Props) {
  const score = report.match_score;

  return (
    <>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1.5rem" }}>
        <div>
          <h1>Analysis Report</h1>
          <p className="subtitle" style={{ marginBottom: 0 }}>
            Match score and actionable feedback for your target role
          </p>
        </div>
        <button className="btn btn-secondary" onClick={onReset}>
          New analysis
        </button>
      </div>

      <div className="report-header">
        <div className="card" style={{ textAlign: "center" }}>
          <div
            className="score-ring"
            style={{ "--score": score } as React.CSSProperties}
          >
            <span className="score-value">{score}</span>
          </div>
          <p style={{ color: "var(--muted)", fontSize: "0.9rem" }}>
            ATS Match Score
          </p>
        </div>

        {report.jd_analysis?.years_experience && (
          <div className="card">
            <h2>Experience Required</h2>
            <p>{report.jd_analysis.years_experience}</p>
          </div>
        )}
      </div>

      <div className="grid-2">
        <div className="card">
          <h2>Matched Skills</h2>
          {report.matched_skills.length ? (
            <div className="chips">
              {report.matched_skills.map((s) => (
                <span key={s} className="chip success">
                  {s}
                </span>
              ))}
            </div>
          ) : (
            <p style={{ color: "var(--muted)" }}>No direct skill matches found.</p>
          )}
        </div>

        <div className="card">
          <h2>Missing Required</h2>
          {report.missing_required_skills.length ? (
            <div className="chips">
              {report.missing_required_skills.map((s) => (
                <span key={s} className="chip danger">
                  {s}
                </span>
              ))}
            </div>
          ) : (
            <p style={{ color: "var(--success)" }}>All required skills matched.</p>
          )}
        </div>
      </div>

      {report.missing_nice_to_have.length > 0 && (
        <div className="card">
          <h2>Missing Nice-to-Have</h2>
          <div className="chips">
            {report.missing_nice_to_have.map((s) => (
              <span key={s} className="chip warning">
                {s}
              </span>
            ))}
          </div>
        </div>
      )}

      {report.format_flags.length > 0 && (
        <div className="card">
          <h2>Formatting Red Flags</h2>
          <ul className="flag-list">
            {report.format_flags.map((flag, i) => (
              <li key={i}>
                <span>{flag.issue}</span>
                <span className={severityClass(flag.severity)}>
                  {flag.severity}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="card">
        <h2>Suggestions</h2>
        <ul className="suggestions">
          {report.suggestions.map((s, i) => (
            <li key={i}>{s}</li>
          ))}
        </ul>
      </div>
    </>
  );
}
