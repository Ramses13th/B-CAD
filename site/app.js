/* No libraries, tracking, or third-party requests. */
(() => {
  'use strict';
  document.body.classList.add('js-ready');
  const toggle = document.querySelector('[data-nav-toggle]');
  const navigation = document.querySelector('[data-navigation]');
  if (toggle && navigation) {
    const closeNavigation = () => { toggle.setAttribute('aria-expanded', 'false'); navigation.classList.remove('is-open'); };
    toggle.addEventListener('click', () => {
      const isOpen = toggle.getAttribute('aria-expanded') !== 'true';
      toggle.setAttribute('aria-expanded', String(isOpen));
      navigation.classList.toggle('is-open', isOpen);
    });
    navigation.addEventListener('click', (event) => { if (event.target.closest('a')) closeNavigation(); });
    document.addEventListener('keydown', (event) => { if (event.key === 'Escape' && toggle.getAttribute('aria-expanded') === 'true') { closeNavigation(); if (navigation.contains(document.activeElement)) toggle.focus(); } });
    window.matchMedia('(min-width: 601px)').addEventListener('change', (event) => { if (event.matches) closeNavigation(); });
  }

  const form = document.querySelector('[data-search-form]');
  const input = document.querySelector('[data-search-input]');
  const results = document.querySelector('[data-search-results]');
  const status = document.querySelector('[data-search-status]');
  if (!form || !input || !results || !status) return;

  const base = document.body.dataset.base || './';
  let entriesPromise;
  const loadEntries = () => {
    if (!entriesPromise) entriesPromise = fetch(new URL(base + 'search-index.json', document.baseURI)).then((response) => {
      if (!response.ok) throw new Error('Search index unavailable');
      return response.json();
    }).then((data) => Array.isArray(data) ? data : (data.pages || data.entries || []));
    return entriesPromise;
  };
  const normalize = (value) => String(value || '').toLocaleLowerCase();
  const getTokens = (value) => [...new Set(normalize(value).match(/[\p{L}\p{N}]+/gu) || [])].slice(0, 12);
  const snippet = (entry, tokens) => {
    const source = String(entry.content || entry.text || entry.description || '').replace(/\s+/g, ' ').trim();
    const haystack = normalize(source);
    const positions = tokens.map((token) => haystack.indexOf(token)).filter((position) => position >= 0);
    const position = positions.length ? Math.min(...positions) : 0;
    const start = Math.max(0, position - 55);
    let end = Math.min(source.length, start + 225);
    if (end < source.length) { const space = source.lastIndexOf(' ', end); if (space > start + 120) end = space; }
    return (start ? '…' : '') + source.slice(start, end).trim() + (end < source.length ? '…' : '');
  };
  const addHighlightedText = (node, value, tokens) => {
    const escapedTokens = tokens.map((token) => token.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).sort((a, b) => b.length - a.length);
    if (!escapedTokens.length) { node.textContent = value; return; }
    const pattern = new RegExp('(' + escapedTokens.join('|') + ')', 'giu');
    let offset = 0;
    for (const match of value.matchAll(pattern)) {
      node.append(document.createTextNode(value.slice(offset, match.index)));
      const mark = document.createElement('mark'); mark.textContent = match[0]; node.append(mark);
      offset = match.index + match[0].length;
    }
    node.append(document.createTextNode(value.slice(offset)));
  };
  let currentRun = 0;
  const search = async (query) => {
    const run = ++currentRun;
    const tokens = getTokens(query);
    results.replaceChildren();
    if (!tokens.length) { status.textContent = 'Search architecture, installation, the roadmap, or contribution guidelines.'; return; }
    status.textContent = 'Searching the blueprint…';
    try {
      const entries = await loadEntries();
      if (run !== currentRun) return;
      const ranked = entries.map((entry) => {
        const title = normalize(entry.title);
        const description = normalize(entry.description);
        const content = normalize(entry.content || entry.text);
        if (!tokens.every((token) => title.includes(token) || description.includes(token) || content.includes(token))) return null;
        const score = tokens.reduce((total, token) => total + (title.includes(token) ? 10 : 0) + (description.includes(token) ? 4 : 0) + (content.includes(token) ? 1 : 0), 0);
        return { entry, score };
      }).filter(Boolean).sort((a, b) => b.score - a.score || String(a.entry.title).localeCompare(String(b.entry.title)));
      const visible = ranked.slice(0, 30);
      status.textContent = ranked.length ? `${ranked.length} ${ranked.length === 1 ? 'result' : 'results'} for “${query}”${ranked.length > 30 ? ' · showing the first 30' : ''}` : `No results for “${query}”. Try fewer words or another term.`;
      for (const { entry } of visible) {
        const rawURL = String(entry.url || entry.path || 'docs/index.html');
        const url = new URL(base + rawURL, document.baseURI);
        if (url.origin !== location.origin || !['http:', 'https:', 'file:'].includes(url.protocol)) continue;
        const article = document.createElement('article'); article.className = 'search-result';
        const heading = document.createElement('h2');
        const link = document.createElement('a'); link.href = url.href; link.textContent = String(entry.title || 'Documentation'); heading.append(link);
        const address = document.createElement('p'); address.className = 'search-result-url'; address.textContent = rawURL.replace(/\.html(?=#|$)/, '');
        const excerpt = document.createElement('p'); addHighlightedText(excerpt, snippet(entry, tokens), tokens);
        article.append(heading, address, excerpt); results.append(article);
      }
      if (!ranked.length) {
        const paragraph = document.createElement('p'); paragraph.className = 'search-empty';
        paragraph.append('You can also ');
        const link = document.createElement('a'); link.href = base + 'docs/index.html'; link.textContent = 'browse all documentation'; paragraph.append(link, '.'); results.append(paragraph);
      }
    } catch {
      if (run !== currentRun) return;
      status.textContent = 'Search could not load. Browse the documentation or try again.';
      const link = document.createElement('a'); link.href = base + 'docs/index.html'; link.textContent = 'Browse the documentation →'; results.append(link);
      entriesPromise = undefined;
    }
  };
  form.addEventListener('submit', (event) => {
    event.preventDefault();
    const query = input.value.trim().slice(0, 200); input.value = query;
    const url = new URL(location.href); if (query) url.searchParams.set('q', query); else url.searchParams.delete('q');
    history.replaceState(null, '', url); search(query);
  });
  const initial = new URL(location.href).searchParams.get('q') || '';
  input.value = initial.slice(0, 200); search(input.value);
  document.addEventListener('keydown', (event) => {
    if (event.key === '/' && !event.ctrlKey && !event.metaKey && !event.altKey && !['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement.tagName) && !document.activeElement.isContentEditable) { event.preventDefault(); input.focus(); }
  });
})();
