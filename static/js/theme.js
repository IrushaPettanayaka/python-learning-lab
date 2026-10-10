(() => {
    const root = document.documentElement;
    const button = document.querySelector('[data-theme-toggle]');
    const label = document.querySelector('[data-theme-label]');
    const color = document.querySelector('meta[name="theme-color"]');
    if (!button || !label) return;

    function apply(theme, save = true) {
        const active = theme === 'light' ? 'light' : 'dark';
        root.dataset.theme = active;
        label.textContent = active === 'dark' ? 'Dark' : 'Light';
        button.setAttribute('aria-pressed', String(active === 'light'));
        button.setAttribute('aria-label', `Switch to ${active === 'dark' ? 'light' : 'dark'} theme`);
        if (color) color.content = active === 'dark' ? '#0b0d10' : '#f2efe8';
        if (save) {
            try { localStorage.setItem('learning-lab-theme', active); } catch (error) {}
        }
    }

    apply(root.dataset.theme, false);
    button.hidden = false;
    button.addEventListener('click', () => apply(root.dataset.theme === 'dark' ? 'light' : 'dark'));
})();
