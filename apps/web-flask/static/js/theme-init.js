(function () {
    const THEME_STORAGE_KEY = 'midi8bitTheme';
    const THEME_VALUES = ['light', 'dark'];
    const htmlElement = document.documentElement;

    function isThemeValue(value) {
        return THEME_VALUES.includes(value);
    }

    function storedTheme() {
        try {
            const value = window.localStorage.getItem(THEME_STORAGE_KEY);
            return isThemeValue(value) ? value : null;
        } catch (error) {
            return null;
        }
    }

    function systemTheme() {
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches) {
            return 'light';
        }
        return 'dark';
    }

    function applyTheme(theme) {
        const nextTheme = isThemeValue(theme) ? theme : systemTheme();
        htmlElement.setAttribute('data-bs-theme', nextTheme);
        return nextTheme;
    }

    function resolvedTheme() {
        return storedTheme() || systemTheme();
    }

    window.midi8bitTheme = {
        applyTheme,
        resolvedTheme,
        storedTheme,
        storageKey: THEME_STORAGE_KEY,
        systemTheme,
    };

    applyTheme(resolvedTheme());
}());
