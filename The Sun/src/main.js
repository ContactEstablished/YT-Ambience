import * as THREE from 'three';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { createSun } from './sun.js';
import { createStars } from './stars.js';
import { advanceMotion } from './motion.js';

const canvas = document.querySelector('#sun');
const status = document.querySelector('#status');
const panel = document.querySelector('#interface');
const controls = [...document.querySelectorAll('button, input')];
const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)');
const settings = { rotation: 1, surfaceFlow: 1, sunspots: 1, flareActivity: 1, flares: 1, corona: 1 };
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

function init() {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: false, powerPreference: 'high-performance' });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 1.5));
  renderer.setClearColor(0x050201);
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.02;
  const scene = new THREE.Scene();
  const camera = new THREE.OrthographicCamera(-3,3,2,-2,.1,40);
  camera.position.z = 8;
  const sun = createSun();
  const composition = new THREE.Group();
  composition.add(sun.group, sun.corona);
  scene.add(composition);
  const initialOrientation = new THREE.Euler(.15,.4,-.12);
  sun.group.rotation.copy(initialOrientation);
  const stars = createStars();
  scene.add(stars);

  const composer = new EffectComposer(renderer);
  composer.addPass(new RenderPass(scene,camera));
  const bloom = new UnrealBloomPass(new THREE.Vector2(1,1),.23,.45,1.35);
  composer.addPass(bloom);
  composer.addPass(new OutputPass());

  let zoom = 1;
  function resize() {
    const width = Math.max(1,canvas.clientWidth), height = Math.max(1,canvas.clientHeight);
    const aspect = width/height;
    const halfHeight = 1.72 / Math.min(1,aspect);
    camera.left = -halfHeight*aspect; camera.right = halfHeight*aspect;
    camera.top = halfHeight; camera.bottom = -halfHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(width,height,false);
    composer.setSize(width,height);
    stars.scale.set(halfHeight*aspect*2,halfHeight*2,1);
    stars.material.uniforms.pixelRatio.value = renderer.getPixelRatio();
    sun.uniforms.pixelRatio.value = renderer.getPixelRatio();
    composition.scale.setScalar(zoom);
  }
  const observer = new ResizeObserver(resize);
  observer.observe(canvas);
  resize();

  for (const [id,key] of [['rotation-speed','rotation'],['surface-flow','surfaceFlow'],['sunspots','sunspots'],['flare-activity','flareActivity'],['flares','flares'],['corona','corona']]) {
    const slider = document.querySelector(`#${id}`);
    slider.addEventListener('input', () => {
      settings[key] = Number(slider.value);
      document.querySelector(`#${id}-value`).value = `${settings[key].toFixed(2)}×`;
    });
  }
  let paused = reducedMotion.matches;
  const pauseButton = document.querySelector('#pause');
  function updatePause() {
    pauseButton.textContent = paused ? 'Resume scene' : 'Pause scene';
    pauseButton.setAttribute('aria-pressed',String(paused));
    document.querySelector('#state-label').textContent = paused ? 'PAUSED' : 'LIVE';
  }
  pauseButton.addEventListener('click', () => { paused = !paused; updatePause(); });
  reducedMotion.addEventListener('change', event => { paused = event.matches; updatePause(); });
  document.querySelector('#stars').addEventListener('click', event => {
    stars.visible = !stars.visible;
    event.currentTarget.setAttribute('aria-pressed',String(stars.visible));
  });
  function changeZoom(factor) { zoom = THREE.MathUtils.clamp(zoom*factor,.55,1.35); resize(); }
  document.querySelector('#zoom-in').addEventListener('click', () => changeZoom(1.1));
  document.querySelector('#zoom-out').addEventListener('click', () => changeZoom(1/1.1));
  document.querySelector('#reset').addEventListener('click', () => {
    zoom = 1;
    sun.group.rotation.copy(initialOrientation);
    resize();
  });
  function rotate(x,y) {
    sun.group.quaternion.premultiply(new THREE.Quaternion().setFromEuler(new THREE.Euler(x,y,0)));
  }
  canvas.addEventListener('keydown', event => {
    const turns = { ArrowLeft: [0,-.06], ArrowRight: [0,.06], ArrowUp: [-.06,0], ArrowDown: [.06,0] };
    if (turns[event.key]) { event.preventDefault(); rotate(...turns[event.key]); }
    else if (['+','=','-'].includes(event.key)) { event.preventDefault(); changeZoom(event.key === '-' ? 1/1.1 : 1.1); }
  });
  const pointers = new Map();
  let pinchDistance = null;
  canvas.addEventListener('pointerdown', event => {
    if (event.button !== 0) return;
    canvas.setPointerCapture(event.pointerId);
    pointers.set(event.pointerId,{ x: event.clientX, y: event.clientY });
    pinchDistance = null;
  });
  canvas.addEventListener('pointermove', event => {
    const previous = pointers.get(event.pointerId);
    if (!previous) return;
    pointers.set(event.pointerId,{ x: event.clientX, y: event.clientY });
    if (pointers.size === 2) {
      const [a,b] = [...pointers.values()];
      const distance = Math.hypot(a.x-b.x,a.y-b.y);
      if (pinchDistance && distance > 0) changeZoom(distance/pinchDistance);
      pinchDistance = distance;
    } else rotate((event.clientY-previous.y)*.004,(event.clientX-previous.x)*.004);
  });
  const release = event => { pointers.delete(event.pointerId); pinchDistance = null; };
  for (const type of ['pointerup','pointercancel','lostpointercapture']) canvas.addEventListener(type,release);
  canvas.addEventListener('wheel', event => {
    event.preventDefault();
    changeZoom(Math.exp(-THREE.MathUtils.clamp(event.deltaY,-100,100)*.001));
  },{ passive: false });

  let previous = performance.now();
  function render(now) {
    const motion = advanceMotion({surfaceTime: sun.uniforms.time.value, flareTime: sun.uniforms.flareTime.value, coronaTime: sun.uniforms.coronaTime.value},(now-previous)/1000,settings,{ paused, dragging: pointers.size > 0 });
    previous = now;
    sun.uniforms.time.value = motion.surfaceTime;
    sun.uniforms.flareTime.value = motion.flareTime;
    sun.uniforms.coronaTime.value = motion.coronaTime;
    sun.group.rotateY(motion.rotationStep);
    sun.uniforms.sunspots.value = settings.sunspots;
    sun.uniforms.flareActivity.value = settings.flareActivity;
    sun.uniforms.flareStrength.value = settings.flares;
    sun.uniforms.coronaStrength.value = settings.corona;
    sun.update();
    composer.render();
  }
  let contextLost = false;
  document.addEventListener('visibilitychange', () => {
    previous = performance.now();
    renderer.setAnimationLoop(document.hidden || contextLost ? null : render);
  });
  canvas.addEventListener('webglcontextlost', event => {
    event.preventDefault();
    contextLost = true;
    renderer.setAnimationLoop(null);
    showError('The 3D view was interrupted. Reload the page to restore the Sun.');
  });
  updatePause();
  // Compile and render before hiding the loading message, including shader diagnostics.
  let shaderFailed = false;
  renderer.debug.onShaderError = (gl,program,vertex,fragment) => {
    shaderFailed = true;
    console.error('Sun shader failed:',gl.getProgramInfoLog(program),gl.getShaderInfoLog(vertex),gl.getShaderInfoLog(fragment));
  };
  composer.render();
  if (shaderFailed) throw new Error('A solar shader could not compile.');
  controls.forEach(control => { control.disabled = false; });
  status.hidden = true;
  renderer.setAnimationLoop(render);
}

try { init(); }
catch (error) {
  console.error('Sun scene could not start:',error);
  showError('The Sun could not load. Check that WebGL 2 is enabled, then reload the page.');
}
