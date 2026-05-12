(function () {
    /*
     * Inline Lucide SVGs used by the Flask UI.
     * Source: https://lucide.dev/ and https://github.com/lucide-icons/lucide
     * License: ISC License, Copyright (c) 2026 Lucide Icons and Contributors.
     * Some icons, including x, are derived from Feather Icons under the MIT License,
     * Copyright (c) 2013-present Cole Bemis. See docs/licensing-audit.md.
     */
    const baseAttributes = 'xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" focusable="false"';
    const icons = {
        languages: '<path d="m5 8 6 6"></path><path d="m4 14 6-6 2-3"></path><path d="M2 5h12"></path><path d="M7 2h1"></path><path d="m22 22-5-10-5 10"></path><path d="M14 18h6"></path>',
        'moon-star': '<path d="M18 5h4"></path><path d="M20 3v4"></path><path d="M20.985 12.486a9 9 0 1 1-9.473-9.472c.405-.022.617.46.402.803a6 6 0 0 0 8.268 8.268c.344-.215.825-.004.803.401"></path>',
        play: '<polygon points="6 3 20 12 6 21 6 3"></polygon>',
        sun: '<circle cx="12" cy="12" r="4"></circle><path d="M12 2v2"></path><path d="M12 20v2"></path><path d="m4.93 4.93 1.41 1.41"></path><path d="m17.66 17.66 1.41 1.41"></path><path d="M2 12h2"></path><path d="M20 12h2"></path><path d="m6.34 17.66-1.41 1.41"></path><path d="m19.07 4.93-1.41 1.41"></path>',
        x: '<path d="M18 6 6 18"></path><path d="m6 6 12 12"></path>',
    };

    function svg(name, className = 'lucide-icon') {
        if (!Object.prototype.hasOwnProperty.call(icons, name)) {
            return '';
        }

        return `<svg class="${className}" ${baseAttributes}>${icons[name]}</svg>`;
    }

    window.octabitLucideIcons = {
        svg,
    };
}());
