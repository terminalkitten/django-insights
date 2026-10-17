const THEME_COOKIE_MAX_AGE = 60 * 60 * 24 * 14;
const FORMULA_START = /^[=+\-@\t\r]/;

function neutralize_formula(text) {
  return FORMULA_START.test(text) && Number.isNaN(Number(text))
    ? `'${text}`
    : text;
}

function generate_csv(table_id, separator = ',') {
  const rows = document.querySelectorAll(`${table_id} tr`);
  const csv = [];
  for (const row of rows) {
    const cells = [];
    for (const col of row.querySelectorAll('td, th')) {
      let data = col.innerText
        .replace(/(\r\n|\n|\r)/gm, '')
        .replace(/(\s\s)/gm, ' ')
        .trim();
      data = neutralize_formula(data).replace(/"/g, '""');
      cells.push(`"${data}"`);
    }
    csv.push(cells.join(separator));
  }
  return csv.join('\n');
}

function download_csv(table_id) {
  const filename = `export_${table_id.replace('#', '')}_${new Date().toLocaleDateString()}.csv`;
  const link = document.createElement('a');
  link.style.display = 'none';
  link.setAttribute(
    'href',
    `data:text/csv;charset=utf-8,${encodeURIComponent(generate_csv(table_id))}`
  );
  link.setAttribute('download', filename);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

function flash_label(button, text) {
  const label = button.querySelector('span');
  const original = label.textContent;
  label.textContent = text;
  setTimeout(() => (label.textContent = original), 1500);
}

function copy_csv(button) {
  navigator.clipboard.writeText(generate_csv(button.dataset.insightsCsvCopy)).then(
    () => flash_label(button, 'Copied'),
    () => flash_label(button, 'Copy failed')
  );
}

function toggle_theme() {
  const dark = document.documentElement.classList.toggle('dark');
  document.cookie = `theme=${dark ? 'dark' : 'light'}; path=/; max-age=${THEME_COOKIE_MAX_AGE}; SameSite=Lax`;
  window.location.reload();
}

document.addEventListener('click', (event) => {
  const target = event.target;

  const opener = target.closest('[data-dialog-open]');
  if (opener) {
    document.querySelector(opener.dataset.dialogOpen)?.showModal();
    return;
  }

  const closer = target.closest('[data-dialog-close]');
  if (closer) {
    closer.closest('dialog')?.close();
    return;
  }

  if (target instanceof HTMLDialogElement) {
    target.close();
    return;
  }

  if (target.closest('[data-sidebar-toggle]')) {
    document.getElementById('sidebar')?.toggle();
    return;
  }

  if (target.closest('[data-theme-toggle]')) {
    toggle_theme();
    return;
  }

  const copy = target.closest('[data-insights-csv-copy]');
  if (copy) {
    copy_csv(copy);
    return;
  }

  const download = target.closest('[data-insights-csv-download]');
  if (download) {
    download_csv(download.dataset.insightsCsvDownload);
  }
});
