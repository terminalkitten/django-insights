/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["../templates/**/*.{html,js}", "node_modules/preline/dist/*.js"],
  darkMode: "class",
  theme: {
    fontFamily: {
      sans: ["Ubuntu", "sans-serif"],
    },
    extend: {
      colors: {
        background: "#f0f3f6",
        foreground: "#010409",
      },
      //   neutral: {
      //     50: "#f9fafb",
      //     100: "#f4f4f5",
      //     200: "#e6e6e6",
      //     300: "#d4d4d4",
      //     400: "#a3a2a3",
      //     500: "#737272",
      //     600: "#555353",
      //     700: "#424040",
      //     800: "#292727",
      //     900: "#1a1818",
      //   },
      //   blue: {
      //     DEFAULT: "#355bb6",
      //     50: "#eff6ff",
      //     100: "#dceafd",
      //     200: "#c3dcfb",
      //     300: "#9cc6f6",
      //     400: "#70a7ec",
      //     500: "#5287df",
      //     600: "#3f6dcd",
      //     700: "#355bb6",
      //     800: "#2746a0",
      //     900: "#1e3a8a",
      //   },
      // },
    },
  },
  plugins: [require("preline/plugin"), require("nightwind")],
};
