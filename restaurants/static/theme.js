// localStorage helper functions
function getStorage(name) {
    return localStorage.getItem(name);
}

function setStorage(name, value) {
    localStorage.setItem(name, value);
}

// Restore dark mode before paint to avoid flash
const saved = getStorage('darkMode');
const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
if (saved === 'true' || (saved === null && prefersDark)) {
    document.documentElement.classList.add('dark');
}

