import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ATS Resume Scorer",
  description: "Compare your resume against a job description",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
