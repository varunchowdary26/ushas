/* =========================================================
   CINEMATIC SLOW-MOTION PAGE TRANSITION ENGINE
   Ushas Herbal Beauty Parlour
========================================================= */

(function () {
    // 1. Create and inject overlay if not present
    function ensureOverlay() {
        let overlay = document.getElementById('cinematic-overlay');
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.id = 'cinematic-overlay';
            overlay.innerHTML = `
                <div class="cinematic-bar"></div>
                <div class="cinematic-sparkle">✦</div>
                <div class="cinematic-text">Ushas Herbal Beauty Parlour</div>
            `;
            if (document.body) {
                document.body.prepend(overlay);
            }
        }
        return overlay;
    }

    // 2. Play page entry on DOM ready
    function handlePageEntry() {
        if (!document.body) return;
        document.body.classList.add('cinematic-entry-ready');
        const overlay = document.getElementById('cinematic-overlay');
        if (overlay) {
            overlay.classList.remove('active');
        }
        // Clean up entry class after bloom finishes
        setTimeout(() => {
            if (document.body) {
                document.body.classList.remove('cinematic-entry-ready');
            }
        }, 1200);
    }

    // 3. Cinematic programmatic navigation
    window.cinematicNavigate = function (url) {
        if (!url) return;
        const overlay = ensureOverlay();
        document.body.classList.add('is-transitioning');
        if (overlay) {
            overlay.classList.add('active');
        }

        // Cinematic slow-motion transition pause
        setTimeout(() => {
            window.location.href = url;
        }, 750);
    };

    // 4. Intercept internal page link clicks
    function setupLinkInterception() {
        document.addEventListener('click', function (e) {
            const link = e.target.closest('a');
            if (!link) return;

            const href = link.getAttribute('href');
            if (!href) return;

            // In-page hash anchors (e.g. #services, #booking)
            if (href.startsWith('#')) return;

            // External protocols or special targets
            if (
                href.startsWith('javascript:') ||
                href.startsWith('tel:') ||
                href.startsWith('mailto:') ||
                link.target === '_blank' ||
                link.hasAttribute('download') ||
                e.ctrlKey || e.metaKey || e.shiftKey || e.altKey
            ) {
                return;
            }

            let targetUrl;
            try {
                targetUrl = new URL(link.href, window.location.href);
            } catch (err) {
                return;
            }

            // Only internal links on the same host
            if (targetUrl.origin !== window.location.origin) return;

            // Normalize pathnames for comparison
            const currentPath = window.location.pathname.replace(/\/$/, '') || '/';
            const destPath = targetUrl.pathname.replace(/\/$/, '') || '/';

            // Same page hash navigation (e.g. index.html#booking while on index.html)
            if (currentPath === destPath && targetUrl.search === window.location.search && targetUrl.hash) {
                return;
            }

            // Same exact URL with no hash
            if (currentPath === destPath && targetUrl.search === window.location.search && !targetUrl.hash) {
                return;
            }

            // Prevent default hard navigation and play cinematic transition!
            e.preventDefault();
            window.cinematicNavigate(link.href);
        });
    }

    // 5. Initialize on load & handle BFCache (Back/Forward navigation)
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            ensureOverlay();
            handlePageEntry();
            setupLinkInterception();
        });
    } else {
        ensureOverlay();
        handlePageEntry();
        setupLinkInterception();
    }

    window.addEventListener('pageshow', (event) => {
        // Reset transition states when restored from browser cache
        if (document.body) {
            document.body.classList.remove('is-transitioning');
        }
        const overlay = document.getElementById('cinematic-overlay');
        if (overlay) {
            overlay.classList.remove('active');
        }
        handlePageEntry();
    });
})();
