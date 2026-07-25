import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        surface: {
          page: "#0d0d0d",
          card: "#1a1a19",
          cardhover: "#212120",
        },
        ink: {
          primary: "#ffffff",
          secondary: "#c3c2b7",
          muted: "#898781",
        },
        line: {
          grid: "#2c2c2a",
          baseline: "#383835",
          border: "rgba(255,255,255,0.10)",
        },
        series: {
          1: "#3987e5", // blue - terneros
          2: "#008300", // green - novillitos 300-390
          3: "#d55181", // magenta - novillitos 391-430
          4: "#c98500", // yellow - novillos +430
          5: "#199e70", // aqua - vaquillonas
          6: "#d95926", // orange - vacas
        },
        status: {
          good: "#0ca30c",
          warning: "#fab219",
          serious: "#ec835a",
          critical: "#d03b3b",
        },
      },
      fontFamily: {
        sans: [
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "Roboto",
          "sans-serif",
        ],
      },
    },
  },
  plugins: [],
};
export default config;
