// Fallback 404 for non-localized paths. Renders its own shell because there is no
// root app/layout (the [locale] layout owns <html>). Defaults to Arabic (RTL).
export default function GlobalNotFound() {
  return (
    <html lang="ar" dir="rtl">
      <body
        style={{
          margin: 0,
          minHeight: "100vh",
          display: "grid",
          placeItems: "center",
          background: "#0a0c11",
          color: "#e2e8f0",
          fontFamily: "system-ui, sans-serif",
        }}
      >
        <div style={{ textAlign: "center" }}>
          <p style={{ margin: 0, fontSize: 56, fontWeight: 700, color: "#a3e635" }}>404</p>
          <a href="/ar" style={{ color: "#94a3b8", textDecoration: "none" }}>
            ← الرئيسية
          </a>
        </div>
      </body>
    </html>
  );
}
