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
   Intake forms — same pattern as the Kirby Gate site.
   Every form posts to FormSubmit. 1) Submit in the background through the AJAX
   endpoint and send the visitor to /thank-you/ ourselves. 2) If that fails
   (FormSubmit down, address not yet activated, no network) fall back to a
   pre-filled email to the partner inbox, so no enquiry is ever lost.
   --------------------------------------------------------------------------- */
(function () {
  var TO = 'info@mainspringhcp.com';
  function lines(form) {
    var seen = {}, out = [];
    new FormData(form).forEach(function (v, k) {
      if (k.charAt(0) === '_' || !String(v).trim()) return;
      (seen[k] = seen[k] || []).push(v);
    });
    Object.keys(seen).forEach(function (k) {
      out.push(k.charAt(0).toUpperCase() + k.slice(1).replace(/[-_]/g, ' ') + ': ' + seen[k].join(', '));
    });
    return out.join('\n');
  }
  function status(form, msg) {
    var el = form.querySelector('.form-status');
    if (!el) return;
    el.textContent = msg || '';
    el.classList.toggle('on', !!msg);
  }
  function mailtoFallback(form) {
    var subj = (form.querySelector('[name="_subject"]') || {}).value || 'Website enquiry';
    status(form, 'Opening your email app with this message ready to send to ' + TO + '.');
    window.location.href = 'mailto:' + TO + '?subject=' + encodeURIComponent(subj) +
      '&body=' + encodeURIComponent(lines(form) + '\n\n- sent from mainspringhcp.com');
  }
  function send(form) {
    var btn = form.querySelector('button[type="submit"]');
    var next = (form.querySelector('[name="_next"]') || {}).value || '/thank-you/';
    if (btn) { btn.disabled = true; btn.dataset.label = btn.textContent; btn.textContent = 'Sending...'; }
    status(form, '');
    var done = false;
    var fail = function () {
      if (done) return; done = true;
      if (btn) { btn.disabled = false; btn.textContent = btn.dataset.label; }
      mailtoFallback(form);
    };
    var timer = setTimeout(fail, 12000);
    fetch(form.action.replace('formsubmit.co/', 'formsubmit.co/ajax/'), {
      method: 'POST', body: new FormData(form), headers: { Accept: 'application/json' }
    }).then(function (r) { return r.json(); }).then(function (j) {
      clearTimeout(timer);
      if (done) return;
      if (j && (j.success === 'true' || j.success === true)) { done = true; window.location.href = next; }
      else fail();
    }).catch(function () { clearTimeout(timer); fail(); });
  }
  document.querySelectorAll('form[action*="formsubmit.co"]').forEach(function (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      if (!window.fetch || !window.FormData) { form.submit(); return; }
      send(form);
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

/* Services chooser: tap a situation, the matching card lights up and scrolls into view. */
(function () {
  document.querySelectorAll('.choose[data-target]').forEach(function (a) {
    var id = a.getAttribute('data-target');
    if (!id) return;
    a.addEventListener('click', function (e) {
      var card = document.getElementById(id);
      if (!card) return;
      e.preventDefault();
      document.querySelectorAll('.choose.on').forEach(function (x) { x.classList.remove('on'); });
      document.querySelectorAll('.svc-card.hit').forEach(function (x) { x.classList.remove('hit'); });
      a.classList.add('on'); card.classList.add('hit');
      card.scrollIntoView({ behavior: 'smooth', block: 'center' });
    });
  });
})();
