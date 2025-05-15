/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        border: "hsl(240, 5%, 84%)",
        input: "hsl(240, 5%, 96%)",
        ring: "hsl(240, 5%, 84%)",
        background: "hsl(0, 0%, 100%)",
        foreground: "hsl(240, 10%, 4%)",
      },
    },
  },
  plugins: [],
}
