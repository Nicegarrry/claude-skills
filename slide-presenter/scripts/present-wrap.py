#!/usr/bin/env python3
"""present-wrap.py — wrap a static HTML deck in a self-contained presentation viewer.

Takes an HTML file that contains one or more fixed-size slide elements (default
selector: elements with class "slide", as produced by consulting-style deck
renderers — each a 1280x720 stage) and injects a screen-only presentation layer:

  - fullscreen one-slide-at-a-time view, scaled to fit the viewport
  - arrow-key / space / PageUp-Down / Home / End navigation + on-screen buttons
  - a thumbnail "switcher" grid (button or press g; Esc / back to return)
  - a fullscreen toggle (button or press f)

The slide markup and any existing @media print rules are left untouched, so the
file still prints one slide per page. Output is a single self-contained HTML file
ready to host (e.g. via the here-now skill).

Usage:
  present-wrap.py --in deck.html [--out deck.present.html]
  present-wrap.py --in deck.html --in-place
  present-wrap.py --in deck.html --slide-class slide

If --out is omitted and --in-place is not set, writes <name>.present.html next to
the input and prints the path.
"""
import argparse, pathlib, sys

CSS = r"""
<style id="pv-style">
/* ===== slide-presenter viewer (screen only; print keeps stacked slides) ===== */
@media screen {
  html, body { margin:0; height:100%; background:#0b0d10; }
  body { overflow:hidden; }
  body.pv-grid { overflow:auto; }

  /* present mode */
  body.pv-present .pv-deck { position:fixed; inset:0; display:block; padding:0; gap:0; background:#0b0d10; }
  body.pv-present .pv-slide {
    position:absolute; left:50%; top:50%;
    transform:translate(-50%,-50%) scale(var(--pv-scale,1)); transform-origin:center center;
    opacity:0; visibility:hidden; pointer-events:none; transition:opacity .18s ease;
    box-shadow:0 18px 60px rgba(0,0,0,.55);
  }
  body.pv-present .pv-slide.pv-active { opacity:1; visibility:visible; pointer-events:auto; }

  /* grid / switcher mode (transform-scale + negative margin collapses the footprint) */
  body.pv-grid .pv-deck {
    position:static; display:grid;
    grid-template-columns:repeat(auto-fill, calc(1280px * var(--pv-ts)));
    justify-content:center; align-content:start; gap:26px; padding:70px 28px 96px; background:#0b0d10;
    --pv-ts:.28;
  }
  body.pv-grid .pv-slide {
    position:relative; left:auto; top:auto; width:1280px; height:720px;
    opacity:1; visibility:visible; pointer-events:auto;
    transform:scale(var(--pv-ts)); transform-origin:top left;
    margin:0 calc(1280px * (var(--pv-ts) - 1)) calc(720px * (var(--pv-ts) - 1)) 0;
    cursor:pointer; outline:3px solid transparent; outline-offset:6px;
    transition:outline-color .12s; box-shadow:0 12px 34px rgba(0,0,0,.5);
  }
  body.pv-grid .pv-slide:hover { outline-color:var(--accent,#5A8FCC); }
  @media screen and (min-width:1700px){ body.pv-grid .pv-deck { --pv-ts:.24; } }
  @media screen and (max-width:1100px){ body.pv-grid .pv-deck { --pv-ts:.34; } }

  /* controls */
  .pv-bar { position:fixed; bottom:18px; left:50%; transform:translateX(-50%); z-index:60;
    display:flex; align-items:center; gap:6px; padding:7px 10px; border-radius:999px;
    background:rgba(18,22,28,.82); -webkit-backdrop-filter:blur(8px); backdrop-filter:blur(8px);
    box-shadow:0 6px 24px rgba(0,0,0,.4); border:1px solid rgba(255,255,255,.08); }
  .pv-btn { display:grid; place-items:center; width:34px; height:34px; border:0; border-radius:50%;
    background:transparent; color:#E7ECF3; cursor:pointer; padding:0; }
  .pv-btn:hover { background:rgba(255,255,255,.12); }
  .pv-btn svg { width:19px; height:19px; display:block; }
  .pv-count { font:600 13px/1 ui-monospace,"JetBrains Mono",monospace; color:#E7ECF3; padding:0 8px; min-width:56px; text-align:center; }
  .pv-sep { width:1px; height:20px; background:rgba(255,255,255,.14); margin:0 3px; }
  .pv-back { position:fixed; top:16px; left:16px; z-index:60; display:none; align-items:center; gap:6px;
    padding:8px 14px 8px 11px; border-radius:999px; border:1px solid rgba(255,255,255,.1);
    background:rgba(18,22,28,.82); color:#E7ECF3; font:600 13px system-ui,sans-serif; cursor:pointer; }
  .pv-back:hover { background:rgba(28,34,42,.92); }
  .pv-back svg { width:16px; height:16px; }
  .pv-hint { position:fixed; top:22px; left:50%; transform:translateX(-50%); z-index:60; display:none;
    color:#9AA7B5; font:600 13px system-ui,sans-serif; }
  body.pv-grid .pv-bar { display:none; }
  body.pv-grid .pv-back, body.pv-grid .pv-hint { display:flex; }
}
@media print { .pv-bar, .pv-back, .pv-hint { display:none !important; } }
</style>
"""

CHEVL = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M15.75 19.5 8.25 12l7.5-7.5"/></svg>'
CHEVR = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="m8.25 4.5 7.5 7.5-7.5 7.5"/></svg>'
GRID  = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3.5" y="3.5" width="7" height="7" rx="1.3"/><rect x="13.5" y="3.5" width="7" height="7" rx="1.3"/><rect x="3.5" y="13.5" width="7" height="7" rx="1.3"/><rect x="13.5" y="13.5" width="7" height="7" rx="1.3"/></svg>'
FULL  = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3.75 8.25v-4.5h4.5M20.25 8.25v-4.5h-4.5M3.75 15.75v4.5h4.5M20.25 15.75v4.5h-4.5"/></svg>'

CONTROLS = f"""
<div class="pv-hint">Overview — click any slide, or press Esc</div>
<button id="pv-back" class="pv-back" aria-label="Back to slideshow" type="button">{CHEVL}<span>Slideshow</span></button>
<div class="pv-bar" role="toolbar" aria-label="Slide controls">
  <button id="pv-prev" class="pv-btn" aria-label="Previous slide" type="button">{CHEVL}</button>
  <span id="pv-count" class="pv-count">1 / 1</span>
  <button id="pv-next" class="pv-btn" aria-label="Next slide" type="button">{CHEVR}</button>
  <span class="pv-sep"></span>
  <button id="pv-gridbtn" class="pv-btn" aria-label="Overview of all slides" type="button">{GRID}</button>
  <button id="pv-fullbtn" class="pv-btn" aria-label="Toggle fullscreen" type="button">{FULL}</button>
</div>
"""

def script(slide_class):
    return r"""
<script>
(function(){
  var SEL = '%SEL%';
  var slides = Array.prototype.slice.call(document.querySelectorAll(SEL));
  if(!slides.length) return;
  // tag slides + ensure a deck container class for scoping
  slides.forEach(function(s){ s.classList.add('pv-slide'); });
  var deck = slides[0].parentElement;
  if(deck) deck.classList.add('pv-deck');
  var count = document.getElementById('pv-count');
  var idx = 0;
  function fit(){
    var s = Math.min((window.innerWidth - 48)/1280, (window.innerHeight - 104)/720);
    document.documentElement.style.setProperty('--pv-scale', (s>0?s:1).toFixed(4));
  }
  function render(){
    for (var i=0;i<slides.length;i++) slides[i].classList.toggle('pv-active', i===idx);
    if (count) count.textContent = (idx+1)+' / '+slides.length;
  }
  function go(n){ idx = Math.max(0, Math.min(slides.length-1, n)); render(); }
  function present(){ document.body.classList.remove('pv-grid'); document.body.classList.add('pv-present'); window.scrollTo(0,0); fit(); render(); }
  function grid(){ document.body.classList.remove('pv-present'); document.body.classList.add('pv-grid'); }
  function toggleGrid(){ document.body.classList.contains('pv-grid') ? present() : grid(); }
  function full(){ try { if(!document.fullscreenElement){ document.documentElement.requestFullscreen(); } else { document.exitFullscreen(); } } catch(e){} }
  slides.forEach(function(s,i){ s.addEventListener('click', function(){ if(document.body.classList.contains('pv-grid')){ idx=i; present(); } }); });
  window.addEventListener('keydown', function(e){
    var g = document.body.classList.contains('pv-grid');
    if (e.key==='ArrowRight'||e.key==='PageDown'||e.key===' '){ if(!g){ go(idx+1); e.preventDefault(); } }
    else if (e.key==='ArrowLeft'||e.key==='PageUp'){ if(!g){ go(idx-1); e.preventDefault(); } }
    else if (e.key==='Home'){ go(0); }
    else if (e.key==='End'){ go(slides.length-1); }
    else if (e.key==='g'||e.key==='G'){ toggleGrid(); }
    else if (e.key==='Escape'){ if(g) present(); }
    else if (e.key==='f'||e.key==='F'){ full(); }
  });
  window.addEventListener('resize', function(){ if(document.body.classList.contains('pv-present')) fit(); });
  document.getElementById('pv-prev').onclick = function(){ go(idx-1); };
  document.getElementById('pv-next').onclick = function(){ go(idx+1); };
  document.getElementById('pv-gridbtn').onclick = toggleGrid;
  document.getElementById('pv-fullbtn').onclick = full;
  document.getElementById('pv-back').onclick = present;
  present();
})();
</script>
""".replace('%SEL%', slide_class)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", dest="out")
    ap.add_argument("--in-place", action="store_true")
    ap.add_argument("--slide-class", default="slide",
                    help="CSS class identifying each slide element (default: slide)")
    a = ap.parse_args()

    src = pathlib.Path(a.inp)
    html = src.read_text()
    sel = "." + a.slide_class.lstrip(".")
    if "</head>" not in html or "</body>" not in html:
        sys.exit("input is missing </head> or </body>; expected a full HTML document")
    if "pv-style" in html:
        print("already wrapped (pv-style present); leaving as-is", file=sys.stderr)
    else:
        html = html.replace("</head>", CSS + "</head>", 1)
        html = html.replace("</body>", CONTROLS + script(sel) + "</body>", 1)

    if a.in_place:
        out = src
    elif a.out:
        out = pathlib.Path(a.out)
    else:
        out = src.with_suffix(".present.html")
    out.write_text(html)
    print(str(out))

if __name__ == "__main__":
    main()
