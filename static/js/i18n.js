// i18n.js – simple language switcher
// Loads translation JSON files from /static/lang/ and updates text elements using data-i18n keys.

(function () {
  const LANG_KEY = 'vampire_lang';
  const defaultLang = 'zh-Hant';
  const supported = ['zh-Hant', 'zh-Hans', 'en'];

  function getLang() {
    const stored = localStorage.getItem(LANG_KEY);
    if (stored && supported.includes(stored)) return stored;
    return defaultLang;
  }

  function setLang(lang) {
    if (!supported.includes(lang)) return;
    localStorage.setItem(LANG_KEY, lang);
    loadTranslations(lang);
    updateButtons(lang);
  }

  function loadTranslations(lang) {
    fetch(`/static/lang/${lang}.json`)
      .then(r => r.json())
      .then(data => {
        document.querySelectorAll('[data-i18n]').forEach(el => {
          const key = el.getAttribute('data-i18n');
          if (data[key]) el.innerHTML = data[key];
        });
        // Update language button active state
        document.querySelectorAll('.nav-lang-btn').forEach(btn => {
          btn.classList.toggle('active', btn.dataset.lang === lang);
          btn.setAttribute('aria-selected', btn.dataset.lang === lang);
        });
      })
      .catch(() => console.warn('[i18n] Failed to load translation for', lang));
  }

  function updateButtons(lang) {
    // No extra UI needed beyond active class handled in loadTranslations
  }

  // Attach click listeners to language buttons
  document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.nav-lang-btn').forEach(btn => {
      btn.addEventListener('click', () => setLang(btn.dataset.lang));
    });
    // Initialise language on page load
    loadTranslations(getLang());
  });
})();
