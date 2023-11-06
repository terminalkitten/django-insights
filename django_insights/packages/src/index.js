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

  // Enable CSV copy
  const copyButtons = document.querySelectorAll('[data-insights-csv-copy]');

  copyButtons.forEach((btn) => {
    btn.addEventListener('click', () => {
      const tableId = btn.getAttribute('data-insights-csv-copy');
      copy_csv(tableId);
    });
  });

  // Enable CSV downloads
  const downloadButtons = document.querySelectorAll(
    '[data-insights-csv-download]'
  );

  downloadButtons.forEach((btn) => {
    btn.addEventListener('click', () => {
      const tableId = btn.getAttribute('data-insights-csv-download');
      download_csv(tableId);
    });
  });
});

function generate_csv(table_id, separator = ',') {
  // Select rows from table_id
  var rows = document.querySelectorAll(`${table_id} tr`);
  // Construct csv
  var csv = [];
  for (var i = 0; i < rows.length; i++) {
    var row = [],
      cols = rows[i].querySelectorAll('td, th');
    for (var j = 0; j < cols.length; j++) {
      // Clean innertext to remove multiple spaces and jumpline (break csv)
      var data = cols[j].innerText
        .replace(/(\r\n|\n|\r)/gm, '')
        .replace(/(\s\s)/gm, ' ');
      // Escape double-quote with double-double-quote (see https://stackoverflow.com/questions/17808511/properly-escape-a-double-quote-in-csv)
      data = data.replace(/"/g, '""');
      // Push escaped string
      row.push('"' + data + '"');
    }
    csv.push(row.join(separator));
  }
  return csv.join('\n');
}

function download_csv(tableId) {
  var csv_string = generate_csv(tableId);

  // Download it
  const filename =
    'export_' +
    tableId.replace('#', '') +
    '_' +
    new Date().toLocaleDateString() +
    '.csv';
  const link = document.createElement('a');
  link.style.display = 'none';
  link.setAttribute('target', '_blank');
  link.setAttribute(
    'href',
    'data:text/csv;charset=utf-8,' + encodeURIComponent(csv_string)
  );
  link.setAttribute('download', filename);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

function copy_csv(tableId) {
  var csv_string = generate_csv(tableId);
  navigator.clipboard.writeText(csv_string).then(
    () => {
      const dataCopiedMsg = document.getElementById('data-copied-msg');
      dataCopiedMsg.classList.remove('hidden');
    },
    (err) => {
      alert('Er ging iets mis', err);
    }
  );
}
