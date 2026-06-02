// Cookie helper functions
function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
}

function setCookie(name, value, days = 365) {
    const date = new Date();
    date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
    const expires = `expires=${date.toUTCString()}`;
    document.cookie = `${name}=${value};${expires};path=/`;
}

// Restore dark mode before paint to avoid flash
const saved = getCookie('darkMode');
const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
if (saved === 'true' || (saved === null && prefersDark)) {
    document.documentElement.classList.add('dark');
}
