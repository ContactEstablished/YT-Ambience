import * as THREE from 'three';
import { BODY_FACTS, LOCATIONS } from './facts.js';
import { surfacePosition } from './orbits.js';

export function createExplorer({ canvas, camera, mars, moons, globe, focusBody, showLocation, onFactsChange }) {
  const layer = document.querySelector('#fact-markers');
  const navigation = document.querySelector('#fact-navigation');
  const panel = document.querySelector('#fact-card');
  const content = document.querySelector('#fact-content');
  const toggle = document.querySelector('#facts');
  const category = document.querySelector('#fact-category');
  const index = document.querySelector('#location-index');
  const launch = document.querySelector('#explore-launch');
  const search = document.querySelector('#fact-search');
  const list = document.querySelector('#location-list');
  const results = document.querySelector('#fact-results');
  const raycaster = new THREE.Raycaster();
  const ndc = new THREE.Vector2();
  const objects = [mars, ...moons];
  const bodies = { mars, phobos: moons[0], deimos: moons[1] };
  let enabled = false, selected = null, lastInvoker = null;
  let gesture = null, lastTap = null;
  let cardTimer = null;
  let highlighted = null;

  function textElement(tag, text, parent, className) {
    const element = document.createElement(tag);
    element.textContent = text;
    if (className) element.className = className;
    parent.append(element);
    return element;
  }
  function closeCard() {
    clearTimeout(cardTimer);
    panel.hidden = true;
    selected = null;
    const target = lastInvoker?.isConnected && lastInvoker.getClientRects().length ? lastInvoker : canvas;
    target.focus({ preventScroll: true });
  }
  function openCard(data, invoker = canvas) {
    if (!enabled) return;
    selected = data.id;
    lastInvoker = invoker;
    content.replaceChildren();
    textElement('p', data.category, content, 'eyebrow');
    const title = textElement('h2', data.title, content);
    title.id = 'fact-title';
    textElement('p', data.summary, content, 'fact-summary');
    const stats = document.createElement('dl');
    for (const [name, value] of data.stats ?? []) {
      textElement('dt', name, stats);
      textElement('dd', value, stats);
    }
    if (data.lat !== undefined) {
      textElement('dt', 'Coordinates', stats);
      textElement('dd', `${Math.abs(data.lat).toFixed(2)}°${data.lat < 0 ? 'S' : 'N'}, ${data.lon.toFixed(2)}°E`, stats);
    }
    content.append(stats);
    if (data.details) textElement('p', data.details, content, 'fact-summary');
    if (data.events) {
      textElement('h3', 'Notable events', content);
      const events = document.createElement('ul');
      data.events.forEach(([date, text]) => textElement('li', `${date} — ${text}`, events));
      content.append(events);
    }
    if (data.lat !== undefined || data.id !== 'mars') {
      const action = textElement('button', data.lat !== undefined ? 'Show location on Mars' : `Focus on ${data.title}`, content, 'fact-action');
      action.type = 'button';
      action.addEventListener('click', () => {
        if (data.lat !== undefined) showLocation(data); else focusBody(data.id);
        closeCard();
      });
    }
    textElement('p', 'Reference values, not live readings. Animation timing is adjusted for ambience.', content, 'fact-note');
    textElement('h3', 'Sources', content);
    for (const [title, url] of data.sources) {
      const link = textElement('a', title, content, 'fact-source');
      link.href = url;
      link.target = '_blank';
      link.rel = 'noopener noreferrer';
    }
    panel.hidden = false;
    panel.scrollTop = 0;
    document.querySelector('#close-fact').focus({ preventScroll: true });
  }
  const markers = [];
  for (const data of [...Object.values(BODY_FACTS), ...LOCATIONS]) {
    const button = textElement('button', '', layer, 'fact-marker');
    button.type = 'button';
    button.setAttribute('aria-label', `Learn about ${data.title}`);
    button.title = data.title;
    button.dataset.fact = data.id;
    if (data.lat !== undefined) {
      const label = textElement('span', '', button, 'location-label');
      textElement('strong', data.title, label);
      textElement('span', '', label, 'location-status');
    }
    button.hidden = true;
    button.addEventListener('click', event => {
      clearTimeout(cardTimer);
      if (event.detail === 0) openCard(data, button);
      else cardTimer = setTimeout(() => openCard(data, button), 350);
    });
    button.addEventListener('dblclick', () => {
      if (data.id === 'phobos' || data.id === 'deimos') { focusBody(data.id); closeCard(); }
    });
    markers.push({ data, button, local: data.lat === undefined ? null : new THREE.Vector3(...surfacePosition(data.lat, data.lon)) });
  }
  function highlightLocation(data) {
    clearLocation();
    highlighted = data.id;
    const marker = markers.find(marker => marker.data.id === highlighted);
    marker.button.classList.add('is-highlighted');
    marker.button.setAttribute('aria-label', `Selected location: ${data.title}. Click to read details.`);
    collapseNavigation();
    setLocationStatus('Turning to location…');
  }
  function collapseNavigation() {
    if (!enabled) return;
    navigation.hidden = panel.hidden = true;
    selected = null;
    launch.textContent = 'Browse locations';
  }
  function setLocationStatus(text) {
    const label = markers.find(marker => marker.data.id === highlighted)?.button.querySelector('.location-status');
    if (label && label.textContent !== text) label.textContent = text;
  }
  function clearLocation() {
    const marker = markers.find(marker => marker.data.id === highlighted);
    if (marker) {
      marker.button.classList.remove('is-highlighted');
      marker.button.setAttribute('aria-label', `Learn about ${marker.data.title}`);
    }
    highlighted = null;
  }
  function filterLocations() {
    index.replaceChildren(new Option('Choose a location or event…', ''));
    list.replaceChildren();
    const query = search.value.trim().toLocaleLowerCase();
    const matches = LOCATIONS.filter(data =>
      (category.value === 'all' || category.value === data.category)
      && [data.title, data.summary, data.details, ...data.stats.flat(), ...(data.events ?? []).flat()]
        .join(' ').toLocaleLowerCase().includes(query));
    results.textContent = matches.length ? `${matches.length} ${matches.length === 1 ? 'result' : 'results'}` : 'No matches. Try a mission name, region, or year.';
    for (const data of matches) {
      index.add(new Option(data.title, data.id));
      const button = textElement('button', '', list, 'location-result');
      button.type = 'button';
      button.dataset.location = data.id;
      textElement('span', data.title, button);
      const date = data.stats.find(([name]) => name.includes('Date') || name.includes('date'))?.[1];
      textElement('small', `${data.category}${date ? ` · ${date}` : ''}`, button);
      button.addEventListener('click', () => { index.value = data.id; openCard(data, button); });
    }
  }
  filterLocations();
  category.addEventListener('change', filterLocations);
  search.addEventListener('input', filterLocations);
  index.addEventListener('change', () => {
    const data = LOCATIONS.find(data => data.id === index.value);
    if (data) openCard(data, index);
  });
  navigation.querySelectorAll('[data-body]').forEach(button => {
    button.addEventListener('click', () => openCard(BODY_FACTS[button.dataset.body], button));
    button.addEventListener('dblclick', () => {
      focusBody(button.dataset.body);
      closeCard();
    });
  });
  function setEnabled(value) {
    enabled = value;
    toggle.setAttribute('aria-pressed', String(enabled));
    toggle.textContent = `Facts, landings & statistics: ${enabled ? 'on' : 'off'}`;
    launch.setAttribute('aria-pressed', String(enabled));
    launch.textContent = enabled ? 'Close explorer' : 'Explore Mars';
    layer.hidden = navigation.hidden = !enabled;
    if (!enabled) { clearTimeout(cardTimer); panel.hidden = true; selected = null; }
    onFactsChange(enabled);
  }
  toggle.addEventListener('click', () => setEnabled(!enabled));
  launch.addEventListener('click', () => {
    if (enabled && navigation.hidden) {
      navigation.hidden = false;
      launch.textContent = 'Close explorer';
      return;
    }
    setEnabled(!enabled);
    if (enabled) document.querySelector('#interface').hidden = true;
  });
  document.querySelector('#close-explorer').addEventListener('click', () => { setEnabled(false); launch.focus(); });
  document.querySelector('#close-fact').addEventListener('click', closeCard);
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && !panel.hidden) { event.preventDefault(); closeCard(); }
  });

  function hitBody(event) {
    const rect = canvas.getBoundingClientRect();
    ndc.set((event.clientX - rect.left) / rect.width * 2 - 1, 1 - (event.clientY - rect.top) / rect.height * 2);
    sceneMatrices();
    raycaster.setFromCamera(ndc, camera);
    const hit = raycaster.intersectObjects(objects, true)[0];
    if (!hit) return null;
    let object = hit.object;
    while (object && !object.userData.bodyId) object = object.parent;
    return object?.userData.bodyId;
  }
  // Ignore clicks produced by a drag or pinch. Body picking uses actual mesh
  // intersections; true-scale moons also have accessible fixed-size markers.
  canvas.addEventListener('pointerdown', event => {
    if (gesture) { gesture.moved = true; return; }
    gesture = { x: event.clientX, y: event.clientY, id: event.pointerId, moved: false };
  });
  canvas.addEventListener('pointermove', event => {
    if (gesture && Math.hypot(event.clientX - gesture.x, event.clientY - gesture.y) > 6) gesture.moved = true;
  });
  canvas.addEventListener('pointerup', event => {
    if (!gesture || gesture.id !== event.pointerId) return;
    const tapped = !gesture.moved;
    gesture = null;
    if (!tapped) { lastTap = null; return; }
    const id = hitBody(event);
    if (!id) { lastTap = null; return; }
    // A second tap at the moon's old orbit position must not select Mars after
    // the first tap has moved the moon into the centered presentation.
    if (lastTap?.focused && performance.now() - lastTap.time < 350) { lastTap = null; return; }
    if (id === 'phobos' || id === 'deimos') {
      clearTimeout(cardTimer);
      focusBody(id);
      panel.hidden = true;
      lastTap = { id, time: performance.now(), focused: true };
      return;
    }
    if (lastTap?.id === id && performance.now() - lastTap.time < 350) {
      clearTimeout(cardTimer);
      focusBody(id);
      panel.hidden = true;
      lastTap = null;
    } else {
      lastTap = { id, time: performance.now() };
      clearTimeout(cardTimer);
      cardTimer = setTimeout(() => openCard(BODY_FACTS[id]), 350);
    }
  });
  canvas.addEventListener('pointercancel', () => { gesture = null; lastTap = null; });
  window.addEventListener('blur', () => { gesture = null; lastTap = null; });
  document.addEventListener('visibilitychange', () => { gesture = null; lastTap = null; });

  const point = new THREE.Vector3(), projected = new THREE.Vector3(), normal = new THREE.Vector3();
  const marsCenter = new THREE.Vector3();
  const normalMatrix = new THREE.Matrix3();
  function sceneMatrices() { globe.updateWorldMatrix(true, true); camera.updateWorldMatrix(true, false); }
  function update() {
    if (!enabled) return;
    sceneMatrices();
    mars.getWorldPosition(marsCenter);
    normalMatrix.getNormalMatrix(mars.matrixWorld);
    const rect = canvas.getBoundingClientRect();
    const placed = [];
    // Place the selected location first, even when it shares coordinates with
    // a landing/event marker or belongs to a different category filter.
    const ordered = highlighted ? [...markers].sort((a, b) => Number(b.data.id === highlighted) - Number(a.data.id === highlighted)) : markers;
    for (const marker of ordered) {
      const { data, button, local } = marker;
      const isHighlighted = data.id === highlighted;
      if (local) {
        if (!isHighlighted && category.value !== 'all' && category.value !== data.category) { button.hidden = true; continue; }
        normal.copy(local).normalize().applyMatrix3(normalMatrix);
        if (normal.z <= 0.025) { button.hidden = true; continue; }
        point.copy(local).applyMatrix4(mars.matrixWorld);
      } else {
        bodies[data.id].getWorldPosition(point);
        if (data.id === 'mars') point.add(new THREE.Vector3(-0.72, 0.72, 0.2));
        else {
          const distanceSquared = (point.x - marsCenter.x) ** 2 + (point.y - marsCenter.y) ** 2;
          const front = marsCenter.z + Math.sqrt(Math.max(0, 1 - distanceSquared));
          if (distanceSquared < 1 && camera.position.z > front && point.z < front) { button.hidden = true; continue; }
        }
      }
      projected.copy(point).project(camera);
      const x = (projected.x + 1) * rect.width / 2, y = (1 - projected.y) * rect.height / 2;
      if (projected.z < -1 || projected.z > 1 || x < 14 || y < 14 || x > rect.width - 14 || y > rect.height - 14
        || placed.some(p => Math.hypot(p.x - x, p.y - y) < p.clearance)) { button.hidden = true; continue; }
      placed.push({ x, y, clearance: isHighlighted ? 85 : 26 });
      button.hidden = false;
      button.style.transform = `translate(${x}px, ${y}px) translate(-50%, -50%)`;
      button.setAttribute('aria-expanded', String(selected === data.id && !panel.hidden));
    }
  }
  function reset() {
    setEnabled(false);
    category.value = 'all';
    search.value = '';
    filterLocations();
    panel.hidden = true;
    gesture = lastTap = null;
  }
  return { update, reset, highlightLocation, clearLocation, setLocationStatus, collapseNavigation };
}
