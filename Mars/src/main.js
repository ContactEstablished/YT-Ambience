import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js';
import { MOONS, moonDisplay, orbitPose, systemHalfHeight } from './orbits.js';
import { createExplorer } from './explorer.js';
import { DEFAULT_SHADOW, advanceCycle, getMarsLighting } from './lighting.js';
import { createStars } from './stars.js';
import { createMoonLocators } from './moon-locators.js';

const SETTINGS = {
  rotationSpeed: 0.012, // One turn in about 8 minutes 44 seconds at 1×.
  exposure: 1.08,
  sunlight: 3.2,
  fill: 0.025,
  nightVisibility: 0.08,
  halfFrame: 2.7,
  initialOrientation: [0, 0, -25 * Math.PI / 180], // North leans 25° to the right.
};
const canvas = document.querySelector('#mars');
const status = document.querySelector('#status');
const panel = document.querySelector('#interface');
const rotationButton = document.querySelector('#rotation');
const speedInput = document.querySelector('#speed');
const speedValue = document.querySelector('#speed-value');
const orbitSpeedInput = document.querySelector('#orbit-speed');
const orbitSpeedValue = document.querySelector('#orbit-speed-value');
const lightingSelect = document.querySelector('#lighting-mode');
const shadowControls = document.querySelector('#shadow-controls');
const shadowInput = document.querySelector('#shadow');
const shadowValue = document.querySelector('#shadow-value');
const cycleDetails = document.querySelector('#cycle-details');
const cyclePhase = document.querySelector('#cycle-phase');
const scaleSelect = document.querySelector('#moon-scale');
const scaleDescription = document.querySelector('#scale-description');
const focusStatus = document.querySelector('#focus-status');
const returnButton = document.querySelector('#return-mars');
const controls = [...document.querySelectorAll('button, input, select')];
const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)');
controls.forEach(control => { control.disabled = true; });

document.addEventListener('keydown', event => {
  if (event.ctrlKey && event.shiftKey && event.code === 'KeyR') {
    event.preventDefault();
    event.stopPropagation();
    if (event.repeat) return;
    panel.hidden = !panel.hidden;
    if (panel.hidden && panel.contains(document.activeElement)) canvas.focus({ preventScroll: true });
  }
}, { capture: true });
document.querySelector('#close-settings').addEventListener('click', () => {
  panel.hidden = true;
  canvas.focus({ preventScroll: true });
});

function showError(message) {
  status.textContent = message;
  status.hidden = false;
  document.querySelectorAll('button, input, select').forEach(control => { control.disabled = true; });
}

async function init() {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, powerPreference: 'high-performance' });
  let contextLost = false;
  canvas.addEventListener('webglcontextlost', event => {
    event.preventDefault();
    contextLost = true;
    renderer.setAnimationLoop(null);
    showError('The graphics connection was interrupted. Reload to restore Mars.');
  });
  renderer.setClearColor('#020305');
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = SETTINGS.exposure;
  const scene = new THREE.Scene();
  const camera = new THREE.OrthographicCamera(-3, 3, 2, -2, 0.1, 500);
  camera.position.set(0, 0, 8);
  const stars = createStars();
  scene.add(stars.points);
  const globe = new THREE.Group();
  const homeOrientation = new THREE.Quaternion().setFromEuler(new THREE.Euler(...SETTINGS.initialOrientation));
  scene.add(globe);
  const light = new THREE.DirectionalLight(0xffffff, SETTINGS.sunlight);
  scene.add(light, new THREE.AmbientLight(0xffffff, SETTINGS.fill));

  const base = import.meta.env.BASE_URL;
  const draco = new DRACOLoader().setDecoderPath(`${base}draco/`).setWorkerLimit(2);
  const loader = new GLTFLoader().setDRACOLoader(draco);
  let marsTexture, moonAssets;
  try {
    [marsTexture, ...moonAssets] = await Promise.all([
      new THREE.TextureLoader().loadAsync(`${base}textures/${renderer.capabilities.maxTextureSize >= 8192 ? 'mars-detail.jpg' : 'mars-detail-4k.jpg'}`),
      ...MOONS.map(moon => loader.loadAsync(`${base}models/${moon.name}.glb`)),
    ]);
  } finally {
    draco.dispose();
  }
  if (contextLost) return;
  marsTexture.colorSpace = THREE.SRGBColorSpace;
  marsTexture.anisotropy = renderer.capabilities.getMaxAnisotropy();
  const mars = new THREE.Mesh(
    new THREE.SphereGeometry(1, 128, 64),
    new THREE.MeshStandardMaterial({ map: marsTexture, roughness: 1, metalness: 0 }),
  );
  function keepNightVisible(material) {
    // Preserve at least 8% of the surface's linear texture color before tone
    // mapping. This reveals terrain at night without changing shadow coverage.
    material.onBeforeCompile = shader => {
      shader.uniforms.nightVisibility = { value: SETTINGS.nightVisibility };
      shader.fragmentShader = `uniform float nightVisibility;\n${shader.fragmentShader}`;
      shader.fragmentShader = shader.fragmentShader.replace(
        '#include <opaque_fragment>',
        'outgoingLight = max(outgoingLight, diffuseColor.rgb * nightVisibility);\n#include <opaque_fragment>',
      );
    };
    material.customProgramCacheKey = () => 'mars-night-visibility-v1';
  }
  keepNightVisible(mars.material);
  mars.userData.bodyId = 'mars';
  globe.add(mars);
  let scaleMode = 'illustrated';
  const moons = moonAssets.map((gltf, index) => {
    // Keep each irregular NASA-derived mesh together with its original UV texture.
    const model = gltf.scene;
    const bounds = new THREE.Box3().setFromObject(model);
    const center = bounds.getCenter(new THREE.Vector3());
    const diameter = Math.max(...bounds.getSize(new THREE.Vector3()).toArray());
    if (!Number.isFinite(diameter) || diameter <= 0) throw new Error('Invalid moon model bounds');
    const normalized = new THREE.Group();
    normalized.scale.setScalar(MOONS[index].diameter / diameter);
    model.position.sub(center);
    normalized.add(model);
    const body = new THREE.Group();
    body.userData.bodyId = MOONS[index].name;
    body.add(normalized);
    globe.add(body);
    model.traverse(object => {
      if (!object.isMesh) return;
      const materials = Array.isArray(object.material) ? object.material : [object.material];
      for (const material of materials) {
        material.roughness = 1;
        material.metalness = 0;
        keepNightVisible(material);
        if (material.map) material.map.anisotropy = renderer.capabilities.getMaxAnisotropy();
      }
    });
    return body;
  });
  let orbitTime = 0;
  function updateMoons() {
    moons.forEach((body, index) => {
      const display = moonDisplay(MOONS[index], scaleMode);
      body.scale.setScalar(display.diameter / MOONS[index].diameter);
      body.userData.displayDiameter = display.diameter;
      const pose = orbitPose(display, orbitTime);
      body.position.set(...pose.position);
      // The same local side always faces Mars, without assuming a mapped prime meridian.
      body.rotation.y = pose.rotationY;
    });
  }

  let zoom = 1;
  let speed = 1;
  let orbitSpeed = 1;
  let lightingMode = 'static';
  let shadowPercent = DEFAULT_SHADOW;
  let cycleTurns = 0;
  let rotating = !reducedMotion.matches;
  let starTime = 0;
  let lastTime = null;
  let focusedMoon = null;
  let overviewZoom = 1;
  let overviewPanelHidden = true;
  let explorer = null;
  let locationVisit = null;
  const pointers = new Map();
  const centeredMoonPosition = new THREE.Vector3();
  function updateView() {
    // Focus is a centered presentation: Mars stays at the origin and the
    // selected moon is displayed in front. Its orbital phase continues so the
    // physical overview can be restored without restarting the system.
    camera.position.set(0, 0, 8);
    if (focusedMoon) {
      globe.updateWorldMatrix(true, false);
      centeredMoonPosition.set(0, 0, 1.5);
      focusedMoon.position.copy(globe.worldToLocal(centeredMoonPosition));
      focusedMoon.scale.setScalar(1);
      focusedMoon.userData.displayDiameter = MOONS.find(moon => moon.name === focusedMoon.userData.bodyId).diameter;
    }
    camera.updateMatrixWorld();
    // Keep the star field fixed in screen space during zoom and moon tracking.
    stars.points.position.set(camera.position.x, camera.position.y, 0);
    stars.points.scale.set((camera.right - camera.left) / zoom, (camera.top - camera.bottom) / zoom, 1);
  }
  function focusBody(id) {
    cancelLocationVisit();
    if (id === 'mars') {
      if (focusedMoon) panel.hidden = overviewPanelHidden;
      focusedMoon = null;
      setZoom(overviewZoom);
    } else {
      const moon = moons.find(body => body.userData.bodyId === id);
      if (!moon) return;
      if (!focusedMoon) { overviewZoom = zoom; overviewPanelHidden = panel.hidden; }
      focusedMoon = moon;
      panel.hidden = true;
      explorer?.collapseNavigation();
      setZoom(SETTINGS.halfFrame * 0.95);
    }
    returnButton.hidden = !focusedMoon;
    focusStatus.hidden = !focusedMoon;
    focusStatus.textContent = focusedMoon ? `Centered on ${id === 'phobos' ? 'Phobos' : 'Deimos'} · moon enlarged for viewing` : '';
    updateMoons();
    updateView();
  }
  function showLocation(data) {
    const startZoom = focusedMoon ? overviewZoom : zoom;
    focusBody('mars');
    // Restore the same 25° north/south orientation used on load and reset.
    // Bring the longitude forward without tilting the latitude toward us.
    const target = new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 1, 0), -(data.lon + 90) * Math.PI / 180);
    locationVisit = {
      from: mars.quaternion.clone(), target, startZoom,
      globeFrom: globe.quaternion.clone(), globeTarget: homeOrientation.clone(),
      duration: reducedMotion.matches ? 0 : 1.2, elapsed: 0, remaining: 15,
    };
    setZoom(startZoom);
    if (reducedMotion.matches) { globe.quaternion.copy(homeOrientation); mars.quaternion.copy(target); setZoom(2); }
    panel.hidden = true;
    explorer.highlightLocation(data);
  }
  function cancelLocationVisit() {
    locationVisit = null;
    explorer?.clearLocation();
  }
  function interruptLocationTurn() {
    // Manual view controls take over the flight without ending the viewing hold.
    if (locationVisit) locationVisit.elapsed = locationVisit.duration;
  }
  function updateLocationVisit(seconds) {
    if (!locationVisit) return false;
    const visit = locationVisit;
    if (visit.elapsed < visit.duration) {
      const turning = Math.min(seconds, visit.duration - visit.elapsed);
      visit.elapsed += turning;
      seconds -= turning;
      const t = visit.elapsed / visit.duration;
      const eased = t * t * (3 - 2 * t);
      mars.quaternion.slerpQuaternions(visit.from, visit.target, eased);
      globe.quaternion.slerpQuaternions(visit.globeFrom, visit.globeTarget, eased);
      setZoom(THREE.MathUtils.lerp(visit.startZoom, 2, eased));
    }
    if (visit.elapsed < visit.duration) {
      explorer.setLocationStatus('Turning to location…');
    } else {
      visit.remaining = Math.max(0, visit.remaining - seconds);
      const willResume = rotating && speed > 0;
      explorer.setLocationStatus(visit.remaining > 0
        ? `${willResume ? 'Rotation resumes in' : 'Viewing location ·'} ${Math.ceil(visit.remaining)}s`
        : willResume ? 'Rotation resumed' : 'Rotation paused');
      if (visit.remaining === 0) locationVisit = null;
    }
    // Hold only Mars and its rotation-linked lighting; the moons keep orbiting.
    return true;
  }
  returnButton.addEventListener('click', () => focusBody('mars'));
  scaleSelect.addEventListener('change', () => {
    scaleMode = scaleSelect.value;
    updateMoons();
    overviewZoom = scaleMode === 'true' ? SETTINGS.halfFrame / 7.5 : 1;
    if (focusedMoon) focusBody(focusedMoon.userData.bodyId); else setZoom(overviewZoom);
    scaleDescription.textContent = scaleMode === 'true'
      ? 'True sizes and mean distances. Moon locators pulse every 5 seconds; click one to center it.'
      : 'Moon sizes enlarged and distances compressed for visibility.';
  });
  function updateLighting() {
    const state = getMarsLighting(lightingMode, cycleTurns, shadowPercent);
    light.position.set(...state.sun);
    light.intensity = SETTINGS.sunlight * state.sunlightStrength;
    if (lightingMode === 'cycle') {
      const text = `${state.phase} · Rotation ${state.phaseIndex + 1} of 4 · ${Math.round(state.shadowPercent)}% shadow`;
      if (cyclePhase.textContent !== text) cyclePhase.textContent = text;
    }
  }
  function updateLightingControls() {
    const cycling = lightingMode === 'cycle';
    shadowControls.hidden = cycling;
    cycleDetails.hidden = !cycling;
    shadowValue.value = `${shadowPercent}%`;
    updateLighting();
  }
  lightingSelect.addEventListener('change', () => {
    lightingMode = lightingSelect.value;
    cycleTurns = 0;
    updateLightingControls();
  });
  shadowInput.addEventListener('input', () => {
    shadowPercent = Number(shadowInput.value);
    updateLightingControls();
  });
  function resize() {
    const { width, height } = canvas.getBoundingClientRect();
    const aspect = width / Math.max(1, height);
    const halfHeight = systemHalfHeight(aspect, SETTINGS.halfFrame);
    renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
    renderer.setSize(width, height, false);
    camera.left = -halfHeight * aspect;
    camera.right = halfHeight * aspect;
    camera.top = halfHeight;
    camera.bottom = -halfHeight;
    camera.updateProjectionMatrix();
    updateView();
    stars.material.uniforms.pixelRatio.value = renderer.getPixelRatio();
  }
  function updateRotationButton() {
    rotationButton.textContent = rotating ? 'Pause animation' : 'Resume animation';
    rotationButton.setAttribute('aria-pressed', String(rotating));
  }
  function setZoom(value) {
    zoom = THREE.MathUtils.clamp(value, 0.15, 30);
    camera.zoom = zoom;
    camera.updateProjectionMatrix();
  }
  function reset() {
    cancelLocationVisit();
    focusedMoon = null;
    scaleMode = 'illustrated';
    overviewZoom = 1;
    scaleSelect.value = scaleMode;
    scaleDescription.textContent = 'Moon sizes enlarged and distances compressed for visibility.';
    returnButton.hidden = focusStatus.hidden = true;
    explorer?.reset();
    globe.quaternion.copy(homeOrientation);
    setZoom(1);
    mars.rotation.set(0, 0.65, 0);
    orbitTime = 0;
    updateMoons();
    starTime = 0;
    speed = 1;
    orbitSpeed = 1;
    lightingMode = 'static';
    shadowPercent = DEFAULT_SHADOW;
    cycleTurns = 0;
    lightingSelect.value = lightingMode;
    shadowInput.value = String(shadowPercent);
    updateLightingControls();
    orbitSpeedInput.value = '1';
    orbitSpeedValue.value = '1.00×';
    speedInput.value = '1';
    speedValue.value = '1.00×';
    rotating = !reducedMotion.matches;
    updateRotationButton();
    updateView();
  }
  speedInput.addEventListener('input', () => {
    speed = Number(speedInput.value);
    speedValue.value = `${speed.toFixed(2)}×`;
  });
  orbitSpeedInput.addEventListener('input', () => {
    orbitSpeed = Number(orbitSpeedInput.value);
    orbitSpeedValue.value = `${orbitSpeed.toFixed(2)}×`;
  });
  rotationButton.addEventListener('click', () => { rotating = !rotating; updateRotationButton(); });
  document.querySelector('#zoom-in').addEventListener('click', () => { interruptLocationTurn(); setZoom(zoom * 1.1); });
  document.querySelector('#zoom-out').addEventListener('click', () => { interruptLocationTurn(); setZoom(zoom / 1.1); });
  document.querySelector('#reset').addEventListener('click', reset);
  reducedMotion.addEventListener('change', () => { rotating = !reducedMotion.matches; updateRotationButton(); });
  canvas.addEventListener('keydown', event => {
    const rotations = { ArrowLeft: [0, -0.06], ArrowRight: [0, 0.06], ArrowUp: [-0.06, 0], ArrowDown: [0.06, 0] };
    if (rotations[event.key]) {
      interruptLocationTurn();
      event.preventDefault();
      const [x, y] = rotations[event.key];
      globe.rotateOnWorldAxis(new THREE.Vector3(0, 1, 0), y);
      globe.rotateOnWorldAxis(new THREE.Vector3(1, 0, 0), x);
    } else if (['+', '=', '-', '_'].includes(event.key)) {
      interruptLocationTurn();
      event.preventDefault();
      setZoom(zoom * (['+', '='].includes(event.key) ? 1.1 : 1 / 1.1));
    }
  });
  canvas.addEventListener('wheel', event => {
    interruptLocationTurn();
    event.preventDefault();
    const delta = event.deltaY * (event.deltaMode === 1 ? 16 : event.deltaMode === 2 ? innerHeight : 1);
    setZoom(zoom * Math.exp(-THREE.MathUtils.clamp(delta, -200, 200) * 0.001));
  }, { passive: false });
  const distance = () => {
    const [a, b] = [...pointers.values()];
    return a && b ? Math.hypot(a.x - b.x, a.y - b.y) : 0;
  };
  canvas.addEventListener('pointerdown', event => {
    if (event.button !== 0) return;
    canvas.focus({ preventScroll: true });
    canvas.setPointerCapture(event.pointerId);
    pointers.set(event.pointerId, { x: event.clientX, y: event.clientY });
  });
  canvas.addEventListener('pointermove', event => {
    const previous = pointers.get(event.pointerId);
    if (!previous) return;
    if (event.clientX !== previous.x || event.clientY !== previous.y) interruptLocationTurn();
    const oldDistance = distance();
    pointers.set(event.pointerId, { x: event.clientX, y: event.clientY });
    if (pointers.size === 2) {
      if (oldDistance > 0) setZoom(zoom * distance() / oldDistance);
    } else if (pointers.size === 1) {
      globe.rotateOnWorldAxis(new THREE.Vector3(0, 1, 0), (event.clientX - previous.x) * 0.005);
      globe.rotateOnWorldAxis(new THREE.Vector3(1, 0, 0), (event.clientY - previous.y) * 0.005);
    }
  });
  for (const name of ['pointerup', 'pointercancel', 'lostpointercapture']) {
    canvas.addEventListener(name, event => pointers.delete(event.pointerId));
  }
  document.addEventListener('visibilitychange', () => { lastTime = null; pointers.clear(); });
  window.addEventListener('blur', () => pointers.clear());
  explorer = createExplorer({
    canvas, camera, mars, moons, globe, focusBody, showLocation,
    onFactsChange: enabled => {
      document.querySelector('main').classList.toggle('exploring', enabled);
      if (enabled) panel.hidden = true;
      if (!enabled) cancelLocationVisit();
    },
  });
  const moonLocators = createMoonLocators({ canvas, camera, globe, moons, focusBody });
  reset();
  resize();
  new ResizeObserver(resize).observe(canvas);
  controls.forEach(control => { control.disabled = false; });
  status.hidden = true;
  renderer.setAnimationLoop(time => {
    if (document.hidden) { lastTime = null; return; }
    const visibleSeconds = lastTime === null ? 0 : Math.max(0, (time - lastTime) / 1000);
    const delta = Math.min(visibleSeconds, 0.1);
    lastTime = time;
    const viewingLocation = pointers.size === 0 && updateLocationVisit(visibleSeconds);
    if (rotating && pointers.size === 0) {
      const rotationStep = SETTINGS.rotationSpeed * speed * delta;
      if (!viewingLocation) mars.rotateY(rotationStep);
      if (!viewingLocation && lightingMode === 'cycle') {
        cycleTurns = advanceCycle(cycleTurns, rotationStep);
        updateLighting();
      }
      orbitTime += orbitSpeed * delta;
      updateMoons();
    }
    if (!reducedMotion.matches && rotating) starTime += delta;
    stars.material.uniforms.time.value = starTime;
    updateView();
    moonLocators.update(scaleMode === 'true', focusedMoon);
    explorer.update();
    renderer.render(scene, camera);
  });
}

init().catch(error => {
  console.error('Mars could not start:', error);
  showError('Mars could not load. Reload the page; if this persists, check that WebGL is enabled and the local textures, moon models, and decoder are available.');
});
