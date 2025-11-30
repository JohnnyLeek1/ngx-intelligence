(function() {
  try {
    const theme = localStorage.getItem('ngx-intelligence-theme') || 'system';
    const isDark = theme === 'dark';
    const isSystem = theme === 'system';
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

    if (isDark || (isSystem && prefersDark)) {
      document.documentElement.classList.add('dark');
    }
  } catch (e) {
    console.error('Error applying theme:', e);
  }
})();
