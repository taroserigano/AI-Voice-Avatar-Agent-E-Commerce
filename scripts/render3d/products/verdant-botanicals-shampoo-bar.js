// Rosemary Mint Shampoo Bar: soft-bevelled pale green bar with a debossed leaf + wordmark,
// on a slatted bamboo soap dish, with a rosemary sprig.
import * as THREE from "three";
import { canvasTexture, fbm3, roundedBox, spacedText } from "../studio.js";
import { bambooMaterial, proceduralMaterial } from "../materials.js";

export const studio = { fov: 26 };

const SOAP = { w: 7.4, h: 2.3, d: 4.9, r: 0.75 };

function stampHeightmap() {
  // 1 = bar surface, 0 = pressed in: a stamped leaf (outline, midrib, veins) over the wordmark,
  // with a thin border line. Maps x -> u, z -> v over the soap's footprint.
  const tex = canvasTexture(1480, 980, (ctx, w, h) => {
    ctx.fillStyle = "#fff";
    ctx.fillRect(0, 0, w, h);
    ctx.filter = "blur(2.5px)";
    ctx.strokeStyle = "#000";
    ctx.fillStyle = "#000";
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    // leaf
    ctx.save();
    ctx.translate(w / 2, h * 0.4);
    ctx.rotate(-0.55);
    ctx.lineWidth = 20;
    ctx.beginPath();
    ctx.moveTo(0, 170);
    ctx.bezierCurveTo(-140, 80, -128, -110, 0, -185);
    ctx.bezierCurveTo(128, -110, 140, 80, 0, 170);
    ctx.stroke();
    ctx.lineWidth = 13;
    ctx.beginPath();
    ctx.moveTo(0, 235);
    ctx.lineTo(0, -150);
    for (const k of [-1, 1]) for (const yy of [95, 30, -35, -95]) { ctx.moveTo(0, yy + 28); ctx.quadraticCurveTo(k * 42, yy + 6, k * 86, yy - 26); }
    ctx.stroke();
    ctx.restore();
    ctx.textAlign = "center";
    ctx.font = "700 112px Georgia, serif";
    spacedText(ctx, "VERDANT", w / 2, h * 0.8, 26);
    ctx.filter = "none";
  }, { srgb: false });
  const c = tex.userData.canvas;
  return { data: c.getContext("2d").getImageData(0, 0, c.width, c.height), w: c.width, h: c.height };
}

function sampleHeight(hm, u, v) {
  const x = Math.min(hm.w - 1.001, Math.max(0, u * (hm.w - 1)));
  const y = Math.min(hm.h - 1.001, Math.max(0, v * (hm.h - 1)));
  const x0 = Math.floor(x), y0 = Math.floor(y), fx = x - x0, fy = y - y0;
  const px = (xx, yy) => hm.data.data[(yy * hm.w + xx) * 4] / 255;
  return (px(x0, y0) * (1 - fx) + px(x0 + 1, y0) * fx) * (1 - fy) + (px(x0, y0 + 1) * (1 - fx) + px(x0 + 1, y0 + 1) * fx) * fy;
}

function soapBar() {
  const { w, h, d, r } = SOAP;
  const g = roundedBox(w, h, d, r, 440);
  const hm = stampHeightmap();
  const p = g.attributes.position, n = g.attributes.normal;
  const depth = 0.1;
  const colors = new Float32Array(p.count * 3).fill(1);
  for (let i = 0; i < p.count; i++) {
    const x = p.getX(i), y = p.getY(i), z = p.getZ(i);
    const ny = n.getY(i);
    if (ny <= 0.2) continue;
    const top = Math.pow(ny, 6);
    // gentle pillow dome on the top face
    const dome = 0.1 * (1 - (x / (w / 2)) ** 2) * (1 - (z / (d / 2)) ** 2);
    const pressed = (1 - sampleHeight(hm, x / w + 0.5, z / d + 0.5)) * top;
    p.setY(i, y + top * dome - pressed * depth);
    // pressed soap is denser and a touch darker
    colors[i * 3] = colors[i * 3 + 1] = colors[i * 3 + 2] = 1 - 0.22 * pressed;
  }
  g.setAttribute("color", new THREE.BufferAttribute(colors, 3));
  // hand-cut surface: faint undulation + fine pits, pushed along the normal
  for (let i = 0; i < p.count; i++) {
    const x = p.getX(i), y = p.getY(i), z = p.getZ(i);
    const k = (fbm3(x * 1.2, y * 1.2, z * 1.2) - 0.5) * 0.018 + (fbm3(x * 9, y * 9, z * 9, 2) - 0.5) * 0.004;
    p.setXYZ(i, x + n.getX(i) * k, y + n.getY(i) * k, z + n.getZ(i) * k);
  }
  g.computeVertexNormals();
  g.translate(0, h / 2, 0);
  const mat = new THREE.MeshPhysicalMaterial({
    color: "#abcca5",
    vertexColors: true,
    roughness: 0.62,
    sheen: 0.3,
    sheenRoughness: 0.55,
    sheenColor: new THREE.Color("#eef7e8"),
    emissive: new THREE.Color("#2a4a2a"),
    emissiveIntensity: 0.08, // cheap subsurface lift in the shadow side
  });
  proceduralMaterial(mat, `
    float n1 = fbm(p * 1.3);
    col *= 0.94 + 0.1 * n1;
    // rosemary / spirulina flecks
    float f = vnoise(p * 34.0);
    float fleck = smoothstep(0.88, 0.95, f);
    col = mix(col, vec3(0.08, 0.13, 0.06), fleck * 0.75);
    float g2 = smoothstep(0.9, 0.97, vnoise(p * 21.0 + 7.3));
    col = mix(col, vec3(0.25, 0.35, 0.18), g2 * 0.5);
    rough = 0.58 + 0.12 * n1;`);
  return new THREE.Mesh(g, mat);
}

function soapDish() {
  const dish = new THREE.Group();
  const slatLen = 11.0, slatD = 0.86, gap = 0.3, count = 7;
  const span = count * slatD + (count - 1) * gap;
  // two cross battens underneath
  for (const x of [-3.9, 3.9]) {
    const b = new THREE.Mesh(roundedBox(1.1, 0.75, span + 0.2, 0.2, 40), bambooMaterial({ seed: x, axis: "z", base: "#d6b98a", dark: "#a98452" }));
    b.position.set(x, 0.375, 0);
    dish.add(b);
  }
  for (let i = 0; i < count; i++) {
    const s = new THREE.Mesh(roundedBox(slatLen, 0.5, slatD, 0.09, 160), bambooMaterial({ seed: i * 1.7 + 0.3, axis: "x", base: "#d6b98a", dark: "#a98452" }));
    s.position.set((i % 2 ? 0.05 : -0.03), 0.75 + 0.25, -span / 2 + slatD / 2 + i * (slatD + gap));
    dish.add(s);
  }
  dish.userData.top = 0.75 + 0.5;
  return dish;
}

function rosemarySprig(curvePts, { needles = 120, seed = 1 } = {}) {
  const g = new THREE.Group();
  const curve = new THREE.CatmullRomCurve3(curvePts);
  g.add(new THREE.Mesh(new THREE.TubeGeometry(curve, 80, 0.085, 8), new THREE.MeshPhysicalMaterial({ color: "#6b6a45", roughness: 0.7 })));
  const needleGeo = new THREE.CapsuleGeometry(0.1, 1.0, 4, 10);
  needleGeo.translate(0, 0.6, 0); // base at origin, pointing +y
  needleGeo.scale(1, 1, 0.5);
  { // taper toward the tip
    const pp = needleGeo.attributes.position;
    for (let i = 0; i < pp.count; i++) { const k = 1 - 0.55 * Math.max(0, pp.getY(i) - 0.2) / 1.0; pp.setX(i, pp.getX(i) * k); pp.setZ(i, pp.getZ(i) * k); }
    needleGeo.computeVertexNormals();
  }
  const mat = new THREE.MeshPhysicalMaterial({ color: "#4d6547", roughness: 0.55, clearcoat: 0.25, clearcoatRoughness: 0.4, sheen: 0.8, sheenColor: new THREE.Color("#c3d1bb"), sheenRoughness: 0.35 });
  const inst = new THREE.InstancedMesh(needleGeo, mat, needles);
  let s = seed;
  const rnd = () => ((s = (s * 16807) % 2147483647) / 2147483647);
  const m = new THREE.Matrix4(), q = new THREE.Quaternion(), up = new THREE.Vector3(0, 1, 0);
  for (let i = 0; i < needles; i++) {
    const t = 0.04 + (i / needles) * 0.94;
    const p = curve.getPointAt(t);
    const tan = curve.getTangentAt(t);
    const side = new THREE.Vector3().crossVectors(tan, up).normalize();
    const nrm = new THREE.Vector3().crossVectors(side, tan).normalize();
    const phi = i * 2.39996 + rnd() * 0.4;
    const radial = side.clone().multiplyScalar(Math.cos(phi)).addScaledVector(nrm, Math.sin(phi));
    if (radial.y < 0) radial.y *= 0.25; // needles resting on the surface splay sideways
    radial.normalize();
    const lean = 0.75 + rnd() * 0.3; // toward the tip
    const dir = radial.multiplyScalar(Math.cos(lean)).addScaledVector(tan, Math.sin(lean) + 0.15).normalize();
    q.setFromUnitVectors(up, dir);
    const len = (1.2 - 0.5 * t) * (0.75 + rnd() * 0.45);
    m.compose(p, q, new THREE.Vector3(1, len, 1));
    inst.setMatrixAt(i, m);
    inst.setColorAt(i, new THREE.Color().setHSL(0.27 + rnd() * 0.05, 0.18 + rnd() * 0.12, 0.72 + rnd() * 0.28));
  }
  // a few young needles clustered at the tip
  g.add(inst);
  return g;
}

export function build() {
  const root = new THREE.Group();
  const dish = soapDish();
  root.add(dish);
  const soap = soapBar();
  soap.position.y = dish.userData.top;
  soap.rotation.y = 0.04;
  root.add(soap);
  const sprig = rosemarySprig([
    new THREE.Vector3(7.8, 0.3, 5.6),
    new THREE.Vector3(5.8, 0.3, 4.9),
    new THREE.Vector3(3.9, 0.3, 4.9),
    new THREE.Vector3(1.9, 0.32, 5.5),
  ]);
  root.add(sprig);
  root.rotation.y = -0.32;
  return { root, frame: { fill: 0.7, elev: 50, azim: 0, yOffset: -0.02 } };
}
