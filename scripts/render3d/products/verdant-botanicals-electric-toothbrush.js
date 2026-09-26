// Sonic Electric Toothbrush: slim glossy white handle, mint accent band, power button,
// replaceable brush head with tufted bristles, standing on a round charging base.
import * as THREE from "three";
import { canvasTexture, drawLeafMark, filletProfile, lathe, roundedBox, spacedText } from "../studio.js";
import { proceduralMaterial } from "../materials.js";

export const studio = { fov: 24, keyDir: [-0.75, 1.3, 0.6], envIntensity: 0.62, keyIntensity: 1.1, shadowOpacity: 0.65 };

const MINT = "#79c9b2";
const BASE_TOP = 1.62;
const HANDLE_H = 14.6;
const OVAL = 0.88; // handle cross-section depth / width

function glossyWhite(extra = {}) {
  return new THREE.MeshPhysicalMaterial({ color: "#f6f6f3", roughness: 0.32, clearcoat: 1, clearcoatRoughness: 0.05, ...extra });
}

function handleTexture() {
  // u wraps the handle (0.5 = front), v = height / HANDLE_H (0 = bottom)
  return canvasTexture(1024, 2048, (ctx, w, h) => {
    ctx.fillStyle = "#f6f6f3";
    ctx.fillRect(0, 0, w, h);
    const Y = (cm) => h * (1 - cm / HANDLE_H);
    // mint accent band just under the shoulder
    ctx.fillStyle = MINT;
    ctx.fillRect(0, Y(13.15), w, Y(12.55) - Y(13.15));
    // mode indicator dots under the button
    ctx.fillStyle = "#b9c2bf";
    for (const [i, cm] of [7.9, 7.45, 7.0].entries()) {
      ctx.beginPath();
      ctx.arc(w / 2, Y(cm), i === 0 ? 7 : 6, 0, Math.PI * 2);
      ctx.fill();
    }
    // vertical wordmark, reading bottom-to-top
    ctx.save();
    ctx.translate(w / 2 + 12, Y(4.2));
    ctx.rotate(-Math.PI / 2);
    ctx.fillStyle = "#8f9a96";
    ctx.textAlign = "center";
    ctx.font = "600 34px 'Segoe UI', Arial, sans-serif";
    spacedText(ctx, "VERDANT", 0, 0, 10);
    ctx.restore();
    drawLeafMark(ctx, w / 2, Y(2.2), 34, "#8fb8aa");
  });
}

function buttonIconTexture() {
  return canvasTexture(256, 256, (ctx, w, h) => {
    ctx.clearRect(0, 0, w, h);
    ctx.strokeStyle = "rgba(255,255,255,0.92)";
    ctx.lineWidth = 16;
    ctx.lineCap = "round";
    ctx.beginPath();
    ctx.arc(w / 2, h / 2 + 6, 58, -Math.PI / 2 + 0.7, Math.PI * 1.5 - 0.7);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(w / 2, h / 2 - 70);
    ctx.lineTo(w / 2, h / 2 + 4);
    ctx.stroke();
  });
}

/** Radius of the handle profile at height y (for placing parts on its surface). */
function handleRadius(prof, y) {
  for (let i = 1; i < prof.length; i++) {
    const a = prof[i - 1], b = prof[i];
    if ((a.y - y) * (b.y - y) <= 0 && a.y !== b.y) return a.x + ((y - a.y) / (b.y - a.y)) * (b.x - a.x);
  }
  return prof[0].x;
}

export function build() {
  const root = new THREE.Group();

  // Charging base.
  const baseProf = filletProfile([[0, 0], [2.95, 0, 0.2], [3.15, 0.3, 0.25], [3.15, 1.0, 0.55], [2.55, BASE_TOP, 0.35], [1.45, BASE_TOP, 0.2], [1.38, BASE_TOP - 0.12], [0, BASE_TOP - 0.12]], 10);
  const base = new THREE.Mesh(lathe(baseProf, 160), new THREE.MeshPhysicalMaterial({ color: "#f1f2ef", roughness: 0.42, clearcoat: 0.6, clearcoatRoughness: 0.2 }));
  root.add(base);
  const ring = new THREE.Mesh(new THREE.TorusGeometry(2.62, 0.026, 12, 160), new THREE.MeshPhysicalMaterial({ color: "#5fb49b", roughness: 0.5 }));
  ring.rotation.x = Math.PI / 2;
  ring.position.y = BASE_TOP - 0.01;
  root.add(ring);

  const brush = new THREE.Group();
  brush.position.y = BASE_TOP - 0.1;

  // Handle.
  const hp = filletProfile([[0, 0], [1.16, 0, 0.18], [1.28, 0.9], [1.34, 4.0], [1.29, 8.0], [1.19, 11.6], [1.12, 12.9, 0.9], [0.66, 14.2, 0.45], [0.56, HANDLE_H], [0, HANDLE_H + 0.02]], 12);
  const hg = lathe(hp, 160);
  const uv = hg.attributes.uv, pos = hg.attributes.position;
  for (let i = 0; i < uv.count; i++) uv.setY(i, pos.getY(i) / HANDLE_H);
  hg.scale(1, 1, OVAL);
  const handle = new THREE.Mesh(hg, glossyWhite({ map: handleTexture() }));
  brush.add(handle);

  // Power button: soft-touch mint pill, slightly proud of the surface.
  const by = 9.35;
  const rb = handleRadius(hp, by) * OVAL;
  const btn = new THREE.Mesh(new THREE.CapsuleGeometry(0.3, 0.55, 8, 32), new THREE.MeshPhysicalMaterial({ color: MINT, roughness: 0.55, sheen: 0.4, sheenColor: new THREE.Color("#e6f7f1") }));
  btn.scale.set(1, 1, 0.32);
  btn.position.set(0, by, rb - 0.03);
  brush.add(btn);
  const icon = new THREE.Mesh(new THREE.PlaneGeometry(0.36, 0.36), new THREE.MeshBasicMaterial({ map: buttonIconTexture(), transparent: true, depthWrite: false }));
  icon.position.set(0, by, rb + 0.072);
  icon.userData.shadow = false;
  brush.add(icon);

  // Replaceable head: neck + oval head + bristle tufts.
  const neckProf = filletProfile([[0, HANDLE_H - 0.4], [0.555, HANDLE_H - 0.4, 0.1], [0.56, HANDLE_H + 0.3, 0.6], [0.44, 16.8], [0.36, 19.2, 0.5], [0.4, 19.8], [0, 19.9]], 10);
  const neck = new THREE.Mesh(lathe(neckProf, 96).scale(1, 1, 0.82), glossyWhite());
  brush.add(neck);
  const headH = 2.45, headW = 1.08, headD = 0.62;
  const head = new THREE.Mesh(roundedBox(headW, headH, headD, 0.28, 64), glossyWhite());
  head.position.set(0, 19.55 + headH / 2 - 0.35, 0.06);
  brush.add(head);
  // bristles: 3 x 8 tufts, slightly domed profile, mint centre rows
  const tuftGeo = new THREE.CapsuleGeometry(0.062, 0.8, 4, 12);
  tuftGeo.rotateX(Math.PI / 2);
  // nylon filaments: fine striations along each tuft (tuft axis = local z)
  const fibres = `
    float fib = vnoise(vec3(p.x * 160.0, p.y * 160.0, p.z * 2.0));
    float tip = smoothstep(0.25, 0.5, p.z);
    col *= 0.82 + 0.26 * fib + 0.08 * tip;
    rough = 0.38 + 0.2 * fib;`;
  const white = proceduralMaterial(new THREE.MeshPhysicalMaterial({ color: "#f7f8f5", roughness: 0.45, sheen: 0.6, sheenColor: new THREE.Color("#ffffff"), transmission: 0.15, thickness: 0.3 }), fibres);
  const mint = proceduralMaterial(new THREE.MeshPhysicalMaterial({ color: "#86d1bb", roughness: 0.45, sheen: 0.6, sheenColor: new THREE.Color("#e8fff7"), transmission: 0.12, thickness: 0.3 }), fibres);
  const faceZ = head.position.z + headD / 2;
  for (let r = 0; r < 9; r++) for (let c = 0; c < 4; c++) {
    const yy = head.position.y - headH / 2 + 0.3 + r * 0.232;
    const xx = (c - 1.5) * 0.215 * (r === 0 || r === 8 ? 0.85 : 1);
    const inner = c === 1 || c === 2;
    const dome = 0.1 * Math.sin((r / 8) * Math.PI) + (inner ? 0.05 : 0);
    const len = 0.74 + dome;
    const t = new THREE.Mesh(tuftGeo, inner && r % 3 !== 1 ? mint : white);
    t.scale.set(1, 1, len / 0.924);
    t.position.set(xx, yy, faceZ + len / 2 - 0.06);
    t.rotation.y = (c - 1.5) * 0.06;
    t.rotation.x = (r - 4) * -0.012;
    brush.add(t);
  }

  brush.rotation.y = -0.6;
  root.add(brush);
  root.rotation.y = 0;
  return { root, frame: { fill: 0.72, elev: 9, azim: 0, yOffset: 0 } };
}
