/**
 * Theme Preload Script
 * Applies theme immediately before page render to prevent flashing
 */
(function() {
  // Constants
  const THEME_KEY = 'hr-theme-preference';
  const DARK_MODE_CLASS = 'dark-mode';
  const LIGHT_THEME = 'light';
  const DARK_THEME = 'dark';
  const AUTO_THEME = 'auto';
  
  // Get saved theme preference
  function getSavedTheme() {
    return localStorage.getItem(THEME_KEY) || AUTO_THEME;
  }
  
  // Check if system prefers dark mode
  function systemPrefersDarkMode() {
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  }
  
  // Apply theme immediately
  function applyThemeImmediately() {
    const savedTheme = getSavedTheme();
    let effectiveTheme = savedTheme;
    
    // If theme is auto, determine based on system preference
    if (savedTheme === AUTO_THEME) {
      effectiveTheme = systemPrefersDarkMode() ? DARK_THEME : LIGHT_THEME;
    }
    
    // Apply theme
    if (effectiveTheme === DARK_THEME) {
      document.documentElement.classList.add(DARK_MODE_CLASS);
      document.documentElement.setAttribute('data-bs-theme', 'dark');
    } else {
      document.documentElement.classList.remove(DARK_MODE_CLASS);
      document.documentElement.setAttribute('data-bs-theme', 'light');
    }
  }
  
  // Apply theme immediately
  applyThemeImmediately();
  
  // Add transition class after DOM is loaded to enable smooth transitions for future changes
  document.addEventListener('DOMContentLoaded', function() {
    // Short delay to ensure page has rendered before adding transitions
    setTimeout(function() {
      document.documentElement.classList.add('theme-transition-ready');
    }, 100);
  });
})();
