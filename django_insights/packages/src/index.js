import 'preline';

function setCookie(theme) {
  document.cookie = `theme=${theme}; path=/; max-age=${60 * 60 * 24 * 14};`;
}

function getCookie(name) {
  let value = `; ${document.cookie}`;
  let parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
}

function darkMode(theme) {
  const element = document.getElementById('html-root');
  if (theme == 'light') {
    element.classList.remove('dark');
  } else {
    element.classList.add('dark');
  }
}

function toggleDarkMode() {
  const element = document.getElementById('html-root');
  if (element.classList.contains('dark')) {
    element.classList.remove('dark');
    return 'light';
  } else {
    element.classList.add('dark');
    return 'dark';
  }
}

document.addEventListener('DOMContentLoaded', function () {
  // set theme
  const theme = getCookie('theme');
  darkMode(theme);

  const button = document.getElementById('mode-toggle');

  button.addEventListener('click', (event) => {
    const theme = toggleDarkMode();
    setCookie(theme);
    window.location.reload();
  });
});
