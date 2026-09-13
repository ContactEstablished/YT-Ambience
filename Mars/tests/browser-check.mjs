import assert from 'node:assert/strict';
import { mkdir, writeFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { chromium } from 'playwright';
import { preview } from 'vite';

// Exercise the built page under a nested URL, with deterministic animation time.
const server = await preview({ configFile: false, base: '/Mars/', preview: { host: '127.0.0.1', port: 5178, strictPort: true } });
const browser = await chromium.launch({ headless: true, args: ['--enable-unsafe-swiftshader'] });
const url = 'http://127.0.0.1:5178/Mars/';
const results = [];
await mkdir('verification', { recursive: true });
const record = text => { results.push(text); console.log(`PASS ${text}`); };

async function prepare(options = {}) {
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, reducedMotion: 'reduce', ...options });
  await page.addInitScript(() => {
    let next = 0, time = 0;
    const queue = new Map();
    window.requestAnimationFrame = callback => { queue.set(++next, callback); return next; };
    window.cancelAnimationFrame = id => queue.delete(id);
    window.advanceScene = (seconds = 0.1) => {
      const count = Math.max(1, Math.ceil(seconds * 10));
      for (let i = 0; i < count; i++) {
        time += seconds * 1000 / count;
        const callbacks = [...queue.values()];
        queue.clear();
        callbacks.forEach(callback => callback(time));
      }
    };
  });
  return page;
}
const step = (page, seconds = 0.1) => page.evaluate(t => window.advanceScene(t), seconds);
const shot = async page => {
  const { width, height } = page.viewportSize();
  // Compare the scene without the focus outline or launcher's composited corners.
  // The launcher and its state are checked separately through the real UI below.
  const bytes = await page.screenshot({ clip: { x: 8, y: 8, width: width - 16, height: height - 16 }, mask: [page.locator('#explore-launch')] });
  return createHash('sha256').update(bytes).digest('hex');
};
const click = (page, selector) => page.$eval(selector, el => el.click());
const slider = (page, selector, value) => page.$eval(selector, (el, v) => { el.value = v; el.dispatchEvent(new Event('input', { bubbles: true })); }, value);
const lighting = (page, mode) => page.$eval('#lighting-mode', (el, value) => { el.value = value; el.dispatchEvent(new Event('change', { bubbles: true })); }, mode);
const ready = async page => {
  await page.goto(url);
  await page.waitForFunction(() => document.querySelector('#status').hidden, {}, { polling: 100 });
  await step(page);
};
// Screen-space reference for the requested 25° right-leaning north axis.
const tiltedLocation = (latitude, width = 1200, height = 800, zoom = 2, longitudePhase = -Math.PI / 2) => {
  const radius = Math.min(width, height) * zoom / 5.4 * 1.006;
  const latitudeRadians = latitude * Math.PI / 180;
  const across = radius * Math.cos(latitudeRadians) * Math.cos(longitudePhase);
  const north = radius * Math.sin(latitudeRadians);
  const tilt = 25 * Math.PI / 180;
  return { x: width / 2 + across * Math.cos(tilt) + north * Math.sin(tilt), y: height / 2 + across * Math.sin(tilt) - north * Math.cos(tilt) };
};

try {
  const page = await prepare();
  const requests = [], errors = [];
  page.on('request', req => requests.push(req.url()));
  page.on('pageerror', error => errors.push(error.message));
  page.on('console', msg => { if (msg.type() === 'error') errors.push(msg.text()); });
  await page.route('**/*', route => {
    const target = route.request().url();
    return /^https?:/.test(target) && !target.startsWith(url) ? route.abort() : route.continue();
  });
  await ready(page);
  assert.equal(await page.title(), 'Mars — Ambience');
  assert.equal(await page.locator('#interface').isHidden(), true);
  await page.screenshot({ path: 'verification/desktop.png' });
  const initial = await shot(page);
  await step(page, 2);
  assert.deepEqual(await shot(page), initial);
  record('Reduced motion starts with the entire scene stationary and controls hidden');

  await page.keyboard.press('Control+Shift+R');
  assert.equal(await page.locator('#interface h1').isVisible(), true);
  assert.equal(await page.locator('#speed-value').textContent(), '1.00×');
  assert.equal(await page.locator('#rotation').textContent(), 'Resume animation');
  await page.waitForTimeout(100);
  await step(page);
  await page.screenshot({ path: 'verification/desktop-controls.png' });
  const menuBounds = await page.locator('.toolbar').boundingBox();
  const sceneBounds = await page.locator('#mars').boundingBox();
  assert.ok(sceneBounds.x + sceneBounds.width <= menuBounds.x, 'desktop menu has its own space beside the scene');
  await page.locator('.toolbar').evaluate(el => { el.scrollTop = el.scrollHeight; });
  await page.locator('#close-settings').click();
  assert.equal(await page.locator('#interface').isHidden(), true);
  await page.keyboard.press('Control+Shift+R');
  await slider(page, '#speed', '0');
  await slider(page, '#orbit-speed', '20');
  assert.equal(await page.locator('#orbit-speed-value').textContent(), '20.00×');
  await click(page, '#rotation');
  await page.keyboard.press('Control+Shift+R');
  const beforeOrbit = await shot(page);
  await step(page, 2);
  assert.notDeepEqual(await shot(page), beforeOrbit);
  await page.screenshot({ path: 'verification/moon-transit.png' });
  await step(page, 4);
  await page.screenshot({ path: 'verification/moon-front.png' });
  await click(page, '#rotation');
  const paused = await shot(page);
  await step(page, 2);
  assert.deepEqual(await shot(page), paused);
  record('Independent orbit speed moves moons while Mars is stopped; pause freezes animation');

  await click(page, '#reset');
  await step(page);
  assert.deepEqual(await shot(page), initial);
  await slider(page, '#orbit-speed', '0');
  await slider(page, '#speed', '20');
  await click(page, '#rotation');
  await step(page, 2);
  assert.notDeepEqual(await shot(page), initial);
  await click(page, '#reset');
  await step(page);
  assert.deepEqual(await shot(page), initial);
  record('Mars spin runs independently; reset restores both speeds, orientation, phases, and zoom');

  await page.locator('#mars').focus();
  await page.keyboard.press('ArrowRight');
  await step(page);
  assert.notDeepEqual(await shot(page), initial);
  await click(page, '#reset');
  await page.mouse.move(900, 450);
  await page.mouse.down();
  await page.mouse.move(1000, 480);
  await page.mouse.up();
  await step(page);
  assert.notDeepEqual(await shot(page), initial);
  await click(page, '#reset');
  await page.mouse.wheel(0, -200);
  await page.waitForTimeout(100);
  await step(page);
  assert.notDeepEqual(await shot(page), initial);
  await click(page, '#reset');
  await page.keyboard.press('+');
  await step(page);
  assert.notDeepEqual(await shot(page), initial);
  await page.keyboard.press('-');
  await step(page);
  assert.deepEqual(await shot(page), initial);
  await click(page, '#zoom-in');
  await step(page);
  assert.notDeepEqual(await shot(page), initial);
  await click(page, '#zoom-out');
  await step(page);
  assert.deepEqual(await shot(page), initial);
  record('Drag, arrow keys, wheel, keyboard zoom, and zoom buttons respond correctly');

  await page.emulateMedia({ reducedMotion: 'no-preference' });
  await page.waitForTimeout(100);
  await step(page, 1);
  assert.equal(await page.locator('#rotation').textContent(), 'Pause animation');
  assert.notDeepEqual(await shot(page), initial);
  await page.evaluate(() => { Object.defineProperty(document, 'hidden', { configurable: true, get: () => true }); document.dispatchEvent(new Event('visibilitychange')); });
  const hidden = await shot(page);
  await step(page, 5);
  assert.deepEqual(await shot(page), hidden);
  await page.evaluate(() => { delete document.hidden; document.dispatchEvent(new Event('visibilitychange')); });
  await step(page, 1);
  assert.notDeepEqual(await shot(page), hidden);
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page.waitForTimeout(100);
  await step(page);
  const reduced = await shot(page);
  await step(page, 1);
  assert.deepEqual(await shot(page), reduced);
  record('Preference changes pause/resume motion; hidden-tab lifecycle suspends time advancement');

  assert.ok(requests.some(r => r.endsWith('phobos.glb')));
  assert.ok(requests.some(r => r.endsWith('deimos.glb')));
  assert.ok(requests.some(r => /mars-detail(?:-4k)?\.jpg$/.test(r)));
  assert.ok(requests.some(r => r.includes('draco_decoder.wasm')));
  assert.ok(requests.filter(r => /^https?:/.test(r)).every(r => r.startsWith(url)));
  assert.deepEqual(errors, []);
  record('Built page loads all imagery, models, and Draco locally under /Mars/, without console errors');

  const lit = await prepare({ viewport: { width: 640, height: 480 } });
  await ready(lit);
  const defaultLight = await shot(lit);
  const shadowShots = new Set();
  for (const percent of ['0', '50', '75', '100']) {
    await slider(lit, '#shadow', percent);
    await step(lit);
    assert.equal(await lit.locator('#shadow-value').textContent(), `${percent}%`);
    shadowShots.add(await shot(lit));
    await lit.screenshot({ path: `verification/shadow-${percent}.png` });
  }
  assert.equal(shadowShots.size, 4);
  await slider(lit, '#shadow', '75');
  await step(lit);
  const static75 = await shot(lit);
  await lighting(lit, 'cycle');
  await step(lit);
  assert.equal(await lit.locator('#shadow-controls').getAttribute('hidden'), '');
  assert.match(await lit.locator('#cycle-phase').textContent(), /^Daylight .*0% shadow$/);
  await step(lit, 1);
  assert.match(await lit.locator('#cycle-phase').textContent(), /^Daylight .*0% shadow$/);
  await lighting(lit, 'static');
  await step(lit);
  assert.equal(await lit.locator('#shadow').inputValue(), '75');
  assert.equal(await shot(lit), static75);
  await click(lit, '#reset');
  await step(lit);
  assert.equal(await lit.locator('#lighting-mode').inputValue(), 'static');
  assert.equal(await lit.locator('#shadow').inputValue(), '20');
  assert.equal(await shot(lit), defaultLight);
  record('Static 0/50/75/100% lighting renders distinctly; loop toggle preserves static shadow; reset restores 20%');

  await lighting(lit, 'cycle');
  await slider(lit, '#speed', '20');
  await slider(lit, '#orbit-speed', '0');
  await click(lit, '#rotation');
  const secondsPerTurn = Math.PI * 2 / (0.012 * 20);
  await step(lit, secondsPerTurn * 1.5);
  assert.match(await lit.locator('#cycle-phase').textContent(), /^Nightfall · Rotation 2 of 4 · 50% shadow$/);
  await lit.screenshot({ path: 'verification/cycle-nightfall.png' });
  await click(lit, '#rotation');
  const frozenCycle = await shot(lit);
  await step(lit, 1);
  assert.equal(await shot(lit), frozenCycle);
  await slider(lit, '#speed', '0');
  await click(lit, '#rotation');
  await step(lit, 1);
  assert.equal(await shot(lit), frozenCycle);
  await slider(lit, '#speed', '20');
  await step(lit, secondsPerTurn * 0.75);
  assert.match(await lit.locator('#cycle-phase').textContent(), /^Night · Rotation 3 of 4 · 100% shadow$/);
  await lit.screenshot({ path: 'verification/cycle-night.png' });
  await step(lit, secondsPerTurn * 1.25);
  assert.match(await lit.locator('#cycle-phase').textContent(), /^Dawn · Rotation 4 of 4 · 50% shadow$/);
  await lit.screenshot({ path: 'verification/cycle-dawn.png' });
  await step(lit, secondsPerTurn * 0.51);
  assert.match(await lit.locator('#cycle-phase').textContent(), /^Daylight · Rotation 1 of 4 · 0% shadow$/);
  await lit.keyboard.press('Control+Shift+R');
  await lit.screenshot({ path: 'verification/cycle-controls.png' });
  await lit.close();
  record('Full four-rotation loop reaches nightfall, night, dawn, and daylight; pause and zero Mars speed freeze it');

  const explore = await prepare({ viewport: { width: 1200, height: 800 } });
  await ready(explore);
  await click(explore, '#facts');
  await step(explore);
  const homePoint = tiltedLocation(18.65, 1200, 800, 1, 226.2 * Math.PI / 180 + 0.65);
  const initialOlympus = await explore.locator('[data-fact="olympus"]').boundingBox();
  assert.ok(initialOlympus && Math.hypot(initialOlympus.x + 14 - homePoint.x, initialOlympus.y + 14 - homePoint.y) < 1, 'initial scene has the requested 25-degree tilt');
  await explore.locator('#mars').focus();
  await explore.keyboard.press('ArrowUp');
  await explore.keyboard.press('ArrowRight');
  await step(explore);
  const draggedOlympus = await explore.locator('[data-fact="olympus"]').boundingBox();
  assert.ok(draggedOlympus && Math.hypot(draggedOlympus.x - initialOlympus.x, draggedOlympus.y - initialOlympus.y) > 1, 'manual orientation remains available');
  await click(explore, '#reset');
  await click(explore, '#facts');
  await step(explore);
  const resetOlympus = await explore.locator('[data-fact="olympus"]').boundingBox();
  assert.deepEqual(resetOlympus, initialOlympus, 'reset restores the original 25-degree orientation');
  await click(explore, '#facts');
  assert.equal(await explore.locator('#explore-launch').isVisible(), true);
  await explore.locator('#explore-launch').click();
  await step(explore);
  assert.equal(await explore.locator('#fact-navigation').isVisible(), true);
  assert.equal(await explore.locator('#facts').getAttribute('aria-pressed'), 'true');
  await explore.locator('#fact-category').selectOption('Landing site');
  assert.equal(await explore.locator('.location-result').count(), 9);
  for (const id of ['viking1', 'viking2', 'pathfinder', 'spirit', 'opportunity', 'phoenix', 'curiosity', 'insight', 'perseverance']) {
    await click(explore, `[data-location="${id}"]`);
    assert.ok(await explore.locator('#fact-content dt').count() >= 5);
    assert.ok(await explore.locator('#fact-content li').count() >= 1);
    assert.ok(await explore.locator('#fact-content a').count() >= 2);
    assert.match(await explore.locator('#fact-content').textContent(), /historic landing position/);
    await click(explore, '#close-fact');
  }
  await explore.locator('#fact-search').fill('Gale');
  assert.equal(await explore.locator('.location-result').count(), 1);
  await explore.locator('[data-location="curiosity"]').click();
  assert.match(await explore.locator('#fact-content').textContent(), /899 kg/);
  await explore.screenshot({ path: 'verification/landing-details.png' });
  await click(explore, '#close-fact');
  await explore.locator('#fact-search').fill('no such mission');
  assert.equal(await explore.locator('.location-result').count(), 0);
  assert.match(await explore.locator('#fact-results').textContent(), /No matches/);
  await explore.locator('#fact-search').fill('');
  await explore.locator('#fact-category').selectOption('Event');
  await explore.locator('#fact-search').fill('2008');
  assert.equal(await explore.locator('.location-result').count(), 1);
  await click(explore, '[data-location="phoenix-ice"]');
  assert.match(await explore.locator('#fact-content').textContent(), /2008-07-31/);
  await click(explore, '#close-fact');
  for (const body of ['mars', 'phobos', 'deimos']) {
    await click(explore, `[data-body="${body}"]`);
    const text = await explore.locator('#fact-content').textContent();
    assert.match(text, /Earth hours/);
    assert.match(text, /Earth days/);
    assert.match(text, /temperature/i);
    await click(explore, '#close-fact');
  }
  await click(explore, '#close-explorer');
  assert.equal(await explore.locator('#fact-navigation').isHidden(), true);
  assert.equal(await explore.locator('#explore-launch').getAttribute('aria-pressed'), 'false');
  await click(explore, '#reset');
  assert.equal(await explore.locator('#fact-search').inputValue(), '');
  record('Visible explorer launcher, nine detailed landing cards, search, events, body statistics, and close/reset pass');
  await click(explore, '#facts');
  await step(explore);
  assert.equal(await explore.locator('#fact-navigation').isVisible(), true);
  assert.ok(await explore.locator('.fact-marker:not([hidden])').count() >= 3);
  await explore.screenshot({ path: 'verification/explorer-markers.png' });
  await explore.locator('[data-fact="phobos"]').click();
  await explore.waitForFunction(() => !document.querySelector('#fact-card').hidden, {}, { polling: 100 });
  assert.equal(await explore.locator('#fact-title').textContent(), 'Phobos');
  assert.match(await explore.locator('#fact-content').textContent(), /9,375 km/);
  assert.ok(await explore.locator('#fact-content a[href^="https://"]').count() >= 2);
  await explore.screenshot({ path: 'verification/phobos-facts.png' });
  await click(explore, '#close-fact');
  await explore.locator('[data-fact="phobos"]').dblclick();
  await step(explore);
  assert.match(await explore.locator('#focus-status').textContent(), /Centered on Phobos/);
  const focusedCenter = async () => {
    const box = await explore.locator('[data-fact="phobos"]').boundingBox();
    assert.ok(box, 'focused moon locator is visible');
    assert.ok(Math.abs(box.x + box.width / 2 - 600) < 0.1);
    assert.ok(Math.abs(box.y + box.height / 2 - 400) < 0.1);
    // Read the rendered canvas immediately after a controlled frame. Terrain
    // must still fill all four sides of the centered Mars disk as moons orbit.
    const limbSamples = await explore.evaluate(() => {
      window.advanceScene(0);
      const source = document.querySelector('#mars');
      const copy = document.createElement('canvas');
      copy.width = source.width; copy.height = source.height;
      const context = copy.getContext('2d');
      context.drawImage(source, 0, 0);
      return [[228, 400], [972, 400], [600, 28], [600, 772]].map(([x, y]) => {
        const pixels = context.getImageData(x - 1, y - 1, 3, 3).data;
        let sum = 0;
        for (let i = 0; i < pixels.length; i += 4) sum += pixels[i] + pixels[i + 1] + pixels[i + 2];
        return sum / 9;
      });
    });
    assert.ok(limbSamples.every(value => value > 18), `Mars stays centered behind the moon: ${limbSamples}`);
  };
  await focusedCenter();
  await explore.screenshot({ path: 'verification/phobos-focus.png' });
  await slider(explore, '#orbit-speed', '20');
  await click(explore, '#rotation');
  const focusedStart = await shot(explore);
  await step(explore, 3);
  await focusedCenter();
  assert.notEqual(await shot(explore), focusedStart);
  await explore.$eval('#moon-scale', el => { el.value = 'true'; el.dispatchEvent(new Event('change')); });
  await step(explore, 3);
  await focusedCenter();
  await explore.screenshot({ path: 'verification/phobos-true-focus.png' });
  await click(explore, '#rotation');
  const frozenFocus = await shot(explore);
  await step(explore, 1);
  assert.equal(await shot(explore), frozenFocus);
  await click(explore, '#return-mars');
  await step(explore);
  assert.equal(await explore.locator('#return-mars').isHidden(), true);
  await explore.screenshot({ path: 'verification/true-scale-overview.png' });
  await click(explore, '#facts');
  await step(explore);
  assert.equal(await explore.locator('#fact-markers').isHidden(), true);
  assert.equal(await explore.locator('#moon-locators').isVisible(), true);
  assert.equal(await explore.locator('.moon-locator:visible').count(), 2);
  assert.equal(await explore.locator('.moon-locator[data-moon="phobos"]').evaluate(el => getComputedStyle(el, '::before').animationName), 'none', 'reduced motion uses a steady locator');
  await explore.screenshot({ path: 'verification/true-scale-locators.png' });
  await explore.locator('.moon-locator[data-moon="deimos"]').click();
  await step(explore);
  assert.match(await explore.locator('#focus-status').textContent(), /Centered on Deimos/);
  await explore.screenshot({ path: 'verification/deimos-centered.png' });
  await click(explore, '#reset');
  await click(explore, '#facts');
  await step(explore);
  await explore.locator('#location-index').selectOption('olympus');
  assert.match(await explore.locator('#fact-title').textContent(), /Olympus Mons/);
  await explore.getByRole('button', { name: 'Show location on Mars' }).evaluate(el => el.click());
  await step(explore);
  const olympus = await explore.locator('[data-fact="olympus"]').boundingBox();
  const olympusTarget = tiltedLocation(18.65);
  assert.ok(olympus && Math.hypot(olympus.x + 14 - olympusTarget.x, olympus.y + 14 - olympusTarget.y) < 1);
  await explore.screenshot({ path: 'verification/olympus-location.png' });
  // Visits undo a manually tilted view while retaining north/south latitude.
  for (const [id, latitude] of [['hellas', -42.43], ['phoenix', 68.22]]) {
    await explore.locator('#mars').focus();
    await explore.keyboard.press('ArrowUp');
    await explore.keyboard.press('ArrowRight');
    await click(explore, '#explore-launch');
    await explore.locator('#location-index').selectOption(id);
    await explore.getByRole('button', { name: 'Show location on Mars' }).evaluate(el => el.click());
    await step(explore);
    const point = await explore.locator(`[data-fact="${id}"]`).boundingBox();
    const target = tiltedLocation(latitude);
    assert.ok(point && Math.hypot(point.x + 14 - target.x, point.y + 14 - target.y) < 1);
    await explore.screenshot({ path: `verification/tilted-${id}.png` });
  }
  await click(explore, '#explore-launch');
  await explore.locator('#fact-category').selectOption('Landing site');
  await step(explore);
  assert.equal(await explore.locator('#location-index option').count(), 10);
  assert.equal(await explore.locator('[data-fact="phoenix"]').isVisible(), true, 'selected location stays highlighted across filters');
  await explore.locator('#location-index').selectOption('perseverance');
  assert.match(await explore.locator('#fact-content').textContent(), /2021-02-18/);
  await explore.keyboard.press('Escape');
  assert.equal(await explore.locator('#fact-card').isHidden(), true);
  await click(explore, '#facts');
  assert.equal(await explore.locator('#fact-markers').isHidden(), true);
  await click(explore, '#reset');
  // Pick the actual mesh with facts off, independent of DOM locator targets.
  await click(explore, '#facts');
  await step(explore);
  const meshTarget = await explore.locator('[data-fact="phobos"]').boundingBox();
  await click(explore, '#facts');
  await explore.mouse.click(meshTarget.x + meshTarget.width / 2, meshTarget.y + meshTarget.height / 2);
  await step(explore);
  assert.match(await explore.locator('#focus-status').textContent(), /Centered on Phobos/);
  await click(explore, '#return-mars');
  await click(explore, '#reset');
  for (let i = 0; i < 45; i++) await click(explore, '#zoom-in');
  await step(explore);
  await explore.screenshot({ path: 'verification/mars-close-zoom.png' });
  // At 30x the scene fills the viewport with terrain; the renderer is still
  // outside the planet rather than clipping through a scaled sphere.
  const closeZoom = await shot(explore);
  await click(explore, '#zoom-in');
  await step(explore);
  assert.equal(await shot(explore), closeZoom);
  await click(explore, '#reset');
  await slider(explore, '#shadow', '100');
  await step(explore);
  await explore.screenshot({ path: 'verification/night-visibility.png' });
  await explore.close();
  record('Facts, source links, location placement/filtering, true-scale moon tracking, pause, return, reset, and 30x zoom pass');

  const visit = await prepare({ viewport: { width: 1200, height: 800 }, reducedMotion: 'no-preference' });
  await ready(visit);
  await visit.$eval('#moon-scale', el => { el.value = 'true'; el.dispatchEvent(new Event('change')); });
  await step(visit);
  const sonar = visit.locator('.moon-locator[data-moon="phobos"]');
  for (let phase = 0; phase < 5; phase++) {
    await step(visit, 1);
    assert.deepEqual(await visit.locator('.moon-locator-label').allTextContents(), ['Phobos', 'Deimos']);
    assert.ok((await visit.locator('.moon-locator').evaluateAll(els => els.map(el => el.title))).every(title => !/behind/i.test(title)));
  }
  assert.equal(await sonar.evaluate(el => getComputedStyle(el, '::before').animationDuration), '5s');
  const sonarPhases = await sonar.evaluate(el => {
    const animation = el.getAnimations({ subtree: true }).find(animation => animation.animationName === 'moon-sonar');
    animation.pause();
    return [500, 4500, 5500].map(time => {
      animation.currentTime = time;
      return getComputedStyle(el, '::before').opacity;
    });
  });
  assert.ok(Number(sonarPhases[0]) > 0 && Number(sonarPhases[1]) === 0);
  assert.equal(sonarPhases[0], sonarPhases[2], 'sonar repeats at five seconds');
  await visit.screenshot({ path: 'verification/moon-sonar.png' });
  await click(visit, '#reset');
  await slider(visit, '#speed', '20');
  await click(visit, '#explore-launch');
  await visit.locator('#location-index').selectOption('ingenuity');
  await visit.getByRole('button', { name: 'Show location on Mars' }).evaluate(el => el.click());
  const selectedPoint = visit.locator('[data-fact="ingenuity"]');
  const pointCenter = async () => {
    const box = await selectedPoint.boundingBox();
    assert.ok(box, 'selected event remains visible, including when it overlaps its landing site');
    return { x: box.x + box.width / 2, y: box.y + box.height / 2 };
  };
  await step(visit, 0.4);
  assert.match(await selectedPoint.textContent(), /Turning to location/);
  const turning = await selectedPoint.boundingBox();
  // A far-side point may still be occluded early in the flight.
  const visitTarget = tiltedLocation(18.44);
  assert.ok(!turning || Math.hypot(turning.x + 14 - visitTarget.x, turning.y + 14 - visitTarget.y) > 2, 'flight has not snapped to its destination');
  await step(visit, 0.9);
  const arrived = await pointCenter();
  assert.ok(Math.hypot(arrived.x - visitTarget.x, arrived.y - visitTarget.y) < 1);
  assert.equal(await visit.locator('#fact-navigation').isHidden(), true);
  assert.equal(await visit.locator('[data-fact="perseverance"]').isHidden(), true);
  assert.match(await selectedPoint.textContent(), /Rotation resumes in 15s/);
  await visit.screenshot({ path: 'verification/location-highlight.png' });
  const moonStart = await visit.locator('[data-fact="phobos"]').getAttribute('style');
  await step(visit, 14.7);
  assert.deepEqual(await pointCenter(), arrived, 'Mars stays centered throughout the 15-second hold');
  assert.notEqual(await visit.locator('[data-fact="phobos"]').getAttribute('style'), moonStart, 'moons keep orbiting during the hold');
  assert.match(await selectedPoint.textContent(), /Rotation resumes in 1s/);
  await step(visit, 0.6);
  assert.match(await selectedPoint.textContent(), /Rotation resumed/);
  const resumed = await pointCenter();
  assert.ok(Math.hypot(resumed.x - arrived.x, resumed.y - arrived.y) > 1);
  assert.ok(Math.abs((resumed.y - arrived.y) - Math.tan(25 * Math.PI / 180) * (resumed.x - arrived.x)) < 0.1, 'resumed rotation preserves the 25-degree north axis');
  await click(visit, '#rotation');
  await click(visit, '#explore-launch');
  await visit.locator('#location-index').selectOption('ingenuity');
  await visit.getByRole('button', { name: 'Show location on Mars' }).evaluate(el => el.click());
  await step(visit, 1.3);
  const pausedLocation = await pointCenter();
  await step(visit, 16);
  assert.deepEqual(await pointCenter(), pausedLocation, 'an already-paused animation must not start automatically');
  assert.equal(await visit.locator('#rotation').textContent(), 'Resume animation');
  assert.match(await selectedPoint.textContent(), /Rotation paused/);
  await click(visit, '#reset');
  assert.equal(await visit.locator('.is-highlighted').count(), 0);
  await visit.close();
  record('Location flight, labeled highlight, overlapping-event priority, 15-second hold, continued moon orbits, resume, and paused-state preservation pass');

  const mobile = await prepare({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true });
  await ready(mobile);
  await mobile.screenshot({ path: 'verification/mobile.png' });
  const mobileInitial = await shot(mobile);
  const cdp = await mobile.context().newCDPSession(mobile);
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchStart', touchPoints: [{ x: 140, y: 390, id: 0 }, { x: 240, y: 390, id: 1 }] });
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchMove', touchPoints: [{ x: 110, y: 390, id: 0 }, { x: 270, y: 390, id: 1 }] });
  await cdp.send('Input.dispatchTouchEvent', { type: 'touchEnd', touchPoints: [] });
  await step(mobile);
  assert.notDeepEqual(await shot(mobile), mobileInitial);
  await click(mobile, '#reset');
  await step(mobile);
  assert.deepEqual(await shot(mobile), mobileInitial);
  await mobile.keyboard.press('Control+Shift+R');
  await mobile.waitForTimeout(100);
  await step(mobile);
  await mobile.screenshot({ path: 'verification/mobile-controls.png' });
  for (const size of [{ width: 390, height: 844 }, { width: 844, height: 390 }]) {
    await mobile.setViewportSize(size);
    await mobile.waitForTimeout(100);
    await step(mobile);
    const bounds = await mobile.locator('.toolbar').boundingBox();
    assert.ok(bounds.x >= 0 && bounds.y >= 0 && bounds.x + bounds.width <= size.width && bounds.y + bounds.height <= size.height);
    const scene = await mobile.locator('#mars').boundingBox();
    assert.ok(scene.x + scene.width <= bounds.x || scene.y >= bounds.y + bounds.height, 'settings do not cover the mobile scene');
  }
  await mobile.screenshot({ path: 'verification/mobile-landscape-controls.png' });
  await lighting(mobile, 'cycle');
  await step(mobile);
  await mobile.screenshot({ path: 'verification/mobile-landscape-cycle.png' });
  const cycleBounds = await mobile.locator('.toolbar').boundingBox();
  assert.ok(cycleBounds.y >= 0 && cycleBounds.y + cycleBounds.height <= 390);
  await mobile.setViewportSize({ width: 390, height: 844 });
  await mobile.waitForTimeout(100);
  await mobile.locator('#explore-launch').tap();
  await step(mobile);
  assert.equal(await mobile.locator('#interface').isHidden(), true);
  await mobile.locator('#fact-search').fill('Jezero');
  await mobile.locator('[data-location="perseverance"]').tap();
  assert.match(await mobile.locator('#fact-content').textContent(), /2021-02-18/);
  await mobile.screenshot({ path: 'verification/mobile-landing-details.png' });
  await mobile.getByRole('button', { name: 'Show location on Mars' }).tap();
  await step(mobile);
  assert.equal(await mobile.locator('#fact-navigation').isHidden(), true);
  const mobilePoint = await mobile.locator('[data-fact="perseverance"]').boundingBox();
  const mobileTarget = tiltedLocation(18.44, 390, 844);
  assert.ok(mobilePoint && Math.hypot(mobilePoint.x + 14 - mobileTarget.x, mobilePoint.y + 14 - mobileTarget.y) < 1);
  const mobileLabel = await mobile.locator('.is-highlighted .location-label').boundingBox();
  assert.ok(mobileLabel && mobileLabel.x >= 0 && mobileLabel.x + mobileLabel.width <= 390);
  await mobile.screenshot({ path: 'verification/mobile-location-highlight.png' });
  await mobile.locator('#explore-launch').tap();
  await mobile.locator('#fact-search').fill('');
  await mobile.locator('#fact-navigation').evaluate(el => { el.scrollTop = 0; });
  await mobile.screenshot({ path: 'verification/mobile-explorer.png' });
  await mobile.locator('[data-body="deimos"]').click();
  await mobile.getByRole('button', { name: 'Focus on Deimos', exact: true }).evaluate(el => el.click());
  await step(mobile);
  assert.equal(await mobile.locator('#return-mars').isVisible(), true);
  assert.equal(await mobile.locator('#fact-navigation').isHidden(), true, 'moon focus clears the centered view on mobile');
  assert.equal(await mobile.locator('#interface').getAttribute('hidden'), '');
  await mobile.screenshot({ path: 'verification/mobile-moon-focus.png' });
  await click(mobile, '#reset');
  await mobile.close();
  record('Mobile pinch zoom, reset, and portrait/landscape control layout pass');

  for (const asset of ['phobos.glb', 'deimos.glb', 'mars-detail*.jpg', 'draco_decoder.wasm']) {
    const broken = await prepare();
    await broken.route(`**/${asset}`, route => route.abort());
    await broken.goto(url);
    await broken.waitForFunction(() => document.querySelector('#status').textContent.includes('could not load'), {}, { polling: 100 });
    assert.equal(await broken.locator('button:not(:disabled), input:not(:disabled), select:not(:disabled)').count(), 0);
    await broken.close();
  }
  record('Missing Mars texture, either moon model, or decoder displays an error with disabled controls');

  const noGL = await prepare();
  await noGL.addInitScript(() => {
    const original = HTMLCanvasElement.prototype.getContext;
    HTMLCanvasElement.prototype.getContext = function(type, ...args) { return type.startsWith('webgl') ? null : original.call(this, type, ...args); };
  });
  await noGL.goto(url);
  await noGL.waitForFunction(() => document.querySelector('#status').textContent.includes('could not load'), {}, { polling: 100 });
  await page.evaluate(() => document.querySelector('#mars').getContext('webgl2').getExtension('WEBGL_lose_context').loseContext());
  await page.waitForFunction(() => document.querySelector('#status').textContent.includes('interrupted'), {}, { polling: 100 });
  assert.equal(await page.locator('button:not(:disabled), input:not(:disabled), select:not(:disabled)').count(), 0);
  record('Unavailable WebGL and actual context loss both display recovery messages');

  await writeFile('verification/results.json', JSON.stringify({ date: new Date().toISOString(), browser: await browser.version(), results }, null, 2));
} finally {
  await browser.close();
  await new Promise(resolve => server.httpServer.close(resolve));
}
