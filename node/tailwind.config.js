module.exports = {
  content: [
      '../django/**/templates/**/*.html',
      './node_modules/flowbite/**/*.js'
  ],
  theme: {
    extend: {
      colors: {
        // Define your custom colors here
        'dark-lt': '#3f3f46',
        'dark-md':'#27272a',
        'dark-hi':'#18181b',
        'uci-blue-lt': '#0369a1',
        'uci-white': '#fafafa',
        'uci-yellow': '#facc15',
        primary: {"50":"#eff6ff","100":"#dbeafe","200":"#bfdbfe","300":"#93c5fd","400":"#60a5fa","500":"#3b82f6","600":"#2563eb","700":"#1d4ed8","800":"#1e40af","900":"#1e3a8a","950":"#172554"}
        // Add more custom colors as needed
      },
    },
  },
  plugins: [
    require('flowbite/plugin'),
    // require('@silvermine/videojs-airplay')(videojs)
  ],
  darkMode: 'class',
}
