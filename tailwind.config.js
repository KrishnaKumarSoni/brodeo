/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.{html,js}",
    "./static/**/*.js"
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        'brodeo-red': '#DC2626',
        'brodeo-black': '#000000',
        'gray': {
          50: '#FAFAFA',
          100: '#F4F4F5',
          200: '#E4E4E7',
          300: '#D4D4D8',
          400: '#A1A1AA',
          500: '#71717A',
          600: '#52525B',
          700: '#3F3F46',
          800: '#1A1A1A',  // Pure black instead of blue-tinted
          900: '#000000'   // Pure black
        }
      },
      fontFamily: {
        'mohave': ['Mohave', 'sans-serif'],
        'inter': ['Inter', 'sans-serif']
      }
    },
  },
  plugins: [],
}