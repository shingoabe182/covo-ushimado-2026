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
