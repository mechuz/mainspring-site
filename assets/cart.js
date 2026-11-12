/* Mainspring — services cart + quick checkout.
   Client-side only: the cart lives in localStorage, the checkout posts the
   selected services with the booking request through the normal intake form. */
(function () {
  var KEY = 'ms_cart';
  var CATALOG = {
    'survey-remediation': ['Survey remediation', '/services/survey-remediation/'],
    'interim-executive-leadership': ['Interim leadership placement', '/services/interim-executive-leadership/'],
    'operational-financial-restructuring': ['Operational & financial restructuring', '/services/operational-financial-restructuring/'],
    'budgeting-financial-analysis': ['Budgeting & financial analysis', '/services/budgeting-financial-analysis/'],
    'forensic-analysis': ['Forensic & payroll analysis', '/services/forensic-analysis/'],
    'due-diligence-underwriting': ['Due diligence & underwriting', '/services/due-diligence-underwriting/'],
    'operating-systems-buildout': ['Operating systems build-out', '/services/operating-systems-buildout/'],
    'capital-projects-redesign': ['Capital projects & renovations', '/services/capital-projects-redesign/'],
    'temporary-management': ['Temporary management & receivership', '/state-agencies/'],
    'operational-assessment': ['Operational assessment (five days on site)', '/how-we-work/'],
    'mock-survey': ['Mock survey', '/services/survey-remediation/']
  };

  function load() { try { return JSON.parse(localStorage.getItem(KEY) || '[]').filter(function (k) { return CATALOG[k]; }); } catch (e) { return []; } }
  function save(c) { try { localStorage.setItem(KEY, JSON.stringify(c)); } catch (e) {} render(); }
  function has(k) { return load().indexOf(k) !== -1; }
  function toggle(k) { var c = load(); var i = c.indexOf(k); if (i === -1) c.push(k); else c.splice(i, 1); save(c); return i === -1; }
  function remove(k) { save(load().filter(function (x) { return x !== k; })); }
  function names(c) { return c.map(function (k) { return CATALOG[k][0]; }); }

  /* clear after a successful booking */
  if (location.pathname.indexOf('/thank-you') === 0) { try { localStorage.removeItem(KEY); } catch (e) {} }

  /* floating cart button + drawer, on every page */
  var fab = document.createElement('button');
  fab.type = 'button'; fab.className = 'cart-fab'; fab.setAttribute('aria-label', 'Your cart');
  fab.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 4h2l2.4 11.2a2 2 0 0 0 2 1.6h7.8a2 2 0 0 0 2-1.5L21 8H6"/><circle cx="10" cy="20" r="1.4"/><circle cx="17" cy="20" r="1.4"/></svg><span class="n">0</span><span class="t">Cart</span>';
  var back = document.createElement('div'); back.className = 'cart-backdrop'; back.hidden = true;
  var drawer = document.createElement('aside'); drawer.className = 'cart-drawer'; drawer.hidden = true;
  drawer.setAttribute('role', 'dialog'); drawer.setAttribute('aria-label', 'Your cart');
  drawer.innerHTML = '<div class="cart-h"><b>Your cart</b><button type="button" class="cart-x" aria-label="Close">&#x2715;</button></div>' +
    '<div class="cart-body"><p class="cart-note">A 30-minute consultation with a partner is always included, no charge. Add the services you want to talk about.</p><div class="cart-items"></div></div>' +
    '<div class="cart-f"><a class="btn btn-primary block" href="/book/">Quick checkout <span class="arrow">&rarr;</span></a><a class="cart-more" href="/services/">Add more services</a></div>';
  document.body.appendChild(fab); document.body.appendChild(back); document.body.appendChild(drawer);

  function open() { back.hidden = false; drawer.hidden = false; requestAnimationFrame(function () { drawer.classList.add('open'); back.classList.add('open'); }); }
  function close() { drawer.classList.remove('open'); back.classList.remove('open'); setTimeout(function () { drawer.hidden = true; back.hidden = true; }, 300); }
  fab.addEventListener('click', open);
  back.addEventListener('click', close);
  drawer.querySelector('.cart-x').addEventListener('click', close);
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') close(); });

  function render() {
    var c = load();
    fab.querySelector('.n').textContent = c.length;
    fab.classList.toggle('on', c.length > 0);
    var list = drawer.querySelector('.cart-items');
    list.innerHTML = c.length ? c.map(function (k) {
      return '<div class="cart-item"><div><b>' + CATALOG[k][0] + '</b><span>Scoped, dated and priced after the call</span></div><button type="button" class="cart-rm" data-rm="' + k + '" aria-label="Remove">Remove</button></div>';
    }).join('') : '<p class="cart-empty">Nothing added yet. The consultation is still yours to book.</p>';
    /* toggle buttons on the page */
    document.querySelectorAll('[data-add]').forEach(function (b) {
      var on = c.indexOf(b.getAttribute('data-add')) !== -1;
      b.classList.toggle('on', on);
      b.innerHTML = on ? 'Added <span aria-hidden="true">&#10003;</span>' : (b.getAttribute('data-label') || 'Add to cart');
    });
    /* checkout page */
    var lines = document.getElementById('ck-lines');
    if (lines) {
      lines.innerHTML = '<div class="ck-line ck-base"><div><b>Consultation with a partner</b><span>30 minutes, video or phone</span></div><em>Included</em></div>' +
        c.map(function (k) { return '<div class="ck-line"><div><b>' + CATALOG[k][0] + '</b><span>Scoped, dated and priced after the call</span></div><button type="button" class="cart-rm" data-rm="' + k + '">Remove</button></div>'; }).join('');
      var hidden = document.querySelector('input[name="services_in_cart"]');
      if (hidden) hidden.value = c.length ? names(c).join('; ') : 'Consultation only';
      var subj = document.querySelector('input[name="_subject"][data-ck]');
      if (subj) subj.value = 'BOOKING — consultation' + (c.length ? ' + ' + c.length + ' service' + (c.length > 1 ? 's' : '') : '') + ' — mainspringhcp.com';
    }
  }

  document.addEventListener('click', function (e) {
    var t = e.target.closest ? e.target : null; if (!t) return;
    var a = t.closest('[data-add]');
    if (a) { e.preventDefault(); var added = toggle(a.getAttribute('data-add')); if (added) { fab.classList.add('bump'); setTimeout(function () { fab.classList.remove('bump'); }, 500); } return; }
    var r = t.closest('[data-rm]');
    if (r) { e.preventDefault(); remove(r.getAttribute('data-rm')); return; }
  });

  /* ?add=slug on the checkout page drops a service straight into the cart */
  var m = location.search.match(/[?&]add=([a-z-]+)/);
  if (m && CATALOG[m[1]] && !has(m[1])) toggle(m[1]);
  window.msCart = { add: function (k) { if (CATALOG[k] && !has(k)) toggle(k); }, remove: remove, has: has, items: load };
  render();
})();
