import * as THREE from 'three';

export function createStars() {
  let seed = 7021;
  const random = () => { seed = (1664525 * seed + 1013904223) >>> 0; return seed / 4294967296; };
  const positions = [], sizes = [], brightness = [], phases = [], rates = [], amounts = [];
  for (let i = 0; i < 1100; i++) {
    positions.push(random() - 0.5, random() - 0.5, -300);
    const prominence = random() ** 3;
    sizes.push(1.0 + prominence * 1.5);
    brightness.push(0.16 + prominence * 0.48);
    phases.push(random() * Math.PI * 2);
    rates.push(2 * Math.PI / (8 + random() * 10));
    amounts.push(random() < 0.18 ? 0.08 + random() * 0.08 : 0);
  }
  const geometry = new THREE.BufferGeometry();
  for (const [name, values, size] of [
    ['position', positions, 3], ['starSize', sizes, 1], ['brightness', brightness, 1],
    ['phase', phases, 1], ['rate', rates, 1], ['twinkle', amounts, 1],
  ]) geometry.setAttribute(name, new THREE.Float32BufferAttribute(values, size));
  const material = new THREE.ShaderMaterial({
    uniforms: { time: { value: 0 }, pixelRatio: { value: 1 } },
    vertexShader: `
      uniform float time;
      uniform float pixelRatio;
      attribute float starSize;
      attribute float brightness;
      attribute float phase;
      attribute float rate;
      attribute float twinkle;
      varying float light;
      void main() {
        light = brightness * (1.0 + twinkle * sin(time * rate + phase));
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        gl_PointSize = starSize * pixelRatio;
      }
    `,
    fragmentShader: `
      varying float light;
      void main() {
        float radius = length(gl_PointCoord - 0.5);
        if (radius > 0.5) discard;
        float softness = 1.0 - smoothstep(0.05, 0.5, radius);
        gl_FragColor = vec4(vec3(0.88, 0.93, 1.0), light * softness);
      }
    `,
    transparent: true, depthWrite: false, depthTest: true,
  });
  return { points: new THREE.Points(geometry, material), material };
}
