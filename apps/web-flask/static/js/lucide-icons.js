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
        play: '<polygon points="6 3 20 12 6 21 6 3"></polygon>',
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
