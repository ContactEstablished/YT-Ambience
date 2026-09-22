import * as THREE from 'three';

export function createStars() {
  let seed = 9182;
  const random = () => { seed = (1664525*seed+1013904223) >>> 0; return seed/4294967296; };
  const positions = [], sizes = [], brightness = [];
  for (let i = 0; i < 2600; i++) {
    positions.push(random()-.5,random()-.5,-12);
    sizes.push(.6+random()**5*2.3);
    brightness.push(.06+random()**4*.66);
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));
  geometry.setAttribute('size',new THREE.Float32BufferAttribute(sizes,1));
  geometry.setAttribute('brightness',new THREE.Float32BufferAttribute(brightness,1));
  const material = new THREE.ShaderMaterial({
    uniforms: { pixelRatio: { value: 1 } },
    vertexShader: `
      uniform float pixelRatio; attribute float size; attribute float brightness; varying float light;
      void main() { light = brightness; gl_PointSize = size*pixelRatio;
        gl_Position = projectionMatrix*modelViewMatrix*vec4(position,1.0); }
    `,
    fragmentShader: `
      varying float light;
      void main() { float r = length(gl_PointCoord-.5); if (r>.5) discard;
        gl_FragColor = vec4(vec3(1.0,.74,.48)*light*(1.0-smoothstep(.0,.5,r)),1.0); }
    `,
    transparent: true, blending: THREE.AdditiveBlending, depthWrite: false,
  });
  return new THREE.Points(geometry,material);
}
