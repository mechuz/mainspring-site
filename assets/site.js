/* Mainspring — shared behaviour: scroll reveals, sticky conversion bar, nav state. */
(function () {
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* reveal on scroll */
  /* failsafe: whatever happens, nothing stays hidden for more than 2.5s */
  setTimeout(function () {
    document.querySelectorAll('.reveal:not(.in)').forEach(function (el) { el.classList.add('in'); });
  }, 2500);

  var items = document.querySelectorAll('.reveal');
  if (!items.length) { /* nothing */ }
  else if (reduce || !('IntersectionObserver' in window)) {
    items.forEach(function (el) { el.classList.add('in'); });
  } else {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); }
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });
    items.forEach(function (el) { io.observe(el); });
  }

  /* sticky conversion bar — appears after the first screen, hides over the footer CTA */
  var bar = document.querySelector('.sticky-cta');
  var nav = document.querySelector('header.nav');
  var foot = document.querySelector('footer.ft');
  function onScroll() {
    var y = window.pageYOffset || document.documentElement.scrollTop;
    if (nav) nav.classList.toggle('scrolled', y > 24);
    if (bar) {
      var nearEnd = foot && foot.getBoundingClientRect().top < window.innerHeight + 120;
      bar.classList.toggle('up', y > window.innerHeight * 0.75 && !nearEnd);
    }
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();
})();

/* ---------------------------------------------------------------------------
   Form fallback. Formspree IDs are not wired yet (two are pending from Max).
   Until they are, every form still works: the submit is intercepted and turned
   into a pre-filled email to the partner inbox, so no lead is ever lost.
   Once action= holds a real Formspree URL this handler steps aside.
   --------------------------------------------------------------------------- */
(function () {
  var TO = 'db@mainspringhcp.com';
  document.querySelectorAll('form.site-form').forEach(function (form) {
    var action = form.getAttribute('action') || '';
    var wired = action.indexOf('formspree.io/f/') > -1 && action.indexOf('YOUR_ID') === -1;
    if (wired) return;

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var honey = form.getAttribute('netlify-honeypot') || 'company';
      var data = new FormData(form);
      var lines = [];
      var seen = {};
      data.forEach(function (v, k) {
        if (k === 'form-name' || k === honey || !String(v).trim()) return;
        if (seen[k]) { seen[k].push(v); } else { seen[k] = [v]; }
      });
      Object.keys(seen).forEach(function (k) {
        var label = k.charAt(0).toUpperCase() + k.slice(1).replace(/[-_]/g, ' ');
        lines.push(label + ': ' + seen[k].join(', '));
      });
      var subject = form.getAttribute('data-subject') || 'Website enquiry';
      var href = 'mailto:' + TO +
        '?subject=' + encodeURIComponent(subject) +
        '&body=' + encodeURIComponent(lines.join('\n') + '\n\n— sent from mainspringhcp.com');
      var status = form.querySelector('.form-status');
      if (status) {
        status.textContent = 'Opening your email app with this message ready to send to ' + TO + '.';
        status.classList.add('on');
      }
      window.location.href = href;
    });
  });
})();

/* ---------------------------------------------------------------------------
   First-screen panels. The cursor-following highlight, the press state, and
   full keyboard operation (each panel is a link, so Enter works natively —
   this only adds the spacebar and the pressed animation).
   --------------------------------------------------------------------------- */
(function () {
  var panels = document.querySelectorAll('.pnl');
  if (!panels.length) return;
  var fine = window.matchMedia('(hover: hover) and (pointer: fine)').matches;

  panels.forEach(function (p) {
    if (fine) {
      p.addEventListener('pointermove', function (e) {
        var r = p.getBoundingClientRect();
        p.style.setProperty('--mx', ((e.clientX - r.left) / r.width) * 100 + '%');
        p.style.setProperty('--my', ((e.clientY - r.top) / r.height) * 100 + '%');
      });
    }
    var press = function () { p.classList.add('pressed'); };
    var release = function () { p.classList.remove('pressed'); };
    p.addEventListener('pointerdown', press);
    p.addEventListener('pointerup', release);
    p.addEventListener('pointercancel', release);
    p.addEventListener('pointerleave', release);
    p.addEventListener('keydown', function (e) {
      if (e.key === ' ') { e.preventDefault(); press(); }
    });
    p.addEventListener('keyup', function (e) {
      if (e.key === ' ') { release(); p.click(); }
    });
  });
})();

/* Ripple on pill buttons — the Chocham touch feedback. */
(function () {
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  document.addEventListener('pointerdown', function (e) {
    var btn = e.target.closest ? e.target.closest('.btn') : null;
    if (!btn) return;
    var r = btn.getBoundingClientRect();
    var d = Math.max(r.width, r.height) * 2;
    var s = document.createElement('span');
    s.className = 'rip';
    s.style.width = s.style.height = d + 'px';
    s.style.left = (e.clientX - r.left - d / 2) + 'px';
    s.style.top = (e.clientY - r.top - d / 2) + 'px';
    btn.appendChild(s);
    setTimeout(function () { s.remove(); }, 700);
  });
})();
