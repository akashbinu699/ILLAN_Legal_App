/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        lm: {
           bg: '#eefcf4', // Lightest green for app bg if needed
           header: '#88e4a8', // The header green
           active: '#4ade80', // Active tab green
           text: '#166534', // Dark green text
        }
      },
    },
  },
  plugins: [],
}
