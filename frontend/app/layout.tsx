import type { Metadata } from "next";
import type { ReactNode } from "react";
import "./globals.css";
import NavBar from "@/components/NavBar";

export const metadata: Metadata = {
  title: "Tablero Ganadero | MAG Cañuelas",
  description:
    "Análisis de precios históricos y actuales del Mercado Agroganadero de Cañuelas (MAG).",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="es-AR">
      <body className="min-h-screen bg-surface-page font-sans text-ink-primary antialiased">
        <NavBar />
        <main className="mx-auto max-w-7xl px-4 py-6">{children}</main>
        <footer className="mx-auto max-w-7xl px-4 py-8 text-center text-[11px] text-ink-muted">
          Herramienta de análisis del mercado ganadero. Datos de referencia del Mercado
          Agroganadero de Cañuelas (MAG) — no incluye información de empresas privadas.
        </footer>
      </body>
    </html>
  );
}
