import * as THREE from 'three';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { createSun } from './sun.js';

// Real GPU regression sweep, separate from the ambience page and production build.
// Sample every pixel before/after bloom, including frames between flare lifecycles.
const result = document.querySelector('#result');
const still = new URLSearchParams(location.search).get('still');
const stillTime = still !== null && Number.isFinite(Number(still)) && Number(still)>=0 && Number(still)<=3600 ? Number(still) : null;
const width = stillTime === null ? 480 : 960, height = stillTime === null ? 270 : 540;
const renderer = new THREE.WebGLRenderer();
renderer.debug.onShaderError = (gl,program,vertex,fragment) => {
  throw new Error([gl.getProgramInfoLog(program),gl.getShaderInfoLog(vertex),gl.getShaderInfoLog(fragment)].join('\n'));
};
renderer.setSize(width,height);
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.02;
document.body.append(renderer.domElement);
const camera = new THREE.OrthographicCamera(-1.72*width/height,1.72*width/height,1.72,-1.72,.1,40);
camera.position.z = 8;
const scene = new THREE.Scene();
const sun = createSun({eruptionSeed: 73491});
scene.add(sun.group,sun.corona);
const composer = new EffectComposer(renderer);
const renderPass = new RenderPass(scene,camera);
const bloom = new UnrealBloomPass(new THREE.Vector2(width,height),.23,.45,1.35);
const output = new OutputPass();
composer.addPass(renderPass); composer.addPass(bloom); composer.addPass(output);
const pixels = new Uint16Array(width*height*4);
let frame = 0;
const report = { frames: 0, invalidSceneChannels: 0, invalidBloomChannels: 0, invalidFrames: [], maxBrightnessStep: 0 };
let previousBrightness;
function inspect(target) {
  renderer.readRenderTargetPixels(target,0,0,width,height,pixels);
  const glError = renderer.getContext().getError();
  if (glError !== 0) throw new Error(`GPU readback failed: ${glError}`);
  let invalid = 0, brightness = 0;
  for (let i=0;i<pixels.length;i++) {
    if ((pixels[i]&0x7c00)===0x7c00) invalid++;
    if (i%4!==3) brightness += THREE.DataUtils.fromHalfFloat(pixels[i]);
  }
  return { invalid, brightness: brightness/(width*height*3) };
}
function step() {
  try {
    const seconds = stillTime ?? frame/10;
    sun.uniforms.time.value = seconds*1.7;
    sun.uniforms.flareTime.value = seconds*1.7;
    sun.uniforms.coronaTime.value = seconds;
    sun.uniforms.flareActivity.value = 1.7;
    sun.group.rotation.set(.15,.4+seconds*.018*7.7,-.12);
    sun.update();
    renderPass.render(renderer,composer.writeBuffer,composer.readBuffer);
    const raw = inspect(composer.readBuffer);
    bloom.render(renderer,composer.writeBuffer,composer.readBuffer);
    const glow = inspect(composer.readBuffer);
    output.renderToScreen = true;
    output.render(renderer,composer.writeBuffer,composer.readBuffer);
    report.invalidSceneChannels += raw.invalid;
    report.invalidBloomChannels += glow.invalid;
    if (raw.invalid || glow.invalid) report.invalidFrames.push(frame);
    if (Number.isFinite(previousBrightness) && Number.isFinite(glow.brightness)) {
      report.maxBrightnessStep = Math.max(report.maxBrightnessStep,Math.abs(glow.brightness-previousBrightness));
    }
    previousBrightness = glow.brightness;
    report.frames = ++frame;
    result.textContent = JSON.stringify(report,null,2);
    if (stillTime === null && frame<600) requestAnimationFrame(step);
    else result.textContent = `${report.invalidSceneChannels || report.invalidBloomChannels ? 'FAIL' : 'PASS'}\n${JSON.stringify(report,null,2)}`;
  } catch(error) { result.textContent = `FAIL: ${error.stack}`; }
}
requestAnimationFrame(step);
