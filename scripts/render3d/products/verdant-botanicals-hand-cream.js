// Shea Butter Hand Cream Trio: three laminate squeeze tubes (round shoulder -> flattened crimped
// seal), pastel screw caps, printed labels, lying fanned out on the sweep.
import * as THREE from "three";
import { canvasTexture, drawLeafMark, filletProfile, fbm3, lathe, spacedText } from "../studio.js";

export const studio = { fov: 26, envIntensity: 0.78, keyIntensity: 1.0 };

const R = 1.6; // tube radius
const LEN = 11.6; // body + seal length along x
const SEAL = 0.1; // last 10% of the length is the flat crimped seal
const TEX = 2048;

const VARIANTS = [
  { cap: "#f2c2a6", ink: "#c7775a", scent: "Peach Blossom" },
  { cap: "#a9dcc8", ink: "#3f8f75", scent: "Fresh Mint" },
  { cap: "#cbbbe8", ink: "#7a64b0", scent: "Lavender" },
];

const flat = (s) => {
  // stays round for the first quarter, then eases into the flat seal
  const t = THREE.MathUtils.clamp((s - 0.24) / (1 - SEAL - 0.24), 0, 1);
  return Math.pow(t, 1.35) * (1.6 - 0.6 * t);
};

/** Tube body: s in [0,1] along +x, theta around; u = 0.5 on top, increasing toward the front (+z). */
function tubeBodyGeometry(seed) {
  const nT = 144, nS = 200;
  const pos = [], uv = [], idx = [];
  const bSeal = 0.03;
  for (let i = 0; i <= nS; i++) {
    const s = i / nS;
    const f = flat(s);
    const a = R + (Math.PI * R * 0.5 - R) * f;
    const b = R * (1 - f) + bSeal * f;
    const x = s * LEN;
    const crimp = s > 1 - SEAL ? 0.014 * Math.sin((x - (1 - SEAL) * LEN) * Math.PI * 2 / 0.11) : 0;
    for (let j = 0; j <= nT; j++) {
      const th = -Math.PI / 2 + (j / nT) * Math.PI * 2; // seam underneath
      const dent = 1 + (fbm3(x * 0.35 + seed, Math.cos(th) * 0.8, Math.sin(th) * 0.8) - 0.5) * 0.035 * (1 - f * 0.8);
      const z = a * Math.cos(th) * dent;
      const y = b * Math.sin(th) * dent + crimp;
      pos.push(x, y, z);
      uv.push(0.5 - (th - Math.PI / 2) / (Math.PI * 2), s);
    }
  }
  for (let i = 0; i < nS; i++) for (let j = 0; j < nT; j++) {
    const a = i * (nT + 1) + j, b = a + nT + 1;
    idx.push(a, b, a + 1, b, b + 1, a + 1);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute("uv", new THREE.Float32BufferAttribute(uv, 2));
  g.setIndex(idx);
  g.computeVertexNormals();
  return g;
}

function labelTexture(v) {
  return canvasTexture(TEX, TEX, (ctx, W, H) => {
    ctx.fillStyle = "#f5f1e9";
    ctx.fillRect(0, 0, W, H);
    // image space: X along the tube (0 = shoulder .. H = seal), Y around (1024 = top, larger = front)
    ctx.setTransform(0, -1, 1, 0, 0, H);
    const Xc = (s) => s * H;
    const mid = 1300; // centre of the visible face
    // coloured collar near the shoulder, all the way round
    ctx.fillStyle = v.cap;
    ctx.fillRect(Xc(0.0), 0, Xc(0.075), W);
    ctx.fillStyle = v.ink;
    ctx.fillRect(Xc(0.075), 0, 6, W);
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    const cx = Xc(0.36);
    drawLeafMark(ctx, Xc(0.155), mid - 8, 58, v.ink);
    ctx.fillStyle = "#3b4a44";
    ctx.font = "600 34px Georgia, serif";
    spacedText(ctx, "VERDANT BOTANICALS", cx, mid - 150, 11);
    ctx.fillStyle = "#26332e";
    ctx.font = "400 108px Georgia, serif";
    spacedText(ctx, "Shea Butter", cx, mid - 52, 1);
    ctx.fillStyle = "#3b4a44";
    ctx.font = "600 38px 'Segoe UI', Arial, sans-serif";
    spacedText(ctx, "HAND CREAM", cx, mid + 38, 15);
    ctx.fillStyle = v.ink;
    ctx.font = "italic 400 58px Georgia, serif";
    spacedText(ctx, v.scent, cx, mid + 112, 1);
    ctx.fillStyle = "#7b8580";
    ctx.font = "400 27px 'Segoe UI', Arial, sans-serif";
    spacedText(ctx, "75 mL  ·  2.5 FL OZ", cx, mid + 175, 6);
    // small print on the flattening part
    ctx.fillStyle = "#9aa39f";
    ctx.font = "400 24px 'Segoe UI', Arial, sans-serif";
    spacedText(ctx, "with shea butter & oat extract  ·  for dry hands", Xc(0.72), mid, 3);
    // seal: tiny batch code
    ctx.font = "400 20px 'Segoe UI', Arial, sans-serif";
    ctx.fillStyle = "#a9b0ad";
    spacedText(ctx, "LOT 26B14  EXP 09/28", Xc(0.955), mid, 3);
  });
}

function tube(v, seed) {
  const g = new THREE.Group();
  const tubeMat = new THREE.MeshPhysicalMaterial({ map: labelTexture(v), roughness: 0.34, clearcoat: 0.9, clearcoatRoughness: 0.14 });
  g.add(new THREE.Mesh(tubeBodyGeometry(seed), tubeMat));
  // shoulder + neck (lathe around y, turned onto the -x axis)
  const shoulder = filletProfile([[R, 0], [R * 0.985, 0.18, 0.12], [1.05, 0.55, 0.25], [0.72, 0.62, 0.08], [0.72, 0.95], [0, 0.95]], 10);
  const sg = lathe(shoulder, 144);
  sg.rotateZ(Math.PI / 2); // +y -> -x
  const plain = new THREE.MeshPhysicalMaterial({ color: "#f5f1e9", roughness: 0.34, clearcoat: 0.9, clearcoatRoughness: 0.14 });
  g.add(new THREE.Mesh(sg, plain));
  // screw cap with a soft rounded end and fine grip ribs
  const Rc = 1.3;
  const capProf = filletProfile([[0, 0], [Rc - 0.06, 0, 0.05], [Rc, 0.08, 0.06], [Rc, 1.75, 0.3], [0, 1.95]], 10);
  const cg = lathe(capProf, 160);
  const cp = cg.attributes.position;
  for (let i = 0; i < cp.count; i++) {
    const x = cp.getX(i), y = cp.getY(i), z = cp.getZ(i);
    const r = Math.hypot(x, z);
    if (r < Rc - 0.1 || y < 0.15 || y > 1.5) continue;
    const ang = Math.atan2(z, x);
    const k = 1 - 0.012 * (0.5 + 0.5 * Math.cos(ang * 60));
    cp.setX(i, x * k);
    cp.setZ(i, z * k);
  }
  cg.computeVertexNormals();
  cg.rotateZ(Math.PI / 2);
  cg.translate(-0.62, 0, 0);
  const capMat = new THREE.MeshPhysicalMaterial({ color: v.cap, roughness: 0.38, clearcoat: 0.4, clearcoatRoughness: 0.3, sheen: 0.3, sheenColor: new THREE.Color("#ffffff") });
  g.add(new THREE.Mesh(cg, capMat));
  // rest on the table: tilt so the seal end touches down, then drop onto y = 0
  const tilt = new THREE.Group();
  tilt.add(g);
  g.rotation.z = -Math.atan((R - 0.03) / (LEN * 0.82));
  tilt.updateMatrixWorld(true);
  const box = new THREE.Box3().setFromObject(g);
  g.position.y = -box.min.y;
  return tilt;
}

export function build() {
  const root = new THREE.Group();
  const layout = [
    { v: VARIANTS[2], pos: [-6.4, 0, -3.6], rot: 0.34 },
    { v: VARIANTS[1], pos: [-6.2, 0, 0.0], rot: 0.0 },
    { v: VARIANTS[0], pos: [-6.0, 0, 3.6], rot: -0.34 },
  ];
  layout.forEach((l, i) => {
    const t = tube(l.v, i * 3.7);
    t.position.set(...l.pos);
    t.rotation.y = l.rot;
    root.add(t);
  });
  return { root, frame: { fill: 0.72, elev: 38, azim: 0, yOffset: 0 } };
}
