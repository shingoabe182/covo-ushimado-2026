// Cursor
const cur = document.getElementById('cur');
const curR = document.getElementById('curR');
let mx=0,my=0,rx=0,ry=0;
window.addEventListener('mousemove',e=>{
  mx=e.clientX;my=e.clientY;
  cur.style.left=mx+'px'; cur.style.top=my+'px';
});
function ringLoop(){
  rx += (mx-rx)*0.14; ry += (my-ry)*0.14;
  curR.style.left=rx+'px'; curR.style.top=ry+'px';
  requestAnimationFrame(ringLoop);
} ringLoop();
document.querySelectorAll('a, .villa, .tile, .exp-item, .btn').forEach(el=>{
  el.addEventListener('mouseenter',()=>{cur.classList.add('big');});
  el.addEventListener('mouseleave',()=>{cur.classList.remove('big');});
});

// Topbar color toggles between hero (dark) / page (white)
const topbar = document.getElementById('topbar');
const heroSentinel = document.getElementById('hero-sentinel');
const sauna = document.getElementById('sauna');
const fab = document.getElementById('reserveFab');
const cta = document.getElementById('cta');
function updateBar(){
  const heroBottom = heroSentinel.getBoundingClientRect().bottom;
  const saunaRect = sauna.getBoundingClientRect();
  const inSauna = saunaRect.top < 80 && saunaRect.bottom > 80;
  if(heroBottom > 80 || inSauna){ topbar.classList.add('on-dark'); }
  else { topbar.classList.remove('on-dark'); }
  // FAB: visible after hero scrolled past, hidden when CTA is in viewport
  const heroPast = heroBottom < window.innerHeight * 0.6;
  const ctaRect = cta.getBoundingClientRect();
  const ctaInView = ctaRect.top < window.innerHeight * 0.75 && ctaRect.bottom > 0;
  if(heroPast && !ctaInView){ fab.classList.add('show'); }
  else { fab.classList.remove('show'); }
}
window.addEventListener('scroll',updateBar,{passive:true});
window.addEventListener('resize',updateBar);
updateBar();

// Reveal
const io = new IntersectionObserver(es=>{
  es.forEach(e=>{ if(e.isIntersecting) e.target.classList.add('in'); });
},{threshold:0.12});
document.querySelectorAll('.reveal').forEach(el=>io.observe(el));

// Smooth scroll
document.querySelectorAll('a[href^="#"]').forEach(a=>{
  a.addEventListener('click',e=>{
    const id = a.getAttribute('href').slice(1);
    const t = document.getElementById(id);
    if(t){ e.preventDefault(); t.scrollIntoView({behavior:'smooth'}); }
  });
});

// Mobile Menu Trigger
const menuToggle = document.getElementById('menuToggle');
const mobileDrawer = document.getElementById('mobileDrawer');
if (menuToggle && mobileDrawer) {
  menuToggle.addEventListener('click', () => {
    document.body.classList.toggle('menu-active');
  });
  mobileDrawer.querySelectorAll('a').forEach(link => {
    link.addEventListener('click', () => {
      document.body.classList.remove('menu-active');
    });
  });
}

/* =========================================================================
   RICH MOTION LAYER
   ========================================================================= */
(function(){
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const desktop = window.matchMedia('(min-width:1024px)').matches;

  /* ---- Scroll progress bar ---- */
  const bar = document.createElement('div');
  bar.className = 'scroll-progress';
  document.body.appendChild(bar);
  function progress(){
    const h = document.documentElement.scrollHeight - window.innerHeight;
    const p = h > 0 ? (window.scrollY / h) : 0;
    bar.style.width = (p * 100) + '%';
  }

  /* ---- Tag photos for clip-path wipe-in ---- */
  ['.villa .ph', '.exp-item .ph', '.bed-photo', '.kitchen-photo',
   '.meal-photo', '.sauna-img'].forEach(sel=>{
    document.querySelectorAll(sel).forEach(el=>el.classList.add('media-reveal'));
  });

  /* ---- Tag list/grid groups for staggered children ---- */
  ['.amenity-list ul', '.kitchen-specs ul', '.exp-more-list', '.bed-specs',
   '.sched-block ul', '.access-info', '.ftr'].forEach(sel=>{
    document.querySelectorAll(sel).forEach(group=>{
      group.classList.add('js-stagger');
      Array.from(group.children).forEach((c,i)=>c.style.setProperty('--d', i));
    });
  });

  /* ---- Observe the new elements and reveal them in view ---- */
  const io2 = new IntersectionObserver(es=>{
    es.forEach(e=>{
      if(e.isIntersecting){ e.target.classList.add('in'); io2.unobserve(e.target); }
    });
  }, { threshold: 0.18, rootMargin: '0px 0px -8% 0px' });
  document.querySelectorAll('.media-reveal, .js-stagger').forEach(el=>io2.observe(el));

  /* Safety net: reveal anything already in view, and guarantee nothing
     stays unrevealed even if the observer never fires (fail-open). */
  function revealInView(){
    document.querySelectorAll('.media-reveal:not(.in), .js-stagger:not(.in)').forEach(el=>{
      const r = el.getBoundingClientRect();
      if(r.top < window.innerHeight * 0.95 && r.bottom > 0) el.classList.add('in');
    });
  }
  window.addEventListener('load', revealInView);
  setTimeout(revealInView, 600);

  /* ---- Hero parallax (subtle) ---- */
  const heroImg = document.querySelector('.hero .img');
  function parallax(){
    if(reduce || !heroImg) return;
    const y = window.scrollY;
    if(y < window.innerHeight * 1.3){
      heroImg.style.transform = 'translate3d(0,' + (y * 0.16) + 'px,0)';
    }
  }

  /* ---- rAF-throttled scroll handler ---- */
  let ticking = false;
  function onScroll(){
    if(ticking) return;
    ticking = true;
    requestAnimationFrame(()=>{ progress(); parallax(); ticking = false; });
  }
  window.addEventListener('scroll', onScroll, { passive:true });
  window.addEventListener('resize', progress);
  progress();

  /* ---- Magnetic buttons (desktop, motion-ok) ---- */
  if(desktop && !reduce){
    document.querySelectorAll('.btn, .map-link').forEach(btn=>{
      btn.addEventListener('mousemove', e=>{
        const r = btn.getBoundingClientRect();
        const x = e.clientX - r.left - r.width / 2;
        const y = e.clientY - r.top - r.height / 2;
        btn.style.transform = 'translate(' + (x * 0.25) + 'px,' + (y * 0.3) + 'px)';
      });
      btn.addEventListener('mouseleave', ()=>{ btn.style.transform = ''; });
    });
  }

  /* =======================================================================
     SIGNATURE 1 — Hero water ripple (expanding rings follow the cursor)
     ======================================================================= */
  (function ripple(){
    const hero = document.querySelector('.hero');
    if(!hero || reduce) return;
    const cv = document.createElement('canvas');
    cv.className = 'ripple-canvas';
    hero.appendChild(cv);
    const ctx = cv.getContext('2d');
    let W = 0, H = 0, dpr = Math.min(window.devicePixelRatio || 1, 2);
    function size(){
      const r = hero.getBoundingClientRect();
      W = r.width; H = r.height;
      cv.width = W * dpr; cv.height = H * dpr;
      cv.style.width = W + 'px'; cv.style.height = H + 'px';
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }
    size();
    window.addEventListener('resize', size);

    const drops = [];
    function drop(x, y, strong){
      drops.push({ x, y, r: 2, max: strong ? 170 : 120, a: strong ? 0.5 : 0.32 });
    }
    let lx = 0, ly = 0;
    hero.addEventListener('mousemove', e=>{
      const r = hero.getBoundingClientRect();
      const x = e.clientX - r.left, y = e.clientY - r.top;
      if(Math.hypot(x - lx, y - ly) > 34){ drop(x, y, false); lx = x; ly = y; }
    });
    hero.addEventListener('click', e=>{
      const r = hero.getBoundingClientRect();
      drop(e.clientX - r.left, e.clientY - r.top, true);
    });
    // ambient drops, lower half (the "sea")
    setInterval(()=>{ if(visible && drops.length < 14) drop(Math.random()*W, H*(0.6+Math.random()*0.35), false); }, 1400);

    let visible = true;
    new IntersectionObserver(es=>{ visible = es[0].isIntersecting; },{threshold:0.02}).observe(hero);

    function frame(){
      ctx.clearRect(0, 0, W, H);
      for(let i = drops.length - 1; i >= 0; i--){
        const d = drops[i];
        d.r += (d.max - d.r) * 0.045;
        d.a *= 0.972;
        if(d.a < 0.012 || d.r > d.max - 1){ drops.splice(i, 1); continue; }
        ctx.beginPath();
        ctx.arc(d.x, d.y, d.r, 0, Math.PI * 2);
        ctx.strokeStyle = 'rgba(255,255,255,' + d.a + ')';
        ctx.lineWidth = 1.1;
        ctx.stroke();
        ctx.beginPath();
        ctx.arc(d.x, d.y, d.r * 0.62, 0, Math.PI * 2);
        ctx.strokeStyle = 'rgba(201,176,128,' + (d.a * 0.6) + ')';
        ctx.lineWidth = 0.8;
        ctx.stroke();
      }
      requestAnimationFrame(frame);
    }
    frame();
  })();

  /* =======================================================================
     SIGNATURE 2 — Venus Road tide reveal (first Experience card)
     ======================================================================= */
  (function tide(){
    const card = document.querySelector('.exp-row .exp-item') ||
                 document.querySelector('a.exp-item[href*="11144"]');
    if(!card) return;
    const ph = card.querySelector('.ph');
    if(!ph) return;
    card.classList.add('tide');
    const water = document.createElement('div');
    water.className = 'tide-water';
    const hint = document.createElement('div');
    hint.className = 'tide-hint';
    hint.textContent = '— 潮が引く';
    ph.appendChild(water);
    ph.appendChild(hint);
  })();

  /* =======================================================================
     SIGNATURE 3 — Sauna heat haze (animated SVG displacement filter)
     ======================================================================= */
  (function heat(){
    const img = document.querySelector('.sauna-img');
    if(!img || reduce) return;
    const ns = 'http://www.w3.org/2000/svg';
    const svg = document.createElementNS(ns, 'svg');
    svg.setAttribute('class', 'svg-defs');
    svg.innerHTML =
      '<defs><filter id="heatHaze" x="-12%" y="-12%" width="124%" height="124%">' +
      '<feTurbulence type="fractalNoise" baseFrequency="0.012 0.028" numOctaves="2" seed="7" result="n">' +
      '<animate attributeName="baseFrequency" dur="14s" values="0.012 0.028;0.014 0.05;0.012 0.028" repeatCount="indefinite"/>' +
      '</feTurbulence>' +
      '<feDisplacementMap in="SourceGraphic" in2="n" scale="7" xChannelSelector="R" yChannelSelector="G"/>' +
      '</filter></defs>';
    document.body.appendChild(svg);
    img.classList.add('heat-on');
    // only run the filter while the sauna is on-screen (perf)
    new IntersectionObserver(es=>{
      img.style.filter = es[0].isIntersecting ? 'url(#heatHaze)' : 'none';
    }, { threshold: 0.05 }).observe(img);
  })();

  /* =======================================================================
     SIGNATURE 4 — GPS typewriter coordinates
     ======================================================================= */
  (function gps(){
    const stamp = document.querySelector('.hero-top .stamp');
    if(!stamp) return;
    const lines = stamp.innerHTML.split(/<br\s*\/?>/i);
    const coord = (lines[0] || 'N 34.62° E 134.16°')
      .replace(/<[^>]*>/g, '').replace(/&nbsp;/g, ' ').replace(/\s+/g, ' ').trim();
    const rest = lines.slice(1).join('<br>');
    stamp.innerHTML = '<span class="gps-line"><span class="gps-text"></span>' +
      '<span class="gps-caret">|</span></span>' + (rest ? '<br>' + rest : '');
    const out = stamp.querySelector('.gps-text');
    const caret = stamp.querySelector('.gps-caret');
    if(reduce){ out.textContent = coord; caret.classList.add('done'); return; }
    let i = 0;
    setTimeout(function tick(){
      if(i <= coord.length){
        out.textContent = coord.slice(0, i);
        i++;
        setTimeout(tick, 55 + Math.random() * 45);
      } else {
        setTimeout(()=>caret.classList.add('done'), 1600);
      }
    }, 1000);
  })();

  /* ---- Smooth FAQ accordion ---- */
  document.querySelectorAll('.faq-item').forEach(item=>{
    const summary = item.querySelector('summary');
    const panel = item.querySelector('p');
    if(!summary || !panel) return;
    panel.style.overflow = 'hidden';
    panel.style.transition = 'max-height .55s cubic-bezier(.2,.8,.2,1), opacity .5s ease';
    summary.addEventListener('click', e=>{
      e.preventDefault();
      const open = item.hasAttribute('open');
      if(open){
        panel.style.maxHeight = panel.scrollHeight + 'px';
        requestAnimationFrame(()=>{ panel.style.maxHeight = '0px'; panel.style.opacity = '0'; });
        panel.addEventListener('transitionend', function te(){
          item.removeAttribute('open');
          panel.style.maxHeight = ''; panel.style.opacity = '';
          panel.removeEventListener('transitionend', te);
        }, { once:true });
      } else {
        item.setAttribute('open','');
        panel.style.maxHeight = '0px'; panel.style.opacity = '0';
        requestAnimationFrame(()=>{
          panel.style.maxHeight = panel.scrollHeight + 'px';
          panel.style.opacity = '1';
        });
        panel.addEventListener('transitionend', function te(){
          panel.style.maxHeight = '';
          panel.removeEventListener('transitionend', te);
        }, { once:true });
      }
    });
  });
})();
