/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        ink: {
          900: '#0a0e17',
          800: '#0f1521',
          700: '#161d2e',
          600: '#1e2740',
        },
        amber: {
          glow: '#ffb13d',
        },
        electric: '#4f8cff',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        display: ['"Space Grotesk"', 'Inter', 'sans-serif'],
      },
      boxShadow: {
        glow: '0 0 40px -10px rgba(255,177,61,0.45)',
        'glow-blue': '0 0 40px -10px rgba(79,140,255,0.5)',
        glass: '0 8px 32px rgba(0,0,0,0.37)',
      },
      backgroundImage: {
        aurora:
          'radial-gradient(60% 60% at 20% 20%, rgba(79,140,255,0.18) 0%, transparent 60%), radial-gradient(50% 50% at 85% 30%, rgba(255,177,61,0.16) 0%, transparent 55%), radial-gradient(60% 60% at 60% 100%, rgba(124,77,255,0.14) 0%, transparent 60%)',
      },
      keyframes: {
        float: {
          '0%,100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-12px)' },
        },
        shimmer: {
          '100%': { transform: 'translateX(100%)' },
        },
      },
      animation: {
        float: 'float 6s ease-in-out infinite',
      },
    },
  },
  plugins: [],
}
