/* Mainspring — "Tell us what is happening": three questions, a plan, an advisor.
   Rules-based, runs in the browser. Advisors come from consultants.json, embedded
   by the build as <script type="application/json" id="ms-consultants">. */
(function () {
  var root = document.querySelector('.dx'); if (!root) return;
  var ISSUES = {
    survey:  { label: 'Survey deficiencies', tags: ['Survey remediation', 'Clinical operations'], services: ['survey-remediation'], folder: 'survey',
      title: 'Clear the survey with evidence the surveyor accepts.',
      first30: ['A licensed administrator and a nurse leader in the building within days', 'Every tag read, an owner and a date on each item', 'The evidence binder started on day one and kept through revisit'],
      then: ['Mock survey before the revisit', 'Systems that keep the building survey-ready without us'] },
    ij:      { label: 'Immediate jeopardy', urgent: true, tags: ['Survey remediation', 'Clinical operations', 'Interim leadership'], services: ['survey-remediation'], folder: 'survey',
      title: 'Abate the jeopardy today. Then fix what caused it.',
      first30: ['Abatement plan and resident safety check today, not this week', 'Removal evidence assembled for the surveyor', 'Root cause fixed so it does not recur'],
      then: ['Plan of correction accepted', 'Staffing and clinical systems rebuilt'] },
    hold:    { label: 'Admissions hold', tags: ['Survey remediation', 'Census growth'], services: ['survey-remediation'], folder: 'survey',
      title: 'Get the hold lifted, in writing, with dates.',
      first30: ['The path back to admitting agreed with the agency', 'Evidence of substantial compliance built item by item', 'Referral sources kept warm while the door is shut'],
      then: ['Census rebuilt from the referral relationships up'] },
    vacancy: { label: 'An empty leadership seat', tags: ['Interim leadership', 'Clinical operations'], services: ['interim-executive-leadership'], folder: 'lead',
      title: 'Someone who has held the seat, in it within days.',
      first30: ['Licensed interim placed by state, in the building in days', 'Staffing, census, compliance, families and the P&L run day to day', 'Operating systems written down as we go'],
      then: ['Help hiring the permanent person', 'A clean handoff, then we leave'] },
    census:  { label: 'Falling census', tags: ['Census growth', 'Turnaround'], services: ['operational-assessment'], folder: 'consult',
      title: 'Find where the admissions stopped, then turn them back on.',
      first30: ['Inquiry-to-move-in funnel measured, response time fixed', 'Referral sources called, every one', 'Weekly funnel scorecard someone owns'],
      then: ['Reviews, listings and website on a routine', 'Demand spent into a building that can convert it'] },
    cash:    { label: 'Cash and budget pressure', tags: ['Restructuring', 'Budgeting & financial analysis'], services: ['operational-financial-restructuring', 'budgeting-financial-analysis'], folder: 'money',
      title: 'Labor to census, vendors renegotiated, a budget that holds.',
      first30: ['Labor, census and cash on one page, daily', 'Agency and overtime brought down against a staffing model', 'A budget by department and by PPD that the department heads run'],
      then: ['Vendors and payroll current', 'Monthly report to ownership or the lender'] },
    numbers: { label: 'Numbers that do not reconcile', tags: ['Forensic & payroll analysis'], services: ['forensic-analysis'], folder: 'money',
      title: 'Find where the money went.',
      first30: ['Payroll checked against the schedule, every pay period', 'Related parties, vendors and resident trust funds traced', 'A written finding you can act on'],
      then: ['Controls so it cannot happen again'] },
    capital: { label: 'A capital project', tags: ['Capital projects'], services: ['capital-projects-redesign'], folder: 'money',
      title: 'Life safety first, the budget held, the building still running.',
      first30: ['Facility condition assessment, roof to boiler', 'Phased plan with life safety first', 'Bids levelled so you compare the same thing'],
      then: ['Owner’s-rep oversight through completion'] },
    deal:    { label: 'A deal to underwrite', tags: ['Due diligence & underwriting', 'Budgeting & financial analysis'], services: ['due-diligence-underwriting'], folder: 'money',
      title: 'An operator’s read of the building, not a broker’s.',
      first30: ['Survey history, staffing and census read the way a surveyor would', 'The P&L rebuilt from the building up', 'A written underwriting memo with the risks priced'],
      then: ['Transition plan if you close'] },
    state:   { label: 'State agency, court or receiver', urgent: true, tags: ['Temporary management', 'Survey remediation', 'Interim leadership'], services: ['temporary-management'], folder: 'state',
      title: 'Licensed operators in the building, reporting in your format.',
      first30: ['Administrator and DON in the building within days', 'Resident safety assessment and financial controls taken over', 'A plan with dates for the agency by day 30'],
      then: ['Deficiencies corrected with evidence', 'Transfer, sale or orderly closure with every resident placed'] },
    unsure:  { label: 'An outside read', tags: ['Turnaround', 'Restructuring'], services: ['operational-assessment'], folder: 'consult',
      title: 'Five days in the building. Findings in dollars and dates.',
      first30: ['A senior operator on site for five days', 'Findings sized in dollars, targets with dates', 'A plan you can act on with or without us'],
      then: ['Execution scoped and priced, if you want it'] }
  };
  var consultants = [];
  try { consultants = JSON.parse((document.getElementById('ms-consultants') || {}).textContent || '[]'); } catch (e) {}

  var state = { type: '', issues: [], urgency: '' };
  var panes = root.querySelectorAll('.dx-pane'), steps = root.querySelectorAll('.dx-steps li');
  function show(n) {
    panes.forEach(function (p) { p.hidden = p.getAttribute('data-pane') !== String(n); });
    steps.forEach(function (s, i) { s.classList.toggle('on', i < n); s.classList.toggle('done', i < n - 1); });
    root.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
  root.addEventListener('click', function (e) {
    var chip = e.target.closest('.dx-chips button');
    if (chip) {
      var group = chip.parentElement, field = group.getAttribute('data-field');
      if (group.hasAttribute('data-single')) {
        group.querySelectorAll('button').forEach(function (b) { b.classList.remove('on'); });
        chip.classList.add('on'); state[field] = chip.getAttribute('data-v');
      } else {
        chip.classList.toggle('on');
        state[field] = Array.prototype.map.call(group.querySelectorAll('button.on'), function (b) { return b.getAttribute('data-v'); });
      }
      return;
    }
    if (e.target.closest('[data-next]')) { show(2); return; }
    if (e.target.closest('[data-back]')) { show(1); return; }
    if (e.target.closest('[data-plan]')) { plan(); show(3); return; }
    if (e.target.closest('[data-restart]')) { show(1); return; }
    var add = e.target.closest('[data-add-plan]');
    if (add && window.msCart) {
      add.getAttribute('data-add-plan').split(',').forEach(function (k) { if (k) window.msCart.add(k); });
      add.innerHTML = 'Added to cart <span aria-hidden="true">&#10003;</span>'; add.disabled = true;
      return;
    }
  });

  function matchAdvisors(tags, st) {
    return consultants.map(function (c) {
      var score = 0;
      tags.forEach(function (t) { if ((c.specialties || []).indexOf(t) !== -1) score += 2; });
      if (st && (c.states || []).some(function (s) { return s.toUpperCase() === st.toUpperCase(); })) score += 1;
      if (c.featured) score += 0.5;
      return { c: c, score: score };
    }).sort(function (a, b) { return b.score - a.score; }).filter(function (x) { return x.score > 0; }).map(function (x) { return x.c; });
  }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (ch) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[ch]; }); }
  function uniq(a) { var seen = {}; return a.filter(function (x) { if (seen[x]) return false; seen[x] = 1; return true; }); }

  function plan() {
    var issues = (state.issues.length ? state.issues : ['unsure']).map(function (k) { return ISSUES[k]; });
    var st = (document.getElementById('dx-state').value || '').trim(), beds = (document.getElementById('dx-beds').value || '').trim();
    var urgent = state.urgency === 'today' || issues.some(function (i) { return i.urgent; });
    var tags = uniq([].concat.apply([], issues.map(function (i) { return i.tags; })));
    var services = uniq([].concat.apply([], issues.map(function (i) { return i.services; })));
    var first30 = uniq([].concat.apply([], issues.map(function (i) { return i.first30; }))).slice(0, 6);
    var then = uniq([].concat.apply([], issues.map(function (i) { return i.then; }))).slice(0, 4);
    var advisors = matchAdvisors(tags, st); var lead = advisors[0], second = advisors[1];
    if (second && !tags.some(function (t) { return (second.specialties || []).indexOf(t) !== -1; })) second = null;
    var where = [state.type, st ? st.toUpperCase() : '', beds ? beds + ' beds' : ''].filter(Boolean).join(' · ');
    var head = issues.length === 1 ? issues[0].title : 'One plan for ' + issues.length + ' problems, one team in the building.';
    var folderLink = '/#folder-' + issues[0].folder;

    var html = '';
    html += '<div class="dx-head"><p class="eyebrow">Your plan' + (where ? ' · ' + esc(where) : '') + '</p><h3>' + esc(head) + '</h3>';
    html += '<p class="dx-issues">' + issues.map(function (i) { return '<span>' + esc(i.label) + '</span>'; }).join('') + '</p></div>';
    if (urgent) html += '<div class="dx-urgent"><b>Same-day response.</b> For jeopardy, an abandonment or a state action, a partner calls you today. Book below or send the form and mark it urgent.</div>';
    html += '<div class="dx-grid">';
    html += '<div class="dx-card"><p class="seclabel">First 30 days · Take control</p><ul class="svc-out">' + first30.map(function (x) { return '<li>' + esc(x) + '</li>'; }).join('') + '</ul></div>';
    html += '<div class="dx-card"><p class="seclabel">Then</p><ul class="svc-out">' + then.map(function (x) { return '<li>' + esc(x) + '</li>'; }).join('') + '</ul><p class="dx-note">Only the first 30 days have a set length. The rest depends on the building; we agree the timeline with you at day 30 and report every month. Fixed fee, in writing, first.</p></div>';
    html += '</div>';
    if (lead) {
      html += '<div class="dx-adv"><div class="dx-adv-who"><span class="mono">' + esc(lead.name.split(' ').map(function (w) { return w[0]; }).slice(0, 2).join('')) + '</span><div><p class="eyebrow">Your advisor</p><h4>' + esc(lead.name) + '</h4><p class="dx-adv-t">' + esc(lead.title) + '</p><p class="dx-adv-why">' + esc((lead.credentials || []).join(' · ')) + '. Matched on ' + esc(tags.filter(function (t) { return (lead.specialties || []).indexOf(t) !== -1; }).slice(0, 3).join(', ').toLowerCase() || 'the whole engagement') + '.</p>' +
        (second ? '<p class="dx-adv-second">With <b>' + esc(second.name) + '</b> on ' + esc(tags.filter(function (t) { return (second.specialties || []).indexOf(t) !== -1; }).slice(0, 2).join(' and ').toLowerCase()) + '.</p>' : '') + '</div></div>';
      html += '<div class="dx-book"><a class="btn btn-primary" href="/book/?consultant=' + esc(lead.slug) + '&mode=video">Book a video call <span class="arrow">&rarr;</span></a><a class="btn btn-ghost" href="/book/?consultant=' + esc(lead.slug) + '&mode=phone">Phone call</a><a class="btn btn-ghost" href="/book/?consultant=' + esc(lead.slug) + '&mode=in-person">In person at the building</a><a class="dx-prof" href="/consultants/' + esc(lead.slug) + '/">Full profile &amp; r\u00e9sum\u00e9 &rarr;</a></div></div>';
    } else {
      html += '<div class="dx-adv"><div><p class="eyebrow">Your advisor</p><h4>A partner matches you from the network.</h4></div><div class="dx-book"><a class="btn btn-primary" href="/book/">Book a consultation <span class="arrow">&rarr;</span></a></div></div>';
    }
    html += '<div class="dx-foot"><button type="button" class="btn btn-ghost" data-add-plan="' + esc(services.join(',')) + '">Add this plan to the cart (' + services.length + ')</button><a class="dx-link" href="' + folderLink + '">Open the ' + esc(issues[0].folder === 'lead' ? 'Leadership' : issues[0].folder === 'consult' ? 'Consulting' : issues[0].folder === 'money' ? 'Money' : issues[0].folder === 'state' ? 'State agencies' : 'Survey & compliance') + ' folder &rarr;</a><button type="button" class="dx-link" data-restart>Start over</button></div>';
    html += '<form class="dx-mail" action="/thank-you/" data-fs="info" method="POST"><input type="hidden" name="_blacklist" value="seeking employment, job opportunity, my resume, backlinks, seo services, guest post, web design, website design, website redesign, redesign your website, found several errors, errors on your site, pending web, rank on google, first page of google, seo audit, mobile app development, app development, my last email, reminder email, tuesday reminder, follow up on my, bitcoin, crypto, casino, lead generation services, video editing, logo design, virtual assistant services"><input type="text" name="_honey" style="display:none" tabindex="-1" autocomplete="off"><input type="hidden" name="_template" value="table"><input type="hidden" name="_subject" value="PLAN REQUEST — ' + esc(issues.map(function (i) { return i.label; }).join(', ')) + ' — mainspringhcp.com"><input type="hidden" name="_next" value="https://mainspringhcp.com/thank-you/"><input type="hidden" name="_captcha" value="false"><input type="text" name="_honey" style="display:none" tabindex="-1" autocomplete="off">' +
      '<input type="hidden" name="building" value="' + esc(where || 'not given') + '"><input type="hidden" name="issues" value="' + esc(issues.map(function (i) { return i.label; }).join('; ')) + '"><input type="hidden" name="urgency" value="' + esc(state.urgency || 'not given') + '"><input type="hidden" name="advisor_matched" value="' + esc(lead ? lead.name : 'network') + '"><input type="hidden" name="plan_first_30_days" value="' + esc(first30.join(' | ')) + '">' +
      '<label for="dx-email">Email me this plan and have ' + esc(lead ? lead.name.split(' ')[0] : 'a partner') + ' call me</label><div class="dx-mail-row"><input id="dx-email" name="email" type="email" required placeholder="you@community.com" autocomplete="email"><input name="phone" type="tel" placeholder="Phone (optional)" autocomplete="tel"><button type="submit" class="btn btn-primary">Send</button></div><p class="form-status" role="status"></p></form>';
    document.getElementById('dx-result').innerHTML = html;
    /* let the shared form handler (site.js) pick up the new form */
    if (window.msBindForms) window.msBindForms();
  }
})();
