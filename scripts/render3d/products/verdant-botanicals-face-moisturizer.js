// Daily Face Moisturizer SPF 30: heavy frosted-glass jar, sage matte cap, wrap label, leaf sprig.
import * as THREE from "three";
import { canvasTexture, drawLeafMark, filletProfile, lathe, leafGeometry, leafMaterial, spacedText } from "../studio.js";

export const studio = { fov: 26 };

const SAGE = "#5f8a78";
const INK = "#2f4a40";

function labelTexture() {
  return canvasTexture(2400, 900, (ctx, w, h) => {
    ctx.fillStyle = "#fbfaf4";
    ctx.fillRect(0, 0, w, h);
    // faint paper tooth
    for (let i = 0; i < 12000; i++) {
      ctx.fillStyle = `rgba(120,110,90,${Math.random() * 0.035})`;
      ctx.fillRect(Math.random() * w, Math.random() * h, 2, 2);
    }
    ctx.strokeStyle = SAGE;
    ctx.lineWidth = 4;
    ctx.strokeRect(40, 40, w - 80, h - 80);
    ctx.textAlign = "center";
    ctx.textBaseline = "alphabetic";
    drawLeafMark(ctx, w / 2, 170, 110, SAGE);
    ctx.fillStyle = INK;
    ctx.font = "600 64px Georgia, 'Times New Roman', serif";
    spacedText(ctx, "VERDANT BOTANICALS", w / 2, 320, 18);
    ctx.fillStyle = "#1f2f29";
    ctx.font = "italic 400 150px Georgia, serif";
    spacedText(ctx, "Daily Face Moisturizer", w / 2, 510, 1);
    ctx.strokeStyle = SAGE;
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(w / 2 - 260, 585);
    ctx.lineTo(w / 2 + 260, 585);
    ctx.stroke();
    ctx.fillStyle = SAGE;
    ctx.font = "600 62px 'Segoe UI', Arial, sans-serif";
    spacedText(ctx, "BROAD SPECTRUM SPF 30", w / 2, 690, 14);
    ctx.fillStyle = "#5c6b65";
    ctx.font = "400 48px 'Segoe UI', Arial, sans-serif";
    spacedText(ctx, "50 mL  ·  1.7 FL OZ", w / 2, 800, 8);
  });
}

function capTopTexture() {
  return canvasTexture(1024, 1024, (ctx, w, h) => {
    ctx.clearRect(0, 0, w, h);
    ctx.translate(w / 2, h / 2);
    ctx.fillStyle = "rgba(40,80,65,0.55)";
    ctx.font = "600 58px Georgia, serif";
    ctx.textAlign = "center";
    const text = "VERDANT BOTANICALS  ·  VERDANT BOTANICALS  ·  ";
    const R = 360;
    const step = (Math.PI * 2) / text.length;
    for (let i = 0; i < text.length; i++) {
      ctx.save();
      ctx.rotate(i * step);
      ctx.fillText(text[i], 0, -R);
      ctx.restore();
    }
    drawLeafMark(ctx, 0, 0, 170, "rgba(40,80,65,0.55)");
  });
}

export function build() {
  const root = new THREE.Group();

  // Glass: closed wall profile (outer up, over the rim, down the inside to a thick base).
  const glassProfile = filletProfile([
    [0, 0],
    [3.25, 0, 0.45],
    [3.25, 3.95, 0.4],
    [2.95, 4.28, 0.18],
    [2.95, 4.78, 0.08],
    [2.58, 4.78, 0.08],
    [2.58, 1.4, 0.55],
    [0, 1.36],
  ], 10);
  const glass = new THREE.Mesh(
    lathe(glassProfile, 160),
    new THREE.MeshPhysicalMaterial({
      color: "#f8fcfa",
      transmission: 1,
      roughness: 0.28,
      thickness: 1.6,
      ior: 1.5,
      attenuationColor: new THREE.Color("#e2f2eb"),
      attenuationDistance: 6,
      specularIntensity: 1,
      envMapIntensity: 1.1,
    }),
  );
  root.add(glass);

  // Cream inside, seen softly through the frosted wall.
  const cream = new THREE.Mesh(
    lathe(filletProfile([[0, 1.37], [2.575, 1.37, 0.5], [2.575, 4.3, 0.1], [0, 4.45]], 8), 96),
    new THREE.MeshPhysicalMaterial({ color: "#fbfbf6", roughness: 0.55, sheen: 0.4, sheenColor: new THREE.Color("#ffffff") }),
  );
  root.add(cream);

  // Cap.
  const capMat = new THREE.MeshPhysicalMaterial({ color: "#93b5a5", roughness: 0.6, sheen: 0.6, sheenRoughness: 0.45, sheenColor: new THREE.Color("#e3f3ec") });
  const cap = new THREE.Mesh(lathe(filletProfile([[2.9, 4.36], [3.36, 4.36, 0.1], [3.36, 6.42, 0.34], [0, 6.42]], 10), 160), capMat);
  root.add(cap);
  const capTop = new THREE.Mesh(
    new THREE.CircleGeometry(2.95, 96),
    new THREE.MeshPhysicalMaterial({ map: capTopTexture(), transparent: true, roughness: 0.6, polygonOffset: true, polygonOffsetFactor: -2 }),
  );
  capTop.rotation.x = -Math.PI / 2;
  capTop.position.y = 6.421;
  capTop.userData.shadow = false;
  root.add(capTop);

  // Wrap label on the front.
  const th = 1.95;
  const label = new THREE.Mesh(
    new THREE.CylinderGeometry(3.268, 3.268, 2.35, 128, 1, true, -th / 2, th),
    new THREE.MeshPhysicalMaterial({ map: labelTexture(), roughness: 0.62, clearcoat: 0.15, clearcoatRoughness: 0.4 }),
  );
  label.position.y = 2.12;
  root.add(label);

  // Leaf sprig lying on the table, front-right.
  const sprig = new THREE.Group();
  const curve = new THREE.CatmullRomCurve3([
    new THREE.Vector3(7.6, 0.08, 3.4),
    new THREE.Vector3(6.0, 0.08, 1.9),
    new THREE.Vector3(5.0, 0.1, 0.2),
    new THREE.Vector3(4.6, 0.12, -1.6),
  ]);
  sprig.add(new THREE.Mesh(new THREE.TubeGeometry(curve, 64, 0.065, 8), new THREE.MeshPhysicalMaterial({ color: "#6f7f45", roughness: 0.5 })));
  const mat = leafMaterial("#4f7d42", 7);
  const up = new THREE.Vector3(0, 1, 0);
  const leaves = [
    [0.12, 1, 2.6, 1.15, 55], [0.3, -1, 2.9, 1.25, 50], [0.48, 1, 2.8, 1.2, 48], [0.64, -1, 2.5, 1.05, 45], [0.8, 1, 2.1, 0.9, 40], [1.0, 0, 1.6, 0.7, 0],
  ];
  for (const [t, side, len, wid, ang] of leaves) {
    const p = curve.getPointAt(Math.min(t, 1));
    const tan = curve.getTangentAt(Math.min(t, 0.999)).setY(0).normalize();
    const dir = tan.clone().applyAxisAngle(up, THREE.MathUtils.degToRad(side * ang)).add(new THREE.Vector3(0, 0.12, 0)).normalize();
    const z = up.clone().addScaledVector(dir, -up.dot(dir)).normalize();
    const x = new THREE.Vector3().crossVectors(dir, z);
    const g = leafGeometry({ length: len, width: wid, fold: 0.22, arch: 0.25, twist: side * 0.15, widest: 0.45 });
    const leaf = new THREE.Mesh(g, mat);
    leaf.matrixAutoUpdate = false;
    leaf.matrix.makeBasis(x, dir, z).setPosition(p.x, p.y + 0.02, p.z);
    sprig.add(leaf);
  }
  root.add(sprig);

  return { root, frame: { fill: 0.64, elev: 17, azim: 4, yOffset: -0.02 } };
}
