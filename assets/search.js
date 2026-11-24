/* SAVEONSUB discovery search (V22 Wave 1).
 *
 * Deterministic, static and client-side. It reads only the governed public
 * CATALOG from assets/catalog.js (held plans are already removed at build
 * time), sends nothing over the network and stores nothing (no browser storage,
 * cookies or analytics events), so search history never leaves the screen.
 *
 * Commercial safety: listing cards never emit cartAdd. Ordering happens only
 * on product pages, where the held-plan notice and cartPlanOk() apply. A price
 * is shown only for an "approved" product with a valid, non-shared plan; any
 * other product shows "Price on request" (an unknown price never becomes 0).
 */
(function (root) {
  'use strict';

  function norm(s) {
    s = String(s == null ? '' : s).toLowerCase();
    s = s.replace(/[‌‍]/g, '');
    s = s.replace(/[০-৯]/g, function (d) { return String(d.charCodeAt(0) - 0x09e6); });
    if (s.normalize) s = s.normalize('NFD').replace(/[̀-ͯ]/g, '').normalize('NFC');
    return s;
  }

  function rawTokens(s) { return norm(s).match(/[a-z0-9ঀ-৿]+/g) || []; }

  // Words that match almost every product (or only describe how people pay or
  // what they fear) carry no discovery signal; "shared"/"reseller" are ignored
  // so they can never steer a query towards a restricted offer.
  var STOP = {};
  ('a an and the for of in on to with is it my me i how what which koto kivabe ' +
   'bd bangladesh bangla price prices dam taka tk buy kinbo kena best cheap cheapest sasta ' +
   'subscription subscriptions plan plans month monthly year 2025 2026 bkash nagad rocket ' +
   'shared share reseller account accounts vs review worth ' +
   'দাম টাকা কিনব কেনা কিনতে সস্তা বাংলাদেশ বিকাশ নগদ সাবস্ক্রিপশন প্ল্যান কত কীভাবে কিভাবে')
    .split(' ').forEach(function (w) { rawTokens(w).forEach(function (t) { STOP[t] = 1; }); });

  function tokens(s) { return rawTokens(s).filter(function (t) { return !STOP[t]; }); }

  // Use-case vocabulary (English, Banglish, Bangla) per catalog category.
  var CAT_WORDS = {
    'AI Assistants': 'chatbot chat assistant gpt ai llm question answer sohokari প্রশ্ন উত্তর চ্যাট চ্যাটবট এআই সহকারী',
    'AI Image & Design': 'image images photo picture design designer logo poster graphic art drawing chobi chhobi chabi dizain ছবি ডিজাইন লোগো পোস্টার',
    'AI Video': 'video videos reel reels edit editing movie clip bhidio vidio ভিডিও এডিট রিল',
    'AI Voice & Music': 'voice audio music song songs speech podcast gaan gan kontho গান মিউজিক ভয়েস অডিও কণ্ঠ',
    'AI Code & Dev': 'code coding programming developer dev software app website programmer কোড কোডিং প্রোগ্রামিং ডেভেলপার',
    'AI Writing': 'writing write essay article content copywriting blog grammar lekha লেখা রাইটিং কনটেন্ট',
    'Workspace & Productivity': 'office productivity notes docs document work team kaj অফিস কাজ নোট',
    'Entertainment': 'movie movies series drama natok cinema stream streaming tv show bineodon নাটক সিনেমা মুভি বিনোদন',
    'Education & Career': 'study student students course learn learning career job exam porashona chhatro shikkha পড়াশোনা ছাত্র শিক্ষা কোর্স ক্যারিয়ার',
    'VPN & Security': 'vpn security privacy safe nirapotta নিরাপত্তা ভিপিএন',
    'Gaming': 'game games gaming play khela খেলা গেম',
    'BD Lifestyle': 'lifestyle daily life জীবনযাপন',
    'Bundles': 'bundle bundles combo package বান্ডেল কম্বো'
  };

  // Query-side aliases: Bangla-script brand names and common short forms.
  var SYN = {};
  [['chatgpt', 'gpt chatgpt চ্যাটজিপিটি জিপিটি'], ['gemini', 'জেমিনি'], ['claude', 'ক্লড'],
   ['canva', 'ক্যানভা'], ['netflix', 'নেটফ্লিক্স'], ['youtube', 'yt ইউটিউব'], ['spotify', 'স্পটিফাই'],
   ['grok', 'গ্রক'], ['perplexity', 'পারপ্লেক্সিটি'], ['midjourney', 'mj মিডজার্নি'], ['capcut', 'ক্যাপকাট'],
   ['copilot', 'কোপাইলট'], ['notion', 'নোশন'], ['adobe', 'অ্যাডোবি'], ['google', 'গুগল']]
    .forEach(function (pair) { rawTokens(pair[1]).forEach(function (a) { (SYN[a] = SYN[a] || []).push(pair[0]); }); });

  // Optimal-string-alignment distance, abandoned once it exceeds `max`.
  function dist(a, b, max) {
    var la = a.length, lb = b.length, i, j;
    if (Math.abs(la - lb) > max) return max + 1;
    var prev2 = null, prev = [], cur;
    for (j = 0; j <= lb; j++) prev[j] = j;
    for (i = 1; i <= la; i++) {
      cur = [i];
      var rowMin = i;
      for (j = 1; j <= lb; j++) {
        var cost = a.charAt(i - 1) === b.charAt(j - 1) ? 0 : 1;
        var v = Math.min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost);
        if (prev2 && i > 1 && j > 1 && a.charAt(i - 1) === b.charAt(j - 2) && a.charAt(i - 2) === b.charAt(j - 1)) {
          v = Math.min(v, prev2[j - 2] + 1);
        }
        cur[j] = v;
        if (v < rowMin) rowMin = v;
      }
      if (rowMin > max) return max + 1;
      prev2 = prev;
      prev = cur;
    }
    return prev[lb];
  }

  function typoAllowance(len) { return len >= 8 ? 2 : (len >= 4 ? 1 : 0); }

  function text(v) {
    if (v == null) return '';
    if (Array.isArray(v)) return v.map(text).join(' ');
    if (typeof v === 'object') return Object.keys(v).map(function (k) { return text(v[k]); }).join(' ');
    return String(v);
  }

  // Fail-closed plan projection used for every price and filter decision.
  function safePlans(p) {
    if (!p || p.sellability !== 'approved' || p.request_price === true || !Array.isArray(p.plans)) return [];
    return p.plans.filter(function (pl) {
      return pl && typeof pl.plan_id === 'string' && pl.plan_id !== '' && !/shared/i.test(pl.plan_id) &&
        pl.type !== 'shared' && typeof pl.bdt === 'number' && isFinite(pl.bdt) && pl.bdt > 0;
    });
  }

  function buildIndex(catalog) {
    var products = (catalog && Array.isArray(catalog.products)) ? catalog.products : [];
    // Other business units are removed from the staged catalog by cross_unit_quarantine.py.
    return products.filter(function (p) { return p && p.id && p.name; }).map(function (p) {
      var seo = p.seo || {};
      var fields = [
        [p.name, 10], [String(p.id).replace(/-/g, ' '), 8], [p.brand, 6], [p.category, 4],
        [CAT_WORDS[p.category], 3], [seo.transliteration, 3], [seo.bangla, 3],
        [seo.primary, 2], [seo.short_tail, 2], [seo.informational, 1], [seo.long_tail, 1]
      ];
      var tw = {};
      fields.forEach(function (f) {
        tokens(text(f[0])).forEach(function (t) { if (!tw[t] || tw[t] < f[1]) tw[t] = f[1]; });
      });
      var plans = safePlans(p);
      var min = null, types = {};
      plans.forEach(function (pl) {
        if (min === null || pl.bdt < min) min = pl.bdt;
        types[pl.type] = 1;
      });
      var nameToks = rawTokens(p.name);
      return {
        id: String(p.id), name: String(p.name), icon: p.icon || '', category: p.category || '',
        tw: tw, toks: Object.keys(tw), nameToks: nameToks, joined: nameToks.join(''),
        plans: plans, minBdt: min, orderable: plans.length > 0, types: Object.keys(types),
        bundle: p.category === 'Bundles'
      };
    });
  }

  function tokenScore(q, d) {
    if (d.tw[q]) return d.tw[q] + (d.nameToks.indexOf(q) > -1 ? 4 : 0);
    var allow = typoAllowance(q.length), best = 0;
    for (var i = 0; i < d.toks.length; i++) {
      var t = d.toks[i], s = 0;
      if (q.length >= 2 && t.indexOf(q) === 0) s = 0.8;
      else if (q.length >= 3 && t.indexOf(q) > 0) s = 0.5;
      else if (allow && Math.abs(t.length - q.length) <= allow && dist(q, t, allow) <= allow) s = 0.6;
      if (s * d.tw[t] > best) best = s * d.tw[t];
    }
    return best;
  }

  function scoreDoc(qt, joinedQ, d) {
    var score = 0, matchedAll = true;
    for (var i = 0; i < qt.length; i++) {
      var alts = [qt[i]].concat(SYN[qt[i]] || []), b = 0;
      for (var k = 0; k < alts.length; k++) { var s = tokenScore(alts[k], d); if (s > b) b = s; }
      if (!b) { matchedAll = false; break; }
      score += b;
    }
    var compound = joinedQ.length >= 4 && d.joined.indexOf(joinedQ) === 0; // "chat gpt" -> ChatGPT
    if (!matchedAll) score = compound ? 12 : 0;
    else score += compound ? 6 : 0;
    // A bundle that merely contains the product must not outrank the product itself.
    return d.bundle ? score * 0.7 : score;
  }

  function passes(d, o) {
    if (o.category && o.category !== 'All' && d.category !== o.category) return false;
    if (o.avail === 'orderable' && !d.orderable) return false;
    if (o.avail === 'inquiry' && d.orderable) return false;
    if (o.type && d.types.indexOf(o.type) === -1) return false;
    if (o.maxBdt && !(d.minBdt !== null && d.minBdt <= o.maxBdt)) return false;
    return true;
  }

  function search(index, q, o) {
    o = o || {};
    var qt = tokens(q), joinedQ = qt.join(''), out = [];
    index.forEach(function (d) {
      if (!passes(d, o)) return;
      var score = qt.length ? scoreDoc(qt, joinedQ, d) : 0;
      if (qt.length && !score) return;
      out.push({ d: d, score: score });
    });
    var sort = o.sort || 'relevance';
    out.sort(function (a, b) {
      if (sort === 'price') {
        var pa = a.d.minBdt === null ? Infinity : a.d.minBdt, pb = b.d.minBdt === null ? Infinity : b.d.minBdt;
        if (pa !== pb) return pa < pb ? -1 : 1;
      } else if (sort === 'relevance' && qt.length && b.score !== a.score) {
        return b.score - a.score;
      }
      return a.d.name.localeCompare(b.d.name);
    });
    return out.map(function (r) { return r.d; });
  }

  // Closest product names for a query that matched nothing.
  function didYouMean(index, q, n) {
    var joinedQ = tokens(q).join('');
    if (joinedQ.length < 3) return [];
    var max = Math.min(3, Math.max(1, Math.floor(joinedQ.length / 3)));
    return index.map(function (d) {
      var best = dist(joinedQ, d.joined.slice(0, joinedQ.length + 1), max);
      d.nameToks.forEach(function (t) { var v = dist(joinedQ, t, max); if (v < best) best = v; });
      return { d: d, v: best };
    }).filter(function (r) { return r.v <= max; })
      .sort(function (a, b) { return a.v - b.v || a.d.name.localeCompare(b.d.name); })
      .slice(0, n || 3).map(function (r) { return r.d; });
  }

  var api = { norm: norm, tokens: tokens, dist: dist, safePlans: safePlans, buildIndex: buildIndex,
              search: search, didYouMean: didYouMean, CAT_WORDS: CAT_WORDS };

  /* ---------------------------------------------------------------- UI ---- */

  var L10N = {
    en: {
      all: 'All', placeholder: 'Search: ChatGPT, video editing, ছবি, gaan…', label: 'Search products',
      avail: 'Availability', availAll: 'Any availability', availOrder: 'Order-ready (published price)',
      availInquiry: 'Price on request', type: 'Access', typeAny: 'Any access type',
      types: { personal: 'Personal', team: 'Team', official: 'Official' },
      budget: 'Budget', budgetAny: 'Any budget', upTo: 'Up to ', sort: 'Sort', sortRel: 'Best match',
      sortName: 'Name A–Z', sortPrice: 'Price: low to high', from: 'From ', onRequest: 'Price on request',
      details: 'Details', product: 'product', products: 'products', inCat: ' in ', matching: ' matching ',
      bundlesBelow: function (n) { return ' + ' + n + ' bundle' + (n === 1 ? '' : 's') + ' below'; },
      none: function (q) { return 'No product matches “' + q + '”.'; },
      dym: 'Did you mean:', tryCats: 'Or browse a category:', ask: 'Ask a human on WhatsApp',
      clear: 'Clear filters', sugg: 'Suggestions', noJs: ''
    },
    bn: {
      all: 'সব', placeholder: 'খুঁজুন: ChatGPT, ভিডিও এডিট, chobi, গান…', label: 'প্রোডাক্ট খুঁজুন',
      avail: 'উপলভ্যতা', availAll: 'সব', availOrder: 'অর্ডারযোগ্য (দাম প্রকাশিত)',
      availInquiry: 'মূল্য অনুরোধসাপেক্ষ', type: 'অ্যাক্সেস', typeAny: 'যেকোনো অ্যাক্সেস',
      types: { personal: 'পার্সোনাল', team: 'টিম', official: 'অফিশিয়াল' },
      budget: 'বাজেট', budgetAny: 'যেকোনো বাজেট', upTo: 'সর্বোচ্চ ', sort: 'সাজান', sortRel: 'সবচেয়ে মিল',
      sortName: 'নাম (A–Z)', sortPrice: 'দাম: কম থেকে বেশি', from: 'শুরু ', onRequest: 'মূল্য অনুরোধসাপেক্ষ',
      details: 'বিস্তারিত', product: 'টি প্রোডাক্ট', products: 'টি প্রোডাক্ট', inCat: ' — ', matching: ' — খোঁজ: ',
      bundlesBelow: function (n) { return ' + নিচে ' + bnDigits(n) + 'টি বান্ডেল'; },
      none: function (q) { return '“' + q + '” — কোনো প্রোডাক্ট মেলেনি।'; },
      dym: 'আপনি কি এটা খুঁজছেন:', tryCats: 'অথবা ক্যাটাগরি দেখুন:', ask: 'হোয়াটসঅ্যাপে মানুষের সাথে কথা বলুন',
      clear: 'ফিল্টার মুছুন', sugg: 'পরামর্শ', noJs: ''
    }
  };
  var BUDGETS = [500, 1000, 2500, 5000];
  var WA = 'https://wa.me/8801305869242?text=' + encodeURIComponent('Hi! Help me choose a subscription');

  function bnDigits(v) { return String(v).replace(/[0-9]/g, function (d) { return String.fromCharCode(0x09e6 + Number(d)); }); }
  function esc(v) {
    return String(v == null ? '' : v).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }
  function money(n, lang) {
    var s = '৳' + Number(n).toLocaleString('en-IN');
    return lang === 'bn' ? bnDigits(s) : s;
  }

  // Listing card: a link to the product page only. Never a cart action.
  function cardHtml(d, lang) {
    var T = L10N[lang === 'bn' ? 'bn' : 'en'];
    var types = d.types.map(function (t) { return '<span>' + esc(T.types[t] || t) + '</span>'; }).join('');
    var price = d.orderable
      ? '<div class="price">' + esc(T.from) + money(d.minBdt, lang) + '</div>'
      : '<div class="price req">' + esc(T.onRequest) + '</div>';
    return '<div class="pcard" data-id="' + esc(d.id) + '"><span class="icon" aria-hidden="true">' + esc(d.icon) +
      '</span><h3>' + esc(d.name) + '</h3><span class="cat">' + esc(d.category) + '</span>' +
      (types ? '<div class="sos-types">' + types + '</div>' : '') + price +
      '<div class="ctas"><a class="btn btn-ghost btn-sm" href="p/' + encodeURIComponent(d.id) + '">' + esc(T.details) +
      '<span class="sos-sr"> — ' + esc(d.name) + '</span></a></div></div>';
  }
  api.cardHtml = cardHtml;

  // catalog.js declares `const CATALOG`: a global lexical binding, NOT a window property.
  function pageCatalog() {
    /* global CATALOG */
    return typeof CATALOG !== 'undefined' ? CATALOG : (root.CATALOG || null);
  }
  api.pageCatalog = pageCatalog;

  var CSS = '.toolbar.sos-disc{display:block;margin:22px 0 6px}' +
    '.sos-sbox{position:relative;max-width:640px}' +
    '.toolbar .sos-sbox input[type=search]{display:block;width:100%;max-width:none;min-width:0;box-sizing:border-box;font-size:16px;min-height:48px}' +
    '.sos-sugg{position:absolute;left:0;right:0;top:100%;z-index:30;margin:4px 0 0;padding:6px;list-style:none;' +
    'background:var(--card,#0f3337);border:1px solid var(--line,#345);border-radius:14px;box-shadow:0 12px 32px rgba(0,0,0,.35)}' +
    '.sos-sugg[hidden]{display:none}' +
    '.sos-sugg li{display:flex;gap:10px;align-items:center;padding:10px 12px;border-radius:10px;cursor:pointer;min-height:44px}' +
    '.sos-sugg li[aria-selected=true],.sos-sugg li:hover{background:rgba(46,240,210,.12)}' +
    '.sos-sugg small{color:var(--muted,#93bdb7);margin-left:auto;font-size:12px}' +
    '.sos-filters{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:12px 0 4px}' +
    '@media (max-width:600px){#chips.chips{flex-wrap:nowrap;overflow-x:auto;-webkit-overflow-scrolling:touch;' +
    'scrollbar-width:thin;padding-bottom:6px}#chips .chip{flex:none}' +
    '.sos-filters{grid-template-columns:1fr 1fr;gap:8px}.sos-filters label{min-width:0}' +
    '.sos-filters select{min-width:0;font-size:13px;padding:8px 10px;text-overflow:ellipsis}}' +
    '.sos-filters select{width:100%;min-height:44px;padding:10px 12px;font-size:14px}' +
    '.sos-filters label{display:flex;flex-direction:column;gap:4px;font-size:12px;font-weight:700;color:var(--muted,#93bdb7);text-transform:uppercase;letter-spacing:.4px}' +
    '.chip{min-height:40px}' +
    '.chip[aria-pressed=true]{background:var(--grad);color:#04122b;border-color:transparent}' +
    '.chip:focus-visible,.sos-sugg li:focus-visible{outline:2px solid var(--green2,#2ef0d2);outline-offset:2px}' +
    '.pcard .sos-types{display:flex;gap:6px;flex-wrap:wrap;margin:6px 0 0}' +
    '.pcard .sos-types span{font-size:11px;font-weight:700;padding:3px 8px;border-radius:999px;border:1px solid var(--line,#345);color:var(--muted,#93bdb7)}' +
    '.pcard .price.req{font-size:15px;color:var(--muted,#93bdb7)}' +
    '.sos-empty{padding:18px;border:1px dashed var(--line,#345);border-radius:14px;color:var(--muted,#93bdb7)}' +
    '.sos-empty .chip{margin:4px}' +
    '.sos-sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}' +
    '@media (prefers-reduced-motion:reduce){.sos-sugg li{transition:none}}';

  function mount(opts) {
    var doc = root.document;
    var grid = doc && doc.getElementById('grid'), input = doc && doc.getElementById('q');
    var catalog = (opts && opts.catalog) || pageCatalog();
    if (!grid || !input || !catalog) return null;
    var lang = opts && opts.lang === 'bn' ? 'bn' : 'en', T = L10N[lang];
    var index = buildIndex(catalog);
    var cats = ['All'].concat((catalog.categories || []).filter(function (c) {
      return c !== 'Bundles' && index.some(function (d) { return d.category === c; });
    }));
    var state = { q: '', category: (opts && opts.category) || 'All', avail: '', type: '', maxBdt: 0, sort: 'relevance' };

    var style = doc.createElement('style');
    style.textContent = CSS;
    doc.head.appendChild(style);

    // Enhance the existing toolbar in place (same ids, so older build steps still find them).
    var toolbar = input.parentNode;
    toolbar.className += ' sos-disc';
    var box = doc.createElement('div');
    box.className = 'sos-sbox';
    toolbar.insertBefore(box, input);
    box.appendChild(input);
    input.removeAttribute('oninput');
    input.setAttribute('placeholder', T.placeholder);
    input.setAttribute('aria-label', T.label);
    input.setAttribute('role', 'combobox');
    input.setAttribute('aria-autocomplete', 'list');
    input.setAttribute('aria-expanded', 'false');
    input.setAttribute('aria-controls', 'sos-sugg');
    input.setAttribute('autocomplete', 'off');
    input.setAttribute('enterkeyhint', 'search');
    var list = doc.createElement('ul');
    list.id = 'sos-sugg';
    list.className = 'sos-sugg';
    list.setAttribute('role', 'listbox');
    list.setAttribute('aria-label', T.sugg);
    list.hidden = true;
    box.appendChild(list);

    function select(id, label, options) {
      return '<label>' + esc(label) + '<select id="' + id + '">' + options.map(function (o) {
        return '<option value="' + esc(o[0]) + '">' + esc(o[1]) + '</option>';
      }).join('') + '</select></label>';
    }
    var hasType = function (t) { return index.some(function (d) { return d.types.indexOf(t) > -1; }); };
    var filters = doc.createElement('div');
    filters.className = 'sos-filters';
    filters.innerHTML =
      select('f-avail', T.avail, [['', T.availAll], ['orderable', T.availOrder], ['inquiry', T.availInquiry]]) +
      select('f-type', T.type, [['', T.typeAny]].concat(['personal', 'team', 'official'].filter(hasType).map(function (t) { return [t, T.types[t]]; }))) +
      select('f-budget', T.budget, [['', T.budgetAny]].concat(BUDGETS.map(function (b) { return [String(b), T.upTo + money(b, lang)]; }))) +
      select('f-sort', T.sort, [['relevance', T.sortRel], ['name', T.sortName], ['price', T.sortPrice]]);
    toolbar.appendChild(filters);

    var chipsEl = doc.getElementById('chips'), countEl = doc.getElementById('count');
    if (chipsEl) chipsEl.removeAttribute('role');

    function readUrl() {
      try {
        var u = new URLSearchParams(root.location.search);
        if (u.get('q')) state.q = u.get('q').slice(0, 80);
        if (u.get('cat') && cats.indexOf(u.get('cat')) > -1) state.category = u.get('cat');
        if (/^(orderable|inquiry)$/.test(u.get('avail') || '')) state.avail = u.get('avail');
        if (/^(personal|team|official)$/.test(u.get('type') || '')) state.type = u.get('type');
        if (BUDGETS.indexOf(Number(u.get('max'))) > -1) state.maxBdt = Number(u.get('max'));
        if (/^(name|price)$/.test(u.get('sort') || '')) state.sort = u.get('sort');
      } catch (e) { /* old browser: defaults */ }
    }
    function writeUrl() {
      if (!root.history || !root.history.replaceState) return;
      var u = new URLSearchParams();
      if (state.q) u.set('q', state.q);
      if (state.category !== 'All') u.set('cat', state.category);
      if (state.avail) u.set('avail', state.avail);
      if (state.type) u.set('type', state.type);
      if (state.maxBdt) u.set('max', String(state.maxBdt));
      if (state.sort !== 'relevance') u.set('sort', state.sort);
      var s = u.toString();
      try { root.history.replaceState(null, '', root.location.pathname + (s ? '?' + s : '') + root.location.hash); } catch (e) { /* ignore */ }
    }

    function catLabel(c) { return c === 'All' ? T.all : c; }
    function drawChips() {
      if (!chipsEl) return;
      chipsEl.innerHTML = cats.map(function (c) {
        return '<button type="button" class="chip' + (c === state.category ? ' on' : '') + '" aria-pressed="' +
          (c === state.category) + '" data-cat="' + esc(c) + '">' + esc(catLabel(c)) + '</button>';
      }).join('');
    }

    function card(d) { return cardHtml(d, lang); }

    function emptyState(q) {
      var dym = didYouMean(index.filter(function (d) { return !d.bundle; }), q, 3);
      return '<div class="sos-empty" role="status"><p><b>' + esc(T.none(q)) + '</b></p>' +
        (dym.length ? '<p>' + esc(T.dym) + ' ' + dym.map(function (d) {
          return '<button type="button" class="chip" data-q="' + esc(d.name) + '">' + esc(d.name) + '</button>';
        }).join('') + '</p>' : '') +
        '<p>' + esc(T.tryCats) + ' ' + cats.filter(function (c) { return c !== 'All'; }).map(function (c) {
          return '<button type="button" class="chip" data-cat="' + esc(c) + '" data-reset="1">' + esc(c) + '</button>';
        }).join('') + '</p>' +
        '<p><button type="button" class="btn btn-ghost btn-sm" data-clear="1">' + esc(T.clear) + '</button> ' +
        '<a href="' + WA + '" target="_blank" rel="noopener" style="color:var(--green2);font-weight:800">' + esc(T.ask) + '</a></p></div>';
    }

    function draw() {
      var o = { category: state.category, avail: state.avail, type: state.type, maxBdt: state.maxBdt, sort: state.sort };
      var res = search(index, state.q, o).filter(function (d) { return !d.bundle; });
      var shownQ = state.q.replace(/[<>&"']/g, '').slice(0, 80);
      grid.innerHTML = res.length ? res.map(card).join('') : emptyState(shownQ);
      if (countEl) {
        var n = res.length, nb = index.filter(function (d) { return d.bundle; }).length;
        var filtered = state.q || state.avail || state.type || state.maxBdt;
        countEl.textContent = (lang === 'bn' ? bnDigits(n) : n) + ' ' + (n === 1 ? T.product : T.products) +
          (state.category !== 'All' ? T.inCat + state.category : '') +
          (shownQ ? T.matching + '“' + shownQ + '”' : '') +
          (state.category === 'All' && !filtered && nb ? T.bundlesBelow(nb) : '');
      }
      drawChips();
      writeUrl();
    }

    var active = -1, items = [];
    function closeSugg() { list.hidden = true; input.setAttribute('aria-expanded', 'false'); input.removeAttribute('aria-activedescendant'); active = -1; }
    function suggest() {
      items = state.q.trim() ? search(index, state.q, { sort: 'relevance' }).slice(0, 6) : [];
      if (!items.length) { closeSugg(); return; }
      list.innerHTML = items.map(function (d, i) {
        return '<li role="option" id="sos-opt-' + i + '" aria-selected="false" data-i="' + i + '"><span aria-hidden="true">' +
          esc(d.icon) + '</span><span>' + esc(d.name) + '</span><small>' +
          esc(d.orderable ? T.from + money(d.minBdt, lang) : T.onRequest) + '</small></li>';
      }).join('');
      list.hidden = false;
      input.setAttribute('aria-expanded', 'true');
      active = -1;
    }
    function highlight(i) {
      var lis = list.querySelectorAll('li');
      if (!lis.length) return;
      active = (i + lis.length) % lis.length;
      for (var k = 0; k < lis.length; k++) lis[k].setAttribute('aria-selected', String(k === active));
      input.setAttribute('aria-activedescendant', 'sos-opt-' + active);
    }
    function go(d) { root.location.href = 'p/' + encodeURIComponent(d.id); }

    var timer = null;
    input.addEventListener('input', function () {
      state.q = input.value.slice(0, 80);
      if (timer) root.clearTimeout(timer);
      timer = root.setTimeout(function () { draw(); suggest(); }, 60);
    });
    input.addEventListener('keydown', function (e) {
      var open = !list.hidden;
      if (e.key === 'ArrowDown') { e.preventDefault(); if (!open) suggest(); highlight(active + 1); }
      else if (e.key === 'ArrowUp' && open) { e.preventDefault(); highlight(active - 1); }
      else if (e.key === 'Enter') {
        if (open && active > -1 && items[active]) { e.preventDefault(); go(items[active]); }
        else { closeSugg(); draw(); }
      } else if (e.key === 'Escape') {
        if (open) closeSugg(); else if (input.value) { input.value = ''; state.q = ''; draw(); }
      }
    });
    input.addEventListener('blur', function () { root.setTimeout(closeSugg, 150); });
    list.addEventListener('mousedown', function (e) {
      var li = e.target.closest ? e.target.closest('li') : null;
      if (li && items[Number(li.getAttribute('data-i'))]) { e.preventDefault(); go(items[Number(li.getAttribute('data-i'))]); }
    });

    function onSelect(id, key, cast) {
      var el = doc.getElementById(id);
      el.addEventListener('change', function () { state[key] = cast(el.value); draw(); });
      return el;
    }
    var fAvail = onSelect('f-avail', 'avail', String), fType = onSelect('f-type', 'type', String);
    var fBudget = onSelect('f-budget', 'maxBdt', function (v) { return Number(v) || 0; });
    var fSort = onSelect('f-sort', 'sort', function (v) { return v || 'relevance'; });

    function clickHandler(e) {
      var b = e.target.closest ? e.target.closest('button') : null;
      if (!b) return;
      if (b.hasAttribute('data-clear')) {
        state.q = ''; state.avail = ''; state.type = ''; state.maxBdt = 0; state.category = 'All'; sync(); draw(); return;
      }
      if (b.hasAttribute('data-q')) { state.q = b.getAttribute('data-q'); sync(); draw(); input.focus(); return; }
      if (b.hasAttribute('data-cat')) {
        if (b.hasAttribute('data-reset')) state.q = '';
        state.category = b.getAttribute('data-cat'); sync(); draw();
      }
    }
    if (chipsEl) chipsEl.addEventListener('click', clickHandler);
    grid.addEventListener('click', clickHandler);

    doc.addEventListener('keydown', function (e) {
      var tag = (e.target && e.target.tagName) || '';
      if (e.key === '/' && !/^(INPUT|TEXTAREA|SELECT)$/.test(tag)) { e.preventDefault(); input.focus(); }
    });

    function sync() {
      input.value = state.q; fAvail.value = state.avail; fType.value = state.type;
      fBudget.value = state.maxBdt ? String(state.maxBdt) : ''; fSort.value = state.sort;
    }

    var bgrid = doc.getElementById('bgrid');
    if (bgrid) bgrid.innerHTML = index.filter(function (d) { return d.bundle; }).map(card).join('');

    readUrl();
    sync();
    draw();
    return { index: index, state: state, draw: draw };
  }

  api.mount = mount;
  root.SOSSearch = api;
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
})(typeof window !== 'undefined' ? window : globalThis);
