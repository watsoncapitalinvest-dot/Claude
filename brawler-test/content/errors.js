// There is no way to see the browser console on a phone, so any error that
// happens during load — WASM failure, a blocked Worker, a failed fetch,
// anything — has to be written straight onto the loading screen itself, or
// it's invisible and looks exactly like a generic hang. This file is loaded
// as a plain external script (not inline) so it still runs even in an
// environment that strips inline <script> content.
window.addEventListener('error', function(e) {
    var el = document.getElementById('loading-overlay');
    if (el && el.style.display !== 'none') {
        el.innerText = 'LOAD ERROR: ' + (e.message || e.error || e) +
            (e.filename ? ('\n' + e.filename + ':' + e.lineno) : '');
    }
});
window.addEventListener('unhandledrejection', function(e) {
    var el = document.getElementById('loading-overlay');
    if (el && el.style.display !== 'none') {
        var reason = e.reason && e.reason.message ? e.reason.message : String(e.reason);
        el.innerText = 'LOAD ERROR (promise): ' + reason;
    }
});
