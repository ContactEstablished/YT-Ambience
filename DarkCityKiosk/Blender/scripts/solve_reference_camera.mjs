#!/usr/bin/env node
// Estimates the camera of _reference/PrimaryReference.png (1672x941) and the
// kiosk's real-world dimensions from pixel measurements.
//
// Method: the kiosk's horizontal edges converge on two vanishing points
// (front face -> right, left face -> left). With no roll, both sit on the
// horizon; orthogonality of the two face directions gives the focal length,
// the horizon's offset from the image centre gives the camera pitch, and the
// VP positions give the yaw of each face. Scale comes from one assumption:
// the side door is DOOR_HEIGHT_M tall. Everything else is solved by
// intersecting pixel rays with the two wall planes.
//
//   node solve_reference_camera.mjs            prints the camera + dimensions
//   node solve_reference_camera.mjs --json f   also writes them to file f

import fs from 'node:fs';

const W = 1672, H = 941;
const PX = W / 2, PY = H / 2;
const DOOR_HEIGHT_M = 2.0;

// ---- Measurements (image pixels, read off grid crops) ----
// Front-face edges, each as two points. All should meet at VP_R.
const frontLines = {
  canopyTop: [[655, 392], [1000, 505]],
  counterEdge: [[645, 680], [895, 705]],
  platformTop: [[600, 797], [1050, 802]],
};
// Left-face edges. All should meet at VP_L.
const leftLines = {
  canopyTop: [[302, 460], [630, 387]],
  canopyBottom: [[302, 512], [610, 455]],
};
const m = {
  cornerBase: [648, 800], // front-left body corner where it meets the platform
  doorBottom: [473, 790], // side door, centre of the sill
  doorTop: [473, 532], // side door, centre of the head
  // Points on the LEFT wall plane: [x, y] at a known feature
  leftWallEnd: [367, 790], // back-left body corner, at the platform
  leftLantern: [340, 600], // ramen lantern centre (sits just off the wall)
  // Points on the FRONT wall plane
  frontWallEnd: [967, 798], // front-right body corner, at the platform
  serviceWinLeft: [712, 640],
  serviceWinRight: [820, 650],
  serviceWinTop: [766, 575],
  counterTopFront: [700, 684], // counter lip (projects off the wall)
  glazedWinLeft: [872, 680],
  glazedWinRight: [950, 690],
  glazedWinTop: [911, 623],
  glazedWinBottom: [911, 740],
  // Canopy (yellow lightbox) at the corner and the ends
  canopyCornerTop: [648, 388],
  canopyCornerBottom: [648, 454],
  canopyFrontEndTop: [1000, 503],
  canopyFrontEndBottom: [1000, 560],
  canopyLeftEndTop: [302, 460],
  canopyLeftEndBottom: [302, 512],
  // Roof clutter tops (above the corner region)
  roofTallestBox: [580, 285],
  roofTanks: [730, 320],
  roofMastTop: [893, 315],
};

// ---- Geometry helpers ----
const sub = (a, b) => [a[0] - b[0], a[1] - b[1]];
function intersect([p1, p2], [p3, p4]) {
  const d1 = sub(p2, p1), d2 = sub(p4, p3);
  const den = d1[0] * d2[1] - d1[1] * d2[0];
  const t = ((p3[0] - p1[0]) * d2[1] - (p3[1] - p1[1]) * d2[0]) / den;
  return [p1[0] + t * d1[0], p1[1] + t * d1[1]];
}
function meanVP(lines) {
  const ls = Object.values(lines), pts = [];
  for (let i = 0; i < ls.length; i++) for (let j = i + 1; j < ls.length; j++) pts.push(intersect(ls[i], ls[j]));
  return [pts.reduce((s, p) => s + p[0], 0) / pts.length, pts.reduce((s, p) => s + p[1], 0) / pts.length, pts];
}

// ---- Vanishing points -> intrinsics + orientation ----
const [vrx, vry, vrAll] = meanVP(frontLines);
const [vlx, vly, vlAll] = meanVP(leftLines);
// Force a shared horizon (no roll): weight the front VP more (3 lines, one
// nearly on the horizon) and keep the left VP's x where its lines cross that y.
const horizonY = vry;
const leftAtHorizon = Object.values(leftLines).map(([a, b]) => a[0] + (horizonY - a[1]) * (b[0] - a[0]) / (b[1] - a[1]));
const vlxH = leftAtHorizon.reduce((s, v) => s + v, 0) / leftAtHorizon.length;

const dy = horizonY - PY;
const f = Math.sqrt(-((vrx - PX) * (vlxH - PX) + dy * dy));
const pitch = Math.atan(dy / f); // + = camera looks UP (horizon below centre)
const yawR = Math.atan((vrx - PX) * Math.cos(pitch) / f); // front face direction, right of forward
const yawL = Math.atan((vlxH - PX) * Math.cos(pitch) / f); // left face direction (negative = left)

// World: X forward (ground projection of view), Y left, Z up. Camera at (0,0,h).
const cp = Math.cos(pitch), sp = Math.sin(pitch);
function project([X, Y, Z], h) {
  const zr = Z - h;
  const depth = X * cp + zr * sp;
  const up = -X * sp + zr * cp;
  return [PX - f * Y / depth, PY - f * up / depth];
}
// Ray through pixel, in world space (unnormalised), from camera (0,0,h).
function ray([x, y]) {
  const u = (PX - x) / f; // left
  const v = (PY - y) / f; // up
  // camera axes: forward (cp,0,sp), left (0,1,0), up (-sp,0,cp)
  return [cp - v * sp, u, sp + v * cp];
}
const dR = [Math.cos(yawR), -Math.sin(yawR)]; // along front face, to the right
const dL = [Math.cos(yawL), -Math.sin(yawL)]; // along left face, to the left (yawL<0 -> +Y)

// ---- Solve scale: corner distance a, camera height h, platform height p, door offset s ----
// Corner base B = a * (unit ray direction of cornerBase on ground plane z=p).
function residuals([a, h, p, s]) {
  const rc = ray(m.cornerBase);
  const tc = a / rc[0];
  const B = [rc[0] * tc, rc[1] * tc, h + rc[2] * tc]; // point on the corner ray at forward distance a
  const out = [];
  out.push(B[2] - p); // corner base sits at platform height
  const D = [B[0] + s * dL[0], B[1] + s * dL[1]];
  const db = project([D[0], D[1], p], h), dt = project([D[0], D[1], p + DOOR_HEIGHT_M], h);
  out.push((db[0] - m.doorBottom[0]) / 50, (db[1] - m.doorBottom[1]) / 50, (dt[1] - m.doorTop[1]) / 50);
  return out;
}
function solve(x) {
  for (let it = 0; it < 200; it++) {
    const r = residuals(x);
    const J = r.map(() => []);
    for (let k = 0; k < x.length; k++) {
      const e = 1e-6 * Math.max(1, Math.abs(x[k]));
      const x2 = x.slice(); x2[k] += e;
      const r2 = residuals(x2);
      r2.forEach((v, i) => (J[i][k] = (v - r[i]) / e));
    }
    // Gauss-Newton with damping (normal equations)
    const n = x.length, A = Array.from({ length: n }, () => Array(n).fill(0)), g = Array(n).fill(0);
    for (let i = 0; i < r.length; i++) for (let a = 0; a < n; a++) {
      g[a] += J[i][a] * r[i];
      for (let b = 0; b < n; b++) A[a][b] += J[i][a] * J[i][b];
    }
    for (let a = 0; a < n; a++) A[a][a] += 1e-6;
    const dx = gauss(A, g.map((v) => -v));
    for (let k = 0; k < n; k++) x[k] += dx[k];
    if (Math.hypot(...dx) < 1e-10) break;
  }
  return x;
}
function gauss(A, b) {
  const n = b.length, M = A.map((row, i) => [...row, b[i]]);
  for (let c = 0; c < n; c++) {
    let piv = c;
    for (let r = c + 1; r < n; r++) if (Math.abs(M[r][c]) > Math.abs(M[piv][c])) piv = r;
    [M[c], M[piv]] = [M[piv], M[c]];
    for (let r = 0; r < n; r++) if (r !== c) {
      const k = M[r][c] / M[c][c];
      for (let j = c; j <= n; j++) M[r][j] -= k * M[c][j];
    }
  }
  return M.map((row, i) => row[n] / row[i]);
}

const [a, h, p, sDoor] = solve([10, 0.4, 0.15, 1.5]);
const rc = ray(m.cornerBase), tc = a / rc[0];
const corner = [rc[0] * tc, rc[1] * tc]; // ground-plane XY of the front-left body corner

// Intersect a pixel ray with a vertical wall plane through `corner` along `dir`.
function onWall(px, dir) {
  const r = ray(px);
  // plane normal (horizontal) perpendicular to dir
  const nrm = [-dir[1], dir[0]];
  const t = (nrm[0] * corner[0] + nrm[1] * corner[1]) / (nrm[0] * r[0] + nrm[1] * r[1]);
  const P = [r[0] * t, r[1] * t, h + r[2] * t];
  const along = (P[0] - corner[0]) * dir[0] + (P[1] - corner[1]) * dir[1];
  return { along, z: P[2], P };
}
const L = (k) => onWall(m[k], dL), F = (k) => onWall(m[k], dR);
const r2 = (v) => Math.round(v * 100) / 100;

const dist = Math.hypot(corner[0], corner[1]);
const hfov = 2 * Math.atan(PX / f) * 180 / Math.PI;
const result = {
  camera: {
    focalPx: r2(f),
    horizontalFovDeg: r2(hfov),
    focalMm_fullFrame36: r2(36 * f / W),
    focalMm_ueDefault23_76: r2(23.76 * f / W),
    pitchUpDeg: r2(pitch * 180 / Math.PI),
    heightM: r2(h),
    distanceToCornerM: r2(dist),
    frontFaceYawFromViewDeg: r2(yawR * 180 / Math.PI),
    leftFaceYawFromViewDeg: r2(yawL * 180 / Math.PI),
    horizonY: r2(horizonY),
    vpFront: [r2(vrx), r2(vry)],
    vpLeft: [r2(vlxH), r2(horizonY)],
    vpLeftRaw: [r2(vlx), r2(vly)],
    vpPairsFront: vrAll.map((q) => q.map(r2)),
  },
  kiosk: {
    platformHeightM: r2(p),
    doorCentreFromCornerM: r2(sDoor),
    leftFaceLengthM: r2(L('leftWallEnd').along),
    frontFaceLengthM: r2(F('frontWallEnd').along),
    serviceWindow: {
      fromCornerM: [r2(F('serviceWinLeft').along), r2(F('serviceWinRight').along)],
      topZ: r2(F('serviceWinTop').z),
    },
    counterLipZ_onWallPlane: r2(F('counterTopFront').z),
    glazedWindow: {
      fromCornerM: [r2(F('glazedWinLeft').along), r2(F('glazedWinRight').along)],
      zRange: [r2(F('glazedWinBottom').z), r2(F('glazedWinTop').z)],
    },
    canopyAtCorner_onWallPlane: { bottomZ: r2(F('canopyCornerBottom').z), topZ: r2(F('canopyCornerTop').z) },
    canopyFrontEnd_onWallPlane: { along: r2(F('canopyFrontEndTop').along), bottomZ: r2(F('canopyFrontEndBottom').z), topZ: r2(F('canopyFrontEndTop').z) },
    canopyLeftEnd_onWallPlane: { along: r2(L('canopyLeftEndTop').along), bottomZ: r2(L('canopyLeftEndBottom').z), topZ: r2(L('canopyLeftEndTop').z) },
    roofTops_onFrontPlane: { tallestBox: r2(L('roofTallestBox').z), tanks: r2(F('roofTanks').z), mast: r2(F('roofMastTop').z) },
    leftLanternZ: r2(L('leftLantern').z),
  },
  check: {
    doorBottomPx: project([corner[0] + sDoor * dL[0], corner[1] + sDoor * dL[1], p], h).map(r2),
    doorTopPx: project([corner[0] + sDoor * dL[0], corner[1] + sDoor * dL[1], p + DOOR_HEIGHT_M], h).map(r2),
    cornerBasePx: project([corner[0], corner[1], p], h).map(r2),
  },
};
console.log(JSON.stringify(result, null, 2));
const ji = process.argv.indexOf('--json');
if (ji > 0) fs.writeFileSync(process.argv[ji + 1], JSON.stringify(result, null, 2));
