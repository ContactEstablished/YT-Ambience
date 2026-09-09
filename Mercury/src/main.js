import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { createStars } from './stars.js';

const SETTINGS = {
  rotationSpeed: 0.012, // One turn in about 8 minutes 44 seconds at 1×.
  exposure: 1.08,
  sunlight: 3.2,
  fill: 0.025,
  daylightFraction: 0.8,
  halfFrame: 1.65,
  initialOrientation: [0.08, 0.65, -0.025],
};
const canvas = document.querySelector('#mercury');
const status = document.querySelector('#status');
const panel = document.querySelector('#interface');
const rotationButton = document.querySelector('#rotation');
const speedInput = document.querySelector('#speed');
const speedValue = document.querySelector('#speed-value');
const controls = [...document.querySelectorAll('button, input')];
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

function showError(message) {
  status.textContent = message;
  status.hidden = false;
  controls.forEach(control => { control.disabled = true; });
}

async function init() {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, powerPreference: 'high-performance' });
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
  scene.add(globe);
  const light = new THREE.DirectionalLight(0xffffff, SETTINGS.sunlight);
  const sunZ = SETTINGS.daylightFraction * 2 - 1;
  const sunXY = Math.sqrt(1 - sunZ * sunZ);
  light.position.set(-sunXY * 0.8, sunXY * 0.6, sunZ);
  scene.add(light, new THREE.AmbientLight(0xffffff, SETTINGS.fill));

  // Retain NASA's geometry and UV atlas together; the texture is not a lat/long map.
  const gltf = await new GLTFLoader().loadAsync(`${import.meta.env.BASE_URL}models/mercury.glb`);
  const model = gltf.scene;
  const bounds = new THREE.Box3().setFromObject(model);
  const center = bounds.getCenter(new THREE.Vector3());
  const diameter = Math.max(...bounds.getSize(new THREE.Vector3()).toArray());
  if (!Number.isFinite(diameter) || diameter <= 0) throw new Error('Invalid model bounds');
  const normalized = new THREE.Group();
  normalized.scale.setScalar(2 / diameter);
  model.position.sub(center);
  normalized.add(model);
  globe.add(normalized);
  model.traverse(object => {
    if (!object.isMesh) return;
    const materials = Array.isArray(object.material) ? object.material : [object.material];
    for (const material of materials) {
      if (material.map) material.map.anisotropy = renderer.capabilities.getMaxAnisotropy();
    }
  });

  let zoom = 1;
  let speed = 1;
  let rotating = !reducedMotion.matches;
  let starTime = 0;
  let lastTime = null;
  const pointers = new Map();
  function resize() {
    const { width, height } = canvas.getBoundingClientRect();
    const aspect = width / Math.max(1, height);
    const halfHeight = SETTINGS.halfFrame / Math.min(1, aspect);
    renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
    renderer.setSize(width, height, false);
    camera.left = -halfHeight * aspect;
    camera.right = halfHeight * aspect;
    camera.top = halfHeight;
    camera.bottom = -halfHeight;
    camera.updateProjectionMatrix();
    stars.points.scale.set(halfHeight * aspect * 2, halfHeight * 2, 1);
    stars.material.uniforms.pixelRatio.value = renderer.getPixelRatio();
  }
  function updateRotationButton() {
    rotationButton.textContent = rotating ? 'Pause rotation' : 'Resume rotation';
    rotationButton.setAttribute('aria-pressed', String(rotating));
  }
  function setZoom(value) {
    zoom = THREE.MathUtils.clamp(value, 0.55, 1.45);
    globe.scale.setScalar(zoom);
  }
  function reset() {
    globe.rotation.set(...SETTINGS.initialOrientation);
    setZoom(1);
    speed = 1;
    speedInput.value = '1';
    speedValue.value = '1.00×';
    rotating = !reducedMotion.matches;
    updateRotationButton();
  }
  speedInput.addEventListener('input', () => {
    speed = Number(speedInput.value);
    speedValue.value = `${speed.toFixed(2)}×`;
  });
  rotationButton.addEventListener('click', () => { rotating = !rotating; updateRotationButton(); });
  document.querySelector('#zoom-in').addEventListener('click', () => setZoom(zoom * 1.1));
  document.querySelector('#zoom-out').addEventListener('click', () => setZoom(zoom / 1.1));
  document.querySelector('#reset').addEventListener('click', reset);
  reducedMotion.addEventListener('change', () => { rotating = !reducedMotion.matches; updateRotationButton(); });
  canvas.addEventListener('keydown', event => {
    const rotations = { ArrowLeft: [0, -0.06], ArrowRight: [0, 0.06], ArrowUp: [-0.06, 0], ArrowDown: [0.06, 0] };
    if (rotations[event.key]) {
      event.preventDefault();
      const [x, y] = rotations[event.key];
      globe.rotateOnWorldAxis(new THREE.Vector3(0, 1, 0), y);
      globe.rotateOnWorldAxis(new THREE.Vector3(1, 0, 0), x);
    } else if (['+', '=', '-', '_'].includes(event.key)) {
      event.preventDefault();
      setZoom(zoom * (['+', '='].includes(event.key) ? 1.1 : 1 / 1.1));
    }
  });
  canvas.addEventListener('wheel', event => {
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
  canvas.addEventListener('webglcontextlost', event => {
    event.preventDefault();
    renderer.setAnimationLoop(null);
    showError('The graphics connection was interrupted. Reload to restore Mercury.');
  });
  reset();
  resize();
  new ResizeObserver(resize).observe(canvas.parentElement);
  controls.forEach(control => { control.disabled = false; });
  status.hidden = true;
  renderer.setAnimationLoop(time => {
    if (document.hidden) { lastTime = null; return; }
    const delta = lastTime === null ? 0 : Math.min((time - lastTime) / 1000, 0.1);
    lastTime = time;
    if (rotating && pointers.size === 0) globe.rotateY(SETTINGS.rotationSpeed * speed * delta);
    if (!reducedMotion.matches && rotating) starTime += delta;
    stars.material.uniforms.time.value = starTime;
    renderer.render(scene, camera);
  });
}

init().catch(error => {
  console.error('Mercury could not start:', error);
  showError('Mercury could not load. Reload the page; if this persists, check that WebGL is enabled and the local model is available.');
});
