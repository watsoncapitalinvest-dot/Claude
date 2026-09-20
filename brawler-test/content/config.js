// This used to be an inline <script> block in game.html. Moved to an
// external file because the entire loader depends on this code running —
// it's the thing that creates the tag that loads main.js — and if anything
// in the delivery path strips or ignores inline script content while still
// running real external script files, an inline version of this file would
// silently never execute, and nothing downstream would ever get a chance
// to either. This file has no such single point of failure: it's a normal
// script resource like any image or stylesheet on the page.
// Relative, not absolute: this page can be served from any depth (locally
// from this folder directly, or on GitHub Pages under /Claude/brawler-test/),
// and an absolute '/content/' path silently 404s every asset the moment the
// page isn't served from the domain root — with zero visible error, since a
// <script src> or fetch() 404 doesn't throw a catchable exception.
const contentPath = 'content/';
// Bump this on every deploy that changes any of these files.
const BUILD = '2026-09-20f';
window.myGame = {
    contentPath: contentPath,
    paths: {
        assetsPaths: [contentPath + 'game-test.zip?v=' + BUILD],
        'OpenBOR.zip': contentPath + 'OpenBOR.zip?v=' + BUILD,
        'game.css': contentPath + 'game.css?v=' + BUILD,
        'main.js': contentPath + 'main.js?v=' + BUILD,
        'mobile.js': contentPath + 'mobile.js?v=' + BUILD,
        'buttons.zip': contentPath + 'buttons.zip?v=' + BUILD,
        'fflate.min.js': contentPath + 'fflate.min.js?v=' + BUILD,
        'nipplejs.min.js': contentPath + 'nipplejs.min.js?v=' + BUILD,
    },
    assetType: 'zip',
    baseWidth: 320,
    baseHeight: 240,
};

const link = document.createElement('link');
link.rel = 'stylesheet';
link.href = window.myGame.paths['game.css'];
document.head.appendChild(link);

window.myGame.LoadingOverlay = document.getElementById('loading-overlay');
window.myGame.canvas = document.getElementById('canvas');
window.myGame.canvas.width = window.myGame.baseWidth;
window.myGame.canvas.height = window.myGame.baseHeight;
window.myGame.overlay = document.getElementById('overlay');
window.myGame.buttonsOverlay = document.getElementById('buttons-overlay');

var mainScript = document.createElement('script');
mainScript.src = window.myGame.paths['main.js'];
mainScript.onerror = function() {
    // A <script src> load failure (e.g. a 404 from a wrong path) does not
    // throw a catchable exception and does not reach window.onerror — it is
    // otherwise completely silent. This is the only way to surface it.
    var el = document.getElementById('loading-overlay');
    if (el) el.innerText = 'Failed to load ' + mainScript.src + ' (404 or network error).';
};
document.body.appendChild(mainScript);
