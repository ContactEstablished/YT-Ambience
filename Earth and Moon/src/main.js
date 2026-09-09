import * as THREE from 'three';
import { createMoon, LUNAR_SHADOW_DIRECTION } from './moon.js';
import { createStars } from './stars.js';
import { advanceCycle, getEarthLighting } from './earth-lighting.js';

// The small set of art-direction values to change in our next design pass.
const SETTINGS = {
  radius: 2.55,
  rotationSpeed: 0.018, // radians per second
  cloudDriftSpeed: 0.004,
  cloudOpacity: 0.84,
  bumpScale: 0.012,
  exposure: 1.12,
  // Orthographic illuminated fraction = (1 + sunDirection.z) / 2 = 80%.
  daylightFraction: 0.8,
  moonRotationSpeed: 0.002, // one seamless revolution in about 52 minutes
  earthScale: 1.20,
  initialLatitude: 17,
  initialLongitude: 52,
  background: '#020305',
};

const canvas = document.querySelector('#earth');
const status = document.querySelector('#status');
const rotationButton = document.querySelector('#rotation');
const cloudButton = document.querySelector('#clouds');
const interfacePanel = document.querySelector('#interface');
const buttons = [...document.querySelectorAll('button, input, select')];
const lightingSelect = document.querySelector('#lighting-mode');
const phaseDisplay = document.querySelector('#cycle-phase');
const cycleDescription = document.querySelector('#cycle-description');
const speeds = { earth: 1, moon: 1 };
for (const body of ['earth', 'moon']) {
  const slider = document.querySelector(`#${body}-speed`);
  slider.addEventListener('input', () => {
    speeds[body] = Number(slider.value);
    document.querySelector(`#${body}-speed-value`).value = `${speeds[body].toFixed(2)}×`;
  });
}
// Capture the shortcut before the browser's default hard-reload action.
document.addEventListener('keydown', event => {
  if (event.ctrlKey && event.shiftKey && event.code === 'KeyR') {
    event.preventDefault();
    event.stopPropagation();
    if (event.repeat) return;
    interfacePanel.hidden = !interfacePanel.hidden;
    if (interfacePanel.hidden && interfacePanel.contains(document.activeElement)) canvas.focus({ preventScroll: true });
  }
}, { capture: true });
buttons.forEach(button => { button.disabled = true; });
const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)');
let rotating = !reducedMotion.matches;

function showError(message) {
  status.textContent = message;
  status.hidden = false;
  buttons.forEach(button => { button.disabled = true; });
}

async function init() {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, powerPreference: 'high-performance' });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 1.75));
  renderer.setClearColor(SETTINGS.background);
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = SETTINGS.exposure;
  const scene = new THREE.Scene();
  const stars = createStars();
  scene.add(stars.points);
  // Fixed composition: interaction changes Earth, never the lunar horizon.
  const camera = new THREE.OrthographicCamera(-15, 15, 10, -10, 0.1, 500);
  camera.position.set(0, 0, 30);
  camera.layers.enable(1);
  let earthZoom = 1;
  let lightingMode = 'default';
  let cycleTurns = 0;
  let viewportAspect = 1;
  let previousPhaseText = '';
  const cycleAppearance = { value: 0 };
  const atmosphereStrength = { value: 1 };

  const globe = new THREE.Group();
  scene.add(globe);
  const initialOrientation = new THREE.Quaternion().setFromEuler(new THREE.Euler(
    THREE.MathUtils.degToRad(SETTINGS.initialLatitude),
    -THREE.MathUtils.degToRad(SETTINGS.initialLongitude) - Math.PI / 2,
    0,
    'XYZ',
  ));
  globe.quaternion.copy(initialOrientation);

  const sunDirection = new THREE.Vector3(0, 0.8, 0.6);
  const sunUniform = { value: sunDirection };
  const sun = new THREE.DirectionalLight(0xfff4e5, 3.1);
  sun.position.copy(sunDirection).multiplyScalar(20);
  scene.add(sun, new THREE.AmbientLight(0x7295bf, 0.025));

  const { moon, textures: moonTextures } = createMoon();
  moon.layers.set(1);
  scene.add(moon);
  const moonSun = new THREE.DirectionalLight(0xffffff, 2.8);
  moonSun.position.set(-45, 16, 25);
  moonSun.layers.set(1);
  const moonFill = new THREE.AmbientLight(0xffffff, 0.10);
  moonFill.layers.set(1);
  scene.add(moonSun, moonFill);

  const loader = new THREE.TextureLoader();
  const maxAnisotropy = Math.min(8, renderer.capabilities.getMaxAnisotropy());
  moonTextures.forEach(map => { map.anisotropy = maxAnisotropy; });
  async function texture(file, color = true) {
    const result = await loader.loadAsync(`${import.meta.env.BASE_URL}textures/${file}`);
    if (color) result.colorSpace = THREE.SRGBColorSpace;
    result.anisotropy = maxAnisotropy;
    return result;
  }
  const [day, night, bump, water, cloudMap] = await Promise.all([
    texture('earth.jpg'), texture('earth-night.jpg'), texture('earth-bump.jpg', false),
    texture('earth-water.png', false), texture('clouds.png'),
  ]);

  const surface = new THREE.MeshPhongMaterial({
    map: day, bumpMap: bump, bumpScale: SETTINGS.bumpScale,
    specularMap: water, specular: new THREE.Color(0x425d76), shininess: 28,
    emissiveMap: night, emissive: new THREE.Color(0xffffff), emissiveIntensity: 0.2,
  });
  // Keep city lights on the unlit hemisphere as the globe moves through sunlight.
  surface.onBeforeCompile = shader => {
    shader.uniforms.sunDirection = sunUniform;
    shader.uniforms.cycleAppearance = cycleAppearance;
    shader.vertexShader = 'varying vec3 vWorldNormal;\n' + shader.vertexShader;
    shader.vertexShader = shader.vertexShader.replace('#include <begin_vertex>', `
      #include <begin_vertex>
      vWorldNormal = normalize(mat3(modelMatrix) * normal);
    `);
    shader.fragmentShader = 'uniform vec3 sunDirection; uniform float cycleAppearance; varying vec3 vWorldNormal;\n' + shader.fragmentShader;
    shader.fragmentShader = shader.fragmentShader.replace('#include <emissivemap_fragment>', `
      #include <emissivemap_fragment>
      float darkness = 1.0 - smoothstep(-0.20, 0.15, dot(normalize(vWorldNormal), sunDirection));
      float cities = max(totalEmissiveRadiance.r - totalEmissiveRadiance.b, 0.0);
      vec3 defaultNight = vec3(1.0, 0.65, 0.30) * cities;
      float landMask = 1.0 - texture2D(specularMap, vSpecularMapUv).r;
      // Recover faint/whiter settlements in the existing geographic light map.
      // Keep the ocean dark; the lower exponent brings smaller cities into view.
      float cycleCities = max(totalEmissiveRadiance.r - totalEmissiveRadiance.b * 0.85, 0.0) * landMask;
      float terrainLuminance = dot(diffuseColor.rgb, vec3(0.2126, 0.7152, 0.0722));
      vec3 faintTerrain = mix(diffuseColor.rgb, vec3(terrainLuminance), 0.25) * vec3(0.018, 0.026, 0.042);
      // Two successive 5% increases: 1.05 * 1.05 = 1.1025 on land.
      faintTerrain *= 1.0 + 0.1025 * landMask;
      vec3 cycleNight = vec3(1.0, 0.68, 0.34) * pow(cycleCities, 0.65) * 9.5 + faintTerrain;
      totalEmissiveRadiance = mix(defaultNight, cycleNight, cycleAppearance) * darkness;
    `);
  };
  globe.add(new THREE.Mesh(new THREE.SphereGeometry(SETTINGS.radius, 160, 100), surface));

  const clouds = new THREE.Mesh(
    new THREE.SphereGeometry(SETTINGS.radius + 0.013, 128, 80),
    new THREE.MeshPhongMaterial({
      map: cloudMap, transparent: true, opacity: SETTINGS.cloudOpacity, depthWrite: false,
      shininess: 3, emissiveMap: cloudMap, emissive: new THREE.Color(0x14263b), emissiveIntensity: 0.3,
    }),
  );
  globe.add(clouds);

  // Two thin shells give the limb its blue scattering without a screen-space halo.
  function atmosphere(radius, outer) {
    return new THREE.Mesh(new THREE.SphereGeometry(radius, 100, 64), new THREE.ShaderMaterial({
      uniforms: { sunDirection: sunUniform, strength: { value: outer ? 0.30 : 0.55 }, atmosphereStrength },
      vertexShader: `
        varying vec3 vNormalWorld;
        varying vec3 vPositionWorld;
        void main() {
          vNormalWorld = normalize(mat3(modelMatrix) * normal);
          vPositionWorld = (modelMatrix * vec4(position, 1.0)).xyz;
          gl_Position = projectionMatrix * viewMatrix * vec4(vPositionWorld, 1.0);
        }
      `,
      fragmentShader: `
        uniform vec3 sunDirection;
        uniform float strength;
        uniform float atmosphereStrength;
        varying vec3 vNormalWorld;
        varying vec3 vPositionWorld;
        void main() {
          vec3 normal = normalize(vNormalWorld);
          vec3 view = normalize(cameraPosition - vPositionWorld);
          float edge = pow(1.0 - abs(dot(normal, view)), 5.0);
          float illumination = smoothstep(-0.4, 0.8, dot(normal, sunDirection));
          vec3 blue = mix(vec3(0.035, 0.11, 0.28), vec3(0.12, 0.46, 1.0), illumination);
          gl_FragColor = vec4(blue, edge * strength * atmosphereStrength * (0.35 + 0.65 * illumination));
        }
      `,
      side: outer ? THREE.BackSide : THREE.FrontSide,
      blending: THREE.AdditiveBlending, transparent: true, depthWrite: false,
    }));
  }
  globe.add(atmosphere(SETTINGS.radius + 0.032, false), atmosphere(SETTINGS.radius + 0.075, true));

  function updateLighting() {
    const state = getEarthLighting(lightingMode, cycleTurns, viewportAspect, LUNAR_SHADOW_DIRECTION, SETTINGS.daylightFraction);
    sunDirection.set(...state.sun);
    sun.position.copy(sunDirection).multiplyScalar(20);
    const cycling = lightingMode === 'cycle';
    cycleAppearance.value = cycling ? 1 : 0;
    clouds.material.emissiveIntensity = cycling ? 0.035 + 0.265 * state.daylight : 0.3;
    atmosphereStrength.value = cycling ? 0.35 + 0.65 * state.daylight : 1;
    const phaseText = `${state.phase} · Rotation ${state.phaseIndex + 1} of 4 · ${Math.floor(state.progress * 100)}%`;
    if (cycling && phaseText !== previousPhaseText) {
      phaseDisplay.textContent = phaseText;
      previousPhaseText = phaseText;
    }
  }
  lightingSelect.addEventListener('change', () => {
    lightingMode = lightingSelect.value;
    cycleTurns = 0;
    phaseDisplay.hidden = cycleDescription.hidden = lightingMode !== 'cycle';
    updateLighting();
  });

  function resize() {
    const width = canvas.clientWidth, height = canvas.clientHeight;
    const aspect = width / height;
    viewportAspect = aspect;
    updateLighting();
    const halfHeight = 10;
    const halfWidth = halfHeight * aspect;
    camera.left = -halfWidth;
    camera.right = halfWidth;
    camera.top = halfHeight;
    camera.bottom = -halfHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(width, height, false);
    stars.points.scale.set(halfWidth * 2, halfHeight * 2, 1);
    stars.material.uniforms.pixelRatio.value = renderer.getPixelRatio();
    // Horizon rises toward the right, matching the reference photograph.
    const radius = Math.max(26, halfWidth * 3);
    moon.scale.setScalar(radius);
    moon.position.set(halfWidth * 0.96, 1.65 - radius, -radius - 5);
    globe.position.set(-halfWidth * 0.15, 4.35, -180);
    globe.scale.setScalar(SETTINGS.earthScale * earthZoom * Math.min(1, aspect / 0.85));
  }
  resize();
  const observer = new ResizeObserver(resize);
  observer.observe(canvas);

  function updateRotationButton() {
    rotationButton.textContent = rotating ? 'Pause rotation' : 'Resume rotation';
    rotationButton.setAttribute('aria-pressed', String(rotating));
  }
  rotationButton.addEventListener('click', () => { rotating = !rotating; updateRotationButton(); });
  cloudButton.addEventListener('click', () => {
    clouds.visible = !clouds.visible;
    cloudButton.setAttribute('aria-pressed', String(clouds.visible));
  });
  function zoom(factor) {
    earthZoom = THREE.MathUtils.clamp(earthZoom / factor, 0.55, 1.5);
    resize();
  }
  document.querySelector('#zoom-in').addEventListener('click', () => zoom(0.88));
  document.querySelector('#zoom-out').addEventListener('click', () => zoom(1 / 0.88));
  document.querySelector('#reset').addEventListener('click', () => {
    earthZoom = 1;
    moon.rotation.set(0.22, 0.3, -0.15);
    globe.quaternion.copy(initialOrientation);
    clouds.rotation.y = 0;
    cycleTurns = 0;
    resize();
  });
  canvas.addEventListener('keydown', event => {
    const rotations = { ArrowLeft: [0, -0.06], ArrowRight: [0, 0.06], ArrowUp: [-0.06, 0], ArrowDown: [0.06, 0] };
    if (rotations[event.key]) {
      event.preventDefault();
      const [x, y] = rotations[event.key];
      globe.quaternion.premultiply(new THREE.Quaternion().setFromEuler(new THREE.Euler(x, y, 0)));
    } else if (['+', '=', '-'].includes(event.key)) {
      event.preventDefault();
      zoom(event.key === '-' ? 1 / 0.88 : 0.88);
    }
  });
  reducedMotion.addEventListener('change', event => { rotating = !event.matches; updateRotationButton(); });
  const pointers = new Map();
  let pinchDistance = null;
  canvas.addEventListener('pointerdown', event => {
    if (event.button !== 0) return;
    canvas.setPointerCapture(event.pointerId);
    pointers.set(event.pointerId, { x: event.clientX, y: event.clientY });
    pinchDistance = null;
  });
  canvas.addEventListener('pointermove', event => {
    const previous = pointers.get(event.pointerId);
    if (!previous) return;
    pointers.set(event.pointerId, { x: event.clientX, y: event.clientY });
    if (pointers.size === 2) {
      const [a, b] = [...pointers.values()];
      const distance = Math.hypot(a.x - b.x, a.y - b.y);
      if (pinchDistance && distance > 0) zoom(pinchDistance / distance);
      pinchDistance = distance;
    } else {
      globe.quaternion.premultiply(new THREE.Quaternion().setFromEuler(new THREE.Euler(
        (event.clientY - previous.y) * 0.004,
        (event.clientX - previous.x) * 0.004, 0,
      )));
    }
  });
  const releasePointer = event => { pointers.delete(event.pointerId); pinchDistance = null; };
  canvas.addEventListener('pointerup', releasePointer);
  canvas.addEventListener('pointercancel', releasePointer);
  canvas.addEventListener('lostpointercapture', releasePointer);
  canvas.addEventListener('wheel', event => {
    event.preventDefault();
    zoom(Math.exp(THREE.MathUtils.clamp(event.deltaY, -100, 100) * 0.001));
  }, { passive: false });
  let previous = performance.now();
  let starTime = 0;
  function render(now) {
    const delta = Math.min((now - previous) / 1000, 0.05);
    previous = now;
    if (rotating) {
      moon.rotation.y = (moon.rotation.y + SETTINGS.moonRotationSpeed * speeds.moon * delta) % (Math.PI * 2);
    }
    if (rotating && pointers.size === 0) {
      const rotationStep = SETTINGS.rotationSpeed * speeds.earth * delta;
      globe.rotateY(rotationStep);
      clouds.rotation.y += SETTINGS.cloudDriftSpeed * speeds.earth * delta;
      if (lightingMode === 'cycle') {
        cycleTurns = advanceCycle(cycleTurns, rotationStep);
        updateLighting();
      }
    }
    if (!reducedMotion.matches) starTime += delta;
    stars.material.uniforms.time.value = starTime;
    // Light layers are camera-scoped in Three.js, so render separate passes.
    // Keep the depth buffer between passes for correct foreground occlusion.
    renderer.autoClear = false;
    renderer.clear();
    camera.layers.set(0);
    renderer.render(scene, camera);
    camera.layers.set(1);
    renderer.render(scene, camera);
  }
  document.addEventListener('visibilitychange', () => {
    previous = performance.now();
    renderer.setAnimationLoop(document.hidden ? null : render);
  });
  canvas.addEventListener('webglcontextlost', event => {
    event.preventDefault();
    renderer.setAnimationLoop(null);
    showError('The 3D view was interrupted. Reload the page to restore the scene.');
  });
  renderer.setAnimationLoop(render);
  updateRotationButton();
  buttons.forEach(button => { button.disabled = false; });
  status.hidden = true;
}

init().catch(error => {
  console.error('Scene could not start:', error);
  showError('The scene could not load. Check that WebGL is enabled and reload the page.');
});
