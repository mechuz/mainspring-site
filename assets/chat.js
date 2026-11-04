/* Mainspring assistant — answers general questions and hands off to a partner.
   Runs entirely in the browser (GitHub Pages has no server). If CHAT_ENDPOINT is
   set, questions are sent there (a small worker holding the AI key) and the
   answer is shown; otherwise a built-in knowledge base answers by keyword and
   anything else goes to a human through the same FormSubmit path the forms use. */
(function () {
  var CHAT_ENDPOINT = '';          // e.g. https://chat.mainspringhcp.com/ask — leave empty for the built-in assistant
  var FORM = 'https://formsubmit.co/ajax/admin@mainspringhcp.com';
  var PHONE = '650-418-2280', TEL = 'tel:+16504182280';

  var KB = [
    { k: ['service', 'what do you do', 'help with', 'offer', 'areas'], a: 'Ten areas of work: interim executive leadership, survey remediation, operational & financial restructuring, budgeting & financial analysis, forensic & payroll analysis, due diligence & underwriting, operating systems, capital projects & renovations, marketing & census building, and technology & agentic advisory. Each is scoped, dated and priced before it begins.', links: [['All services', '/services/']] },
    { k: ['survey', 'deficien', 'jeopardy', 'ij', 'plan of correction', 'poc', 'admissions hold', 'revisit', 'cms', 'citation'], a: 'Survey remediation is core work for us: the removal plan for an immediate jeopardy, the plan of correction, and the execution that makes it hold at revisit. Survey situations get a same-day response — call ' + PHONE + '.', links: [['Survey remediation', '/services/survey-remediation/'], ['IJ: the first 72 hours', '/insights/immediate-jeopardy-first-72-hours/']] },
    { k: ['interim', 'administrator', 'executive director', ' ed ', 'nha', 'vacancy', 'director of nursing', 'don '], a: 'We place a licensed executive director or administrator on an interim basis — through a search or through a turnaround — matched to your state’s licensure. Usually within days.', links: [['Interim executive leadership', '/services/interim-executive-leadership/']] },
    { k: ['census', 'occupancy', 'fill', 'beds', 'move-in', 'marketing', 'website', 'seo', 'review', 'google', 'social', 'referral'], a: 'Census is an operations problem before it is a marketing problem: we measure the inquiry-to-move-in funnel, fix response time and conversion, put reviews and referral sources on a routine, then spend on demand into a building that can convert it.', links: [['Marketing & census building', '/services/rebranding-census-recovery/'], ['Census recovery playbook', '/insights/census-recovery-playbook/']] },
    { k: ['budget', 'cash', 'margin', 'variance', 'financial', 'labor cost', 'agency spend', 'overtime', 'p&l', 'pnl'], a: 'We build zero-based budgets with department heads, labor models tied to census, 13-week cash forecasts and monthly variance packages — the same discipline we run inside our own operating companies.', links: [['Budgeting & financial analysis', '/services/budgeting-financial-analysis/'], ['Operational & financial restructuring', '/services/operational-financial-restructuring/']] },
    { k: ['forensic', 'fraud', 'missing', 'reconcil', 'payroll', 'ghost', 'vendor', 'related party', 'trust fund', 'tracing', 'embezzl'], a: 'Forensic & payroll analysis: hours against schedules and census, vendor and related-party review, funds tracing, trust fund reconciliation, with a findings memo prepared for owners, lenders and counsel. We are not a CPA or law firm; we work alongside yours.', links: [['Forensic & payroll analysis', '/services/forensic-analysis/']] },
    { k: ['buy', 'acqui', 'purchase', 'lend', 'loan', 'refinanc', 'underwrit', 'diligence', 'broker', 'take over', 'takeover'], a: 'Operational and financial due diligence for acquisitions, refinancings and distressed takeovers — survey history, staffing, payor mix, normalized run-rate, capital needs, and a sized turnaround plan with a 100-day plan.', links: [['Due diligence & underwriting', '/services/due-diligence-underwriting/']] },
    { k: ['renovat', 'capex', 'capital', 'construction', 'contractor', 'architect', 'engineer', 'building project'], a: 'We act as your owner’s representative: we bring in and run the general contractor, engineers and architect, bid the work competitively, and hold budget and schedule — while keeping the building licensed and occupied.', links: [['Capital projects & renovations', '/services/capital-projects-redesign/']] },
    { k: ['ai', 'agent', 'automation', 'automat', 'technology', 'software', 'chatbot', 'tech'], a: 'We design and run AI agents for the work that falls through the cracks — inquiry and referral follow-up around the clock, review responses, a daily operating brief, payroll and census monitors — the same ones we run in our own buildings. People decide; the agents carry the weight.', links: [['Technology & agentic advisory', '/services/technology-agentic-advisory/']] },
    { k: ['state', 'agency', 'receiver', 'temporary manage', 'court', 'attorney general', 'monitor', 'closure', 'mandate'], a: 'For state agencies, courts and receivers: temporary management under an enforcement remedy, receivership operations, independent monitoring and managed closures — licensed administrators in the building within days, with reporting built for the agency.', links: [['For state agencies', '/state-agencies/']] },
    { k: ['price', 'pricing', 'cost', 'fee', 'rate', 'how much', 'retainer', 'charge'], a: 'Fees are fixed and tied to milestones, agreed in writing before any work begins — no open-ended retainers. Most engagements start with a five-day diagnostic that is scoped and priced up front. A partner can give you a number after one conversation.', links: [['How we work', '/how-we-work/'], ['Speak with a partner', '/contact/']] },
    { k: ['how do you work', 'process', 'engagement', 'diagnostic', 'scorecard', 'how long', 'timeline', 'steps'], a: 'Four steps: a five-day senior-led diagnostic with findings in dollars and dates; stabilize the immediate risks; rebuild the systems underneath; hand back to permanent leadership. A weekly scorecard keeps everyone looking at the same numbers.', links: [['How we work', '/how-we-work/']] },
    { k: ['where', 'location', 'based', 'new york', 'tennessee', 'state do you', 'serve', 'travel', 'nationwide'], a: 'We are based in New York and Tennessee and work across the United States; our administrators and nurse leaders are placed by state and matched to the licensure that applies.', links: [['About', '/about/']] },
    { k: ['who', 'felix', 'david', 'team', 'partner', 'founder', 'leadership', 'about'], a: 'Felix Strickland III, Managing Director of Operations and Compliance, is a licensed Nursing Home Administrator with multi-state experience across skilled nursing, assisted living and memory care. David Bloch, Managing Partner, leads engagements and client relationships.', links: [['About the firm', '/about/']] },
    { k: ['fast', 'quick', 'soon', 'urgent', 'emergency', 'today', 'tonight', 'same day', 'response time', 'how quickly'], a: 'Survey and leadership emergencies get a same-day response, and we can usually have a licensed leader in the building within days. If it is urgent, call ' + PHONE + ' now.', links: [['Call ' + PHONE, TEL]] },
    { k: ['book', 'schedule', 'calendar', 'appointment', 'meeting', 'call you', 'talk to'], a: 'You can put 30 minutes straight onto a partner’s calendar, or call ' + PHONE + '.', links: [['Book a call', '/book/'], ['Call ' + PHONE, TEL]] },
    { k: ['email', 'contact', 'reach', 'phone number', 'number'], a: 'db@mainspringhcp.com or ' + PHONE + '. Or leave your details here and a partner will reply today.', links: [['Contact', '/contact/']] },
    { k: ['job', 'career', 'work for', 'join', 'consultant', 'network', 'hiring', 'apply', 'nurse', 'employment'], a: 'We run a vetted network of executive directors and nurse leaders who take paid consulting engagements matched to their licensure and schedule. Apply through the consultant network page.', links: [['Consultant network', '/consultant-network/']] },
    { k: ['case stud', 'result', 'example', 'track record', 'reference', 'proof', 'client'], a: 'Our case studies are told with the numbers we can stand behind; communities are not named, and references are available to serious enquiries.', links: [['Case studies', '/case-studies/']] },
    { k: ['news', 'industry', 'headline', 'article', 'insight', 'blog', 'read'], a: 'Two things to read: our operating notes, and a live feed of skilled nursing and senior living headlines updated through the day.', links: [['Insights', '/insights/'], ['Industry news', '/industry/']] },
    { k: ['hello', 'hi', 'hey', 'good morning', 'good afternoon'], a: 'Hello. Ask me about a service, how we work, fees, or how fast we can be in a building — or tell me what is going on and I will point you to a partner.', links: [] }
  ];
  var CHIPS = [['Survey trouble', 'survey'], ['Need a leader placed', 'interim placement'], ['Census is down', 'census'], ['Fees', 'pricing'], ['Talk to a partner', '__human']];

  function el(tag, cls, html) { var e = document.createElement(tag); if (cls) e.className = cls; if (html != null) e.innerHTML = html; return e; }
  function esc(s) { return String(s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }

  function answer(q) {
    var t = ' ' + q.toLowerCase().replace(/[^a-z0-9&' ]/g, ' ') + ' ';
    var best = null, score = 0;
    KB.forEach(function (e) {
      var s = 0; e.k.forEach(function (k) { if (t.indexOf(k) > -1) s += k.length; });
      if (s > score) { score = s; best = e; }
    });
    return best;
  }

  // ---- UI
  var fab = el('button', 'chat-fab', '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12a8 8 0 0 1-8 8H8l-5 3 1.5-4.5A8 8 0 1 1 21 12z"/></svg><span>Ask us</span>');
  fab.setAttribute('aria-label', 'Open chat');
  var box = el('div', 'chat'); box.hidden = true; box.setAttribute('role', 'dialog'); box.setAttribute('aria-label', 'Mainspring assistant');
  box.innerHTML =
    '<div class="chat-h"><div class="chat-mark">M</div><div><b>Mainspring</b><small>Ask about services, fees, timing</small></div><button class="chat-x" aria-label="Close">&times;</button></div>' +
    '<div class="chat-msgs"></div>' +
    '<div class="chat-chips"></div>' +
    '<form class="chat-form"><input type="text" placeholder="Type a question…" aria-label="Your question" autocomplete="off"><button type="submit" aria-label="Send"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"/></svg></button></form>';
  document.body.appendChild(fab); document.body.appendChild(box);
  var msgs = box.querySelector('.chat-msgs'), chips = box.querySelector('.chat-chips'), form = box.querySelector('.chat-form'), input = form.querySelector('input');

  function add(role, html) { var m = el('div', 'chat-m ' + role, html); msgs.appendChild(m); msgs.scrollTop = msgs.scrollHeight; return m; }
  function links(arr) { return arr && arr.length ? '<div class="chat-links">' + arr.map(function (l) { return '<a class="btn btn-primary" href="' + esc(l[1]) + '">' + esc(l[0]) + '</a>'; }).join('') + '</div>' : ''; }
  function setChips(list) { chips.innerHTML = ''; list.forEach(function (c) { var b = el('button', '', esc(c[0])); b.type = 'button'; b.onclick = function () { ask(c[1] === '__human' ? '__human' : c[1], c[0]); }; chips.appendChild(b); }); }

  function human() {
    add('bot', 'Leave your name, phone and what is going on. A partner reads it the same day — same day for survey and leadership situations.' +
      '<form class="chat-lead"><input name="name" placeholder="Your name" required autocomplete="name"><input name="phone" placeholder="Phone" type="tel" required autocomplete="tel"><input name="email" placeholder="Email" type="email" autocomplete="email"><textarea name="details" placeholder="What is happening in the building?" rows="3" required></textarea><button type="submit" class="btn btn-primary">Send to a partner</button></form>' +
      '<div class="chat-links"><a class="btn btn-ghost" href="' + TEL + '">Call ' + PHONE + '</a><a class="btn btn-ghost" href="/book/">Book a call</a></div>');
    var f = msgs.querySelector('.chat-lead:last-of-type');
    f.addEventListener('submit', function (e) {
      e.preventDefault();
      var fd = new FormData(f); fd.append('_subject', 'CHAT LEAD — mainspringhcp.com'); fd.append('_cc', 'db@mainspringhcp.com'); fd.append('_template', 'table');
      var btn = f.querySelector('button'); btn.disabled = true; btn.textContent = 'Sending…';
      var done = function (ok) {
        f.remove();
        add('bot', ok ? 'Got it — thank you. A partner will reply today. If it cannot wait, call ' + PHONE + '.' :
          'That did not go through. Please call ' + PHONE + ' or email <a href="mailto:db@mainspringhcp.com">db@mainspringhcp.com</a> — we answer the same day.');
      };
      fetch(FORM, { method: 'POST', body: fd, headers: { Accept: 'application/json' } }).then(function (r) { return r.json(); })
        .then(function (j) { done(j && (j.success === 'true' || j.success === true)); }).catch(function () { done(false); });
    });
  }

  function ask(q, label) {
    if (q === '__human') { add('me', esc(label || 'Talk to a partner')); human(); return; }
    add('me', esc(label || q));
    if (CHAT_ENDPOINT) {
      var t = add('bot typing', 'Thinking…');
      fetch(CHAT_ENDPOINT, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ q: q, page: location.pathname }) })
        .then(function (r) { return r.json(); }).then(function (j) { t.className = 'chat-m bot'; t.innerHTML = esc(j.answer || '') + links(j.links || []); })
        .catch(function () { t.className = 'chat-m bot'; t.innerHTML = 'I could not reach the assistant. ' + links([['Talk to a partner', '/contact/'], ['Call ' + PHONE, TEL]]); });
      return;
    }
    var e = answer(q);
    if (e) add('bot', esc(e.a) + links(e.links));
    else add('bot', 'I do not have that one. A partner will — tell me what is going on and they will reply today.' + links([['Leave your details', '#human'], ['Call ' + PHONE, TEL]]));
    setChips(CHIPS);
  }

  msgs.addEventListener('click', function (e) { var a = e.target.closest('a[href="#human"]'); if (a) { e.preventDefault(); human(); } });
  form.addEventListener('submit', function (e) { e.preventDefault(); var q = input.value.trim(); if (!q) return; input.value = ''; ask(q); });
  function open() { box.hidden = false; fab.classList.add('off'); if (!msgs.children.length) { add('bot', 'Hello. Ask about a service, fees, or how fast we can be in a building — or tell me what is going on.'); setChips(CHIPS); } setTimeout(function () { input.focus(); }, 50); }
  function close() { box.hidden = true; fab.classList.remove('off'); }
  fab.addEventListener('click', open); box.querySelector('.chat-x').addEventListener('click', close);
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && !box.hidden) close(); });
  // an "Ask us" link anywhere on the page opens the chat
  document.querySelectorAll('a[href="#chat"]').forEach(function (a) { a.addEventListener('click', function (e) { e.preventDefault(); open(); }); });
})();
