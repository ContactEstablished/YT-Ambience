import * as THREE from 'three';

// Screen-space beacons reveal real-scale moons without enlarging their meshes.
// They remain available with the facts explorer turned off.
export function createMoonLocators({ canvas, camera, globe, moons, focusBody }) {
  const layer = document.querySelector('#moon-locators');
  const point = new THREE.Vector3();
  const markers = moons.map(body => {
    const name = body.userData.bodyId;
    const title = name === 'phobos' ? 'Phobos' : 'Deimos';
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'moon-locator';
    button.dataset.moon = name;
    button.setAttribute('aria-label', `Center ${title} in front of Mars`);
    button.title = `${title} — click to center`;
    const label = document.createElement('span');
    label.className = 'moon-locator-label';
    label.textContent = title;
    button.append(label);
    button.addEventListener('click', () => focusBody(name));
    layer.append(button);
    return { body, button };
  });
  function update(enabled, focusedMoon) {
    layer.hidden = !enabled;
    if (!enabled) return;
    globe.updateWorldMatrix(true, true);
    const rect = canvas.getBoundingClientRect();
    for (const { body, button } of markers) {
      body.getWorldPosition(point);
      point.project(camera);
      const x = (point.x + 1) * rect.width / 2;
      const y = (1 - point.y) * rect.height / 2;
      button.hidden = body === focusedMoon || point.z < -1 || point.z > 1
        || x < 22 || y < 22 || x > rect.width - 22 || y > rect.height - 22;
      if (button.hidden) continue;
      button.style.transform = `translate(${x}px, ${y}px) translate(-50%, -50%)`;
    }
  }
  return { update };
}
