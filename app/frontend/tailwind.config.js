/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./{pages,components,layouts,context,hooks,services,state}/**/*.{js,ts,jsx,tsx}",
    "./*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'primary': '#003466',
        'vinuni-blue': '#003466',
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/container-queries'),
  ],
}
