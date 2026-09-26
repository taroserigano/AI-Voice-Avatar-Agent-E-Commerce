// Shared product-photo studio for three.js renders.
// - HDR accumulation: every frame jitters the camera sub-pixel (anti-aliasing) and moves the single
//   shadow light over an area / sky dome (soft shadows + contact occlusion), averaged in linear HDR.
// - Supersampled internal resolution (ss x 1200) box-filtered down to 1200 at the end.
// - Seamless mint sweep: screen-space gradient whose colors are pre-inverted through the tone mapper,
//   so the final pixels hit the requested hex values exactly. Floor = shadow catcher.
// - Softbox environment (PMREM) for reflections: big key top-left, fill right, strip rims behind.
import * as THREE from "three";
import { mergeVertices } from "three/addons/utils/BufferGeometryUtils.js";

export const OUT = 1200;

// ---------- colour helpers ----------
const srgbToLin = (c) => (c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4);
const hexToLin = (hex) => {
  const c = new THREE.Color(hex); // Color stores linear when ColorManagement is on
  return [c.r, c.g, c.b];
};

// "Studio" tone curve: linear up to K, exponential soft shoulder above (hue preserving, desaturates
// blown highlights to white). Linear where the sweep lives, so floor shadows darken it believably.
const TONE_K = 0.85, TONE_DESAT = 0.25;
export function toneJS(v, exposure) {
  let c = v.map((x) => x * exposure);
  const m = Math.max(...c);
  if (m <= TONE_K) return c;
  const fm = TONE_K + (1 - TONE_K) * (1 - Math.exp(-(m - TONE_K) / (1 - TONE_K)));
  c = c.map((x) => (x * fm) / m);
  const g = 1 - 1 / (TONE_DESAT * (m - fm) + 1);
  return c.map((x) => x + (fm - x) * g);
}
const TONE_GLSL = `
  vec3 studioTone(vec3 c){ c *= exposure; float m = max(c.r, max(c.g, c.b)); if (m <= ${TONE_K.toFixed(4)}) return c;
    float K = ${TONE_K.toFixed(4)}; float fm = K + (1.0 - K) * (1.0 - exp(-(m - K) / (1.0 - K)));
    c *= fm / m; float g = 1.0 - 1.0 / (${TONE_DESAT.toFixed(4)} * (m - fm) + 1.0); return mix(c, vec3(fm), g); }
  vec3 toSRGB(vec3 c){ c = clamp(c, 0.0, 1.0); return mix(c * 12.92, 1.055 * pow(c, vec3(1.0 / 2.4)) - 0.055, step(0.0031308, c)); }`;
export function invertToneMap(target, fn, exposure) {
  const x = target.slice();
  for (let sweep = 0; sweep < 12; sweep++) {
    for (let k = 0; k < 3; k++) {
      let lo = 0, hi = 50;
      for (let it = 0; it < 60; it++) {
        const mid = (lo + hi) / 2;
        x[k] = mid;
        if (fn(x, exposure)[k] < target[k]) lo = mid; else hi = mid;
      }
      x[k] = (lo + hi) / 2;
    }
  }
  return x;
}

// ---------- geometry helpers ----------
/** Round the corners of a 2D polyline. pts: [x, y, radius?][]; first/last are kept as-is. */
export function filletProfile(pts, segs = 8) {
  const out = [];
  for (let i = 0; i < pts.length; i++) {
    const [x, y, r = 0] = pts[i];
    if (i === 0 || i === pts.length - 1 || r <= 0) { out.push(new THREE.Vector2(x, y)); continue; }
    const p = new THREE.Vector2(x, y);
    const a = new THREE.Vector2(pts[i - 1][0], pts[i - 1][1]);
    const b = new THREE.Vector2(pts[i + 1][0], pts[i + 1][1]);
    const da = a.clone().sub(p);
    const db = b.clone().sub(p);
    const ra = Math.min(r, da.length() * 0.5);
    const rb = Math.min(r, db.length() * 0.5);
    const p0 = p.clone().add(da.normalize().multiplyScalar(ra));
    const p2 = p.clone().add(db.normalize().multiplyScalar(rb));
    for (let s = 0; s <= segs; s++) {
      const t = s / segs;
      const u = 1 - t;
      out.push(new THREE.Vector2(u * u * p0.x + 2 * u * t * p.x + t * t * p2.x, u * u * p0.y + 2 * u * t * p.y + t * t * p2.y));
    }
  }
  return out;
}

/** LatheGeometry with the seam at the back (u = 0.5 faces +z) and v = arc length along the profile. */
export function lathe(profile, segments = 128) {
  const g = new THREE.LatheGeometry(profile, segments, Math.PI, Math.PI * 2);
  const n = profile.length;
  const acc = [0];
  for (let j = 1; j < n; j++) acc.push(acc[j - 1] + profile[j].distanceTo(profile[j - 1]));
  const total = acc[n - 1] || 1;
  const uv = g.attributes.uv;
  for (let i = 0; i <= segments; i++) for (let j = 0; j < n; j++) uv.setY(i * n + j, acc[j] / total);
  g.userData.arc = acc.map((a) => a / total);
  return g;
}

/** Rounded box built from a finely subdivided cube (so it can take real displacement). */
export function roundedBox(w, h, d, r, res = 64) {
  const g = new THREE.BoxGeometry(1, 1, 1, res, Math.max(4, Math.round((res * h) / w)), Math.max(4, Math.round((res * d) / w)));
  const p = g.attributes.position;
  const hx = w / 2, hy = h / 2, hz = d / 2;
  const v = new THREE.Vector3(), q = new THREE.Vector3(), n = new THREE.Vector3();
  for (let i = 0; i < p.count; i++) {
    v.set(p.getX(i) * w, p.getY(i) * h, p.getZ(i) * d);
    q.set(THREE.MathUtils.clamp(v.x, -hx + r, hx - r), THREE.MathUtils.clamp(v.y, -hy + r, hy - r), THREE.MathUtils.clamp(v.z, -hz + r, hz - r));
    n.subVectors(v, q).normalize();
    v.copy(q).addScaledVector(n, r);
    p.setXYZ(i, v.x, v.y, v.z);
  }
  g.deleteAttribute("normal");
  g.deleteAttribute("uv");
  const m = mergeVertices(g, 1e-5);
  m.computeVertexNormals();
  return m;
}

// ---------- texture helpers ----------
export function canvasTexture(w, h, draw, { srgb = true, repeat = false } = {}) {
  const c = document.createElement("canvas");
  c.width = w;
  c.height = h;
  const ctx = c.getContext("2d");
  draw(ctx, w, h);
  const t = new THREE.CanvasTexture(c);
  if (srgb) t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = 16;
  if (repeat) t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.userData.canvas = c;
  return t;
}

/** Deterministic PRNG so renders are repeatable. */
export function rng(seed = 1) {
  let s = seed >>> 0;
  return () => {
    s = (s + 0x6d2b79f5) >>> 0;
    let t = s;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** Smooth 3D value noise in [0, 1] and a 4-octave fbm (for geometry displacement). */
export function noise3(x, y, z) {
  const h = (i, j, k) => {
    let n = (i * 374761393 + j * 668265263 + k * 1274126177) | 0;
    n = Math.imul(n ^ (n >>> 13), 1274126177);
    return ((n ^ (n >>> 16)) >>> 0) / 4294967295;
  };
  const xi = Math.floor(x), yi = Math.floor(y), zi = Math.floor(z);
  const s = (t) => t * t * (3 - 2 * t);
  const fx = s(x - xi), fy = s(y - yi), fz = s(z - zi);
  const l = (a, b, t) => a + (b - a) * t;
  return l(
    l(l(h(xi, yi, zi), h(xi + 1, yi, zi), fx), l(h(xi, yi + 1, zi), h(xi + 1, yi + 1, zi), fx), fy),
    l(l(h(xi, yi, zi + 1), h(xi + 1, yi, zi + 1), fx), l(h(xi, yi + 1, zi + 1), h(xi + 1, yi + 1, zi + 1), fx), fy),
    fz,
  );
}
export function fbm3(x, y, z, oct = 4) {
  let a = 0.5, s = 0, f = 1;
  for (let i = 0; i < oct; i++) { s += a * noise3(x * f, y * f, z * f); f *= 2.03; a *= 0.5; }
  return s / (1 - Math.pow(0.5, oct));
}

/** Brand leaf mark (two-lobed leaf) drawn at (x, y) with height s. */
export function drawLeafMark(ctx, x, y, s, color) {
  ctx.save();
  ctx.translate(x, y);
  ctx.scale(s / 100, s / 100);
  ctx.fillStyle = color;
  ctx.beginPath();
  ctx.moveTo(0, 50);
  ctx.bezierCurveTo(-38, 20, -34, -30, 0, -50);
  ctx.bezierCurveTo(34, -30, 38, 20, 0, 50);
  ctx.fill();
  ctx.strokeStyle = "rgba(255,255,255,0.85)";
  ctx.lineWidth = 5;
  ctx.lineCap = "round";
  ctx.beginPath();
  ctx.moveTo(0, 44);
  ctx.lineTo(0, -36);
  for (const k of [-1, 1]) for (const yy of [18, -4, -24]) { ctx.moveTo(0, yy + 10); ctx.quadraticCurveTo(k * 10, yy + 2, k * 20, yy - 6); }
  ctx.stroke();
  ctx.restore();
}

/** Text with letter spacing, centred. */
export function spacedText(ctx, text, x, y, spacing) {
  ctx.save();
  ctx.letterSpacing = `${spacing}px`;
  const w = ctx.measureText(text).width - spacing;
  const align = ctx.textAlign;
  ctx.textAlign = "left";
  const x0 = align === "center" ? x - w / 2 : align === "right" ? x - w : x;
  ctx.fillText(text, x0, y);
  ctx.restore();
}

// ---------- botanicals ----------
const leafTexCache = new Map();
export function leafTexture(base = "#5d8a4f", seed = 3) {
  const key = base + seed;
  if (leafTexCache.has(key)) return leafTexCache.get(key);
  const R = rng(seed);
  const t = canvasTexture(256, 1024, (ctx, w, h) => {
    // v along the leaf (bottom = stem), u across
    const g = ctx.createLinearGradient(0, h, 0, 0);
    const c = new THREE.Color(base);
    g.addColorStop(0, `#${c.clone().offsetHSL(0.01, -0.05, 0.02).getHexString()}`);
    g.addColorStop(0.6, base);
    g.addColorStop(1, `#${c.clone().offsetHSL(-0.01, 0.02, -0.04).getHexString()}`);
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, w, h);
    // mottling
    for (let i = 0; i < 500; i++) {
      ctx.fillStyle = `rgba(${R() < 0.5 ? "255,255,230" : "20,40,10"},${0.015 + R() * 0.025})`;
      ctx.beginPath();
      ctx.ellipse(R() * w, R() * h, 2 + R() * 10, 4 + R() * 26, 0, 0, 7);
      ctx.fill();
    }
    // lateral veins
    ctx.strokeStyle = "rgba(210,232,170,0.18)";
    ctx.lineWidth = 3;
    for (let k = 0; k < 9; k++) {
      const y0 = h * (0.92 - k * 0.095);
      for (const s of [-1, 1]) {
        ctx.beginPath();
        ctx.moveTo(w / 2, y0);
        ctx.quadraticCurveTo(w / 2 + s * w * 0.22, y0 - h * 0.05, w / 2 + s * w * 0.48, y0 - h * 0.14);
        ctx.stroke();
      }
    }
    // midrib
    const mg = ctx.createLinearGradient(0, h, 0, 0);
    mg.addColorStop(0, "rgba(215,235,180,0.55)");
    mg.addColorStop(1, "rgba(215,235,180,0.1)");
    ctx.fillStyle = mg;
    ctx.beginPath();
    ctx.moveTo(w / 2 - 7, h);
    ctx.lineTo(w / 2 + 7, h);
    ctx.lineTo(w / 2 + 1, 0);
    ctx.lineTo(w / 2 - 1, 0);
    ctx.fill();
  });
  leafTexCache.set(key, t);
  return t;
}

/**
 * Parametric leaf blade in local space: base at origin, tip along +y, face normal ~ +z.
 * fold: V-fold along midrib (z per unit |x|). arch: lengthwise bend (z at tip). twist in radians.
 */
export function leafGeometry({ length = 3, width = 1.2, fold = 0.25, arch = 0.3, twist = 0, widest = 0.4, nu = 28, nv = 12 } = {}) {
  const pos = [], uv = [], idx = [];
  const pw = Math.log(0.5) / Math.log(widest);
  for (let i = 0; i <= nu; i++) {
    const u = i / nu;
    const hw = (width / 2) * Math.pow(Math.sin(Math.PI * Math.pow(u, pw)), 0.85);
    for (let j = 0; j <= nv; j++) {
      const s = (j / nv) * 2 - 1;
      let x = s * hw;
      let y = u * length;
      let z = fold * Math.abs(x) + arch * u * u - 0.06 * width * Math.sin(Math.PI * u) * (1 - s * s);
      const a = twist * u;
      const xr = x * Math.cos(a) - z * Math.sin(a);
      const zr = x * Math.sin(a) + z * Math.cos(a);
      pos.push(xr, y, zr);
      uv.push(s * 0.5 + 0.5, u);
    }
  }
  for (let i = 0; i < nu; i++) for (let j = 0; j < nv; j++) {
    const a = i * (nv + 1) + j, b = a + nv + 1;
    idx.push(a, b, a + 1, b, b + 1, a + 1);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute("uv", new THREE.Float32BufferAttribute(uv, 2));
  g.setIndex(idx);
  g.computeVertexNormals();
  return g;
}

export function leafMaterial(base = "#5d8a4f", seed = 3) {
  return new THREE.MeshPhysicalMaterial({
    map: leafTexture(base, seed),
    roughness: 0.5,
    clearcoat: 0.5,
    clearcoatRoughness: 0.28,
    sheen: 0.15,
    sheenColor: new THREE.Color("#dfeccf"),
    sheenRoughness: 0.6,
    side: THREE.DoubleSide,
  });
}

// ---------- studio ----------
function softboxTexture() {
  // rectangular diffusion panel: flat centre, soft falloff near the frame, slightly hotter middle
  const N = 256;
  const data = new Uint8Array(N * N * 4);
  for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) {
    const u = (x + 0.5) / N * 2 - 1, v = (y + 0.5) / N * 2 - 1;
    const e = (d) => THREE.MathUtils.smoothstep(1 - d, 0, 0.14);
    const edge = e(Math.abs(u)) * e(Math.abs(v));
    const hot = 0.85 + 0.15 * Math.exp(-(u * u + v * v) * 1.5);
    const val = Math.round(255 * edge * hot);
    data.set([val, val, val, 255], (y * N + x) * 4);
  }
  const t = new THREE.DataTexture(data, N, N);
  t.needsUpdate = true;
  t.magFilter = t.minFilter = THREE.LinearFilter;
  return t;
}

function buildEnvironment(renderer, cfg) {
  const env = new THREE.Scene();
  // Room: vertical gradient, mint floor bounce, soft grey-white walls.
  const room = new THREE.Mesh(
    new THREE.SphereGeometry(40, 128, 64),
    new THREE.ShaderMaterial({
      uniforms: { top: { value: new THREE.Color(cfg.envTop) }, mid: { value: new THREE.Color(cfg.envMid) }, floor: { value: new THREE.Color(cfg.envFloor) } },
      vertexShader: "varying vec3 vDir; void main(){ vDir = normalize(position); gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }",
      fragmentShader: `uniform vec3 top; uniform vec3 mid; uniform vec3 floor; varying vec3 vDir;
        void main(){ float y = normalize(vDir).y; vec3 c = y > 0.0 ? mix(mid, top, pow(y, 0.7)) : mix(mid, floor, min(1.0, -y * 3.0)); gl_FragColor = vec4(c, 1.0); }`,
      side: THREE.BackSide,
      depthWrite: false,
    }),
  );
  env.add(room);
  const tex = softboxTexture();
  const box = (w, h, pos, intensity, tint = "#ffffff") => {
    const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), new THREE.MeshBasicMaterial({ map: tex, color: new THREE.Color(tint).multiplyScalar(intensity), side: THREE.DoubleSide }));
    m.position.set(...pos);
    m.lookAt(0, 0, 0);
    env.add(m);
  };
  for (const b of cfg.softboxes) box(...b);
  const pmrem = new THREE.PMREMGenerator(renderer);
  const rt = pmrem.fromScene(env, 0);
  pmrem.dispose();
  return rt.texture;
}

function buildBackground(cfg, toneFn) {
  const N = 256;
  const inner = invertToneMap(hexToLin(cfg.bgInner), toneFn, cfg.exposure);
  const outer = invertToneMap(hexToLin(cfg.bgOuter), toneFn, cfg.exposure);
  const ci = hexToLin(cfg.bgInner), co = hexToLin(cfg.bgOuter);
  const data = new Float32Array(N * 4);
  for (let i = 0; i < N; i++) {
    const t = i / (N - 1);
    const s = t * t * (3 - 2 * t);
    // interpolate in display space, then invert for each stop
    const disp = ci.map((c, k) => {
      const a = Math.pow(c, 1 / 2.2), b = Math.pow(co[k], 1 / 2.2);
      return Math.pow(a + (b - a) * s, 2.2);
    });
    const lin = i === 0 ? inner : i === N - 1 ? outer : invertToneMap(disp, toneFn, cfg.exposure);
    data.set([...lin, 1], i * 4);
  }
  const lut = new THREE.DataTexture(data, N, 1, THREE.RGBAFormat, THREE.FloatType);
  lut.minFilter = lut.magFilter = THREE.LinearFilter;
  lut.needsUpdate = true;
  const mat = new THREE.ShaderMaterial({
    uniforms: { lut: { value: lut }, res: { value: new THREE.Vector2(1, 1) }, center: { value: new THREE.Vector2(...cfg.bgCenter) }, radius: { value: cfg.bgRadius } },
    vertexShader: "void main(){ gl_Position = vec4(position.xy, 0.99999, 1.0); }",
    fragmentShader: `uniform sampler2D lut; uniform vec2 res; uniform vec2 center; uniform float radius;
      void main(){ vec2 uv = gl_FragCoord.xy / res; float t = clamp(length(uv - center) / radius, 0.0, 1.0);
        gl_FragColor = vec4(texture2D(lut, vec2(t * 0.99609 + 0.00195, 0.5)).rgb, 1.0); }`,
    depthWrite: false,
  });
  const quad = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), mat);
  quad.frustumCulled = false;
  quad.renderOrder = -1000;
  return quad;
}

/**
 * Contact shadow (drei ContactShadows technique): render the scene from below the floor with a
 * "closeness to floor" material, blur it, and lay it on the floor as a soft multiply-style decal.
 */
function contactShadow(renderer, scene, root, cfg) {
  const box = new THREE.Box3().setFromObject(root);
  const size = Math.max(box.max.x - box.min.x, box.max.z - box.min.z) * 1.6;
  const cx = (box.min.x + box.max.x) / 2, cz = (box.min.z + box.max.z) / 2;
  const res = 1024;
  const opts = { type: THREE.HalfFloatType };
  const rtA = new THREE.WebGLRenderTarget(res, res, opts);
  const rtB = new THREE.WebGLRenderTarget(res, res, opts);
  const cam = new THREE.OrthographicCamera(-size / 2, size / 2, size / 2, -size / 2, 0, cfg.contactHeight);
  cam.position.set(cx, 0, cz);
  cam.up.set(0, 0, 1); // image right = +x, image up = +z (plane v runs toward -z, so v is flipped below)
  cam.lookAt(cx, 1, cz);
  cam.updateMatrixWorld(true);
  const depthMat = new THREE.ShaderMaterial({
    uniforms: { h: { value: cfg.contactHeight } },
    vertexShader: "varying float vY; void main(){ vec4 w = modelMatrix * vec4(position, 1.0); vY = w.y; gl_Position = projectionMatrix * viewMatrix * w; }",
    fragmentShader: "uniform float h; varying float vY; void main(){ float t = clamp(vY / h, 0.0, 1.0); gl_FragColor = vec4(vec3(pow(1.0 - t, 1.6)), 1.0); }",
    side: THREE.DoubleSide,
  });
  // closest-to-floor wins: use max blending on the "darkness" value
  depthMat.blending = THREE.CustomBlending;
  depthMat.blendEquation = THREE.MaxEquation;
  depthMat.blendSrc = THREE.OneFactor;
  depthMat.blendDst = THREE.OneFactor;
  depthMat.depthTest = false;
  depthMat.depthWrite = false;
  const hidden = [];
  scene.traverse((o) => { if ((o.isMesh && !isDescendant(o, root)) && o.visible) { hidden.push(o); o.visible = false; } });
  const prevOverride = scene.overrideMaterial;
  const prevEnv = scene.environment;
  scene.overrideMaterial = depthMat;
  renderer.setRenderTarget(rtA);
  renderer.setClearColor(0x000000, 1);
  renderer.clear();
  renderer.render(scene, cam);
  scene.overrideMaterial = prevOverride;
  scene.environment = prevEnv;
  hidden.forEach((o) => (o.visible = true));
  // separable gaussian blur, a few passes
  const blur = new THREE.ShaderMaterial({
    uniforms: { t: { value: null }, dir: { value: new THREE.Vector2() } },
    vertexShader: "varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }",
    fragmentShader: `uniform sampler2D t; uniform vec2 dir; varying vec2 vUv;
      void main(){ vec4 s = vec4(0.0); float wsum = 0.0;
        for (int i = -12; i <= 12; i++) { float w = exp(-float(i*i) / 50.0); s += texture2D(t, vUv + dir * float(i)) * w; wsum += w; }
        gl_FragColor = s / wsum; }`,
    depthTest: false,
  });
  const q = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), blur);
  const qs = new THREE.Scene();
  qs.add(q);
  const qc = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
  const rtC = new THREE.WebGLRenderTarget(res, res, opts);
  const pass = (src, dst, dx, dy) => {
    blur.uniforms.t.value = src.texture;
    blur.uniforms.dir.value.set(dx / res, dy / res);
    renderer.setRenderTarget(dst);
    renderer.render(qs, qc);
  };
  // tight contact (rtB), then a wide ambient falloff (rtA) built from it
  pass(rtA, rtC, cfg.contactBlur, 0);
  pass(rtC, rtB, 0, cfg.contactBlur);
  pass(rtB, rtC, cfg.contactBlur * 5, 0);
  pass(rtC, rtA, 0, cfg.contactBlur * 5);
  renderer.setRenderTarget(null);
  const mat = new THREE.ShaderMaterial({
    uniforms: { tight: { value: rtB.texture }, wide: { value: rtA.texture }, color: { value: new THREE.Color(cfg.shadowColor) }, opacity: { value: cfg.contactOpacity }, mixW: { value: cfg.contactWide } },
    vertexShader: "varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }",
    fragmentShader: `uniform sampler2D tight; uniform sampler2D wide; uniform vec3 color; uniform float opacity; uniform float mixW; varying vec2 vUv;
      void main(){ vec2 uv = vec2(vUv.x, 1.0 - vUv.y); float a = mix(texture2D(tight, uv).r, texture2D(wide, uv).r, mixW) * opacity; gl_FragColor = vec4(color, a); }`,
    transparent: true,
    depthWrite: false,
    polygonOffset: true,
    polygonOffsetFactor: -1,
  });
  const plane = new THREE.Mesh(new THREE.PlaneGeometry(size, size), mat);
  plane.rotation.x = -Math.PI / 2;
  plane.position.set(cx, 0.002, cz);
  plane.userData.noFrame = true;
  plane.renderOrder = -1;
  return plane;
}
function isDescendant(o, root) {
  for (let p = o; p; p = p.parent) if (p === root) return true;
  return false;
}

/** Fit camera: object's projected bounds fill `fill` of the frame (max of w/h), centred at ndc (0, yOffset). */
export function frameCamera(camera, root, { fill = 0.66, elev = 18, azim = 0, yOffset = 0, xOffset = 0 } = {}) {
  root.updateMatrixWorld(true);
  const pts = [];
  root.traverse((o) => {
    if (!o.isMesh || o.userData.noFrame) return;
    const p = o.geometry.attributes.position;
    const step = Math.max(1, Math.floor(p.count / 3000));
    const v = new THREE.Vector3();
    const m = new THREE.Matrix4();
    const instances = o.isInstancedMesh ? o.count : 1;
    for (let k = 0; k < instances; k += o.isInstancedMesh ? Math.max(1, Math.floor(instances / 60)) : 1) {
      if (o.isInstancedMesh) { o.getMatrixAt(k, m); m.premultiply(o.matrixWorld); } else m.copy(o.matrixWorld);
      for (let i = 0; i < p.count; i += step) pts.push(v.fromBufferAttribute(p, i).applyMatrix4(m).clone());
    }
  });
  const box = new THREE.Box3().setFromPoints(pts);
  const target = box.getCenter(new THREE.Vector3());
  const e = THREE.MathUtils.degToRad(elev), a = THREE.MathUtils.degToRad(azim);
  const dir = new THREE.Vector3(Math.sin(a) * Math.cos(e), Math.sin(e), Math.cos(a) * Math.cos(e));
  let dist = box.getSize(new THREE.Vector3()).length() * 2;
  const tanH = Math.tan(THREE.MathUtils.degToRad(camera.fov / 2));
  for (let it = 0; it < 30; it++) {
    camera.position.copy(target).addScaledVector(dir, dist);
    camera.lookAt(target);
    camera.updateMatrixWorld(true);
    let x0 = Infinity, x1 = -Infinity, y0 = Infinity, y1 = -Infinity;
    const v = new THREE.Vector3();
    for (const p of pts) {
      v.copy(p).project(camera);
      x0 = Math.min(x0, v.x); x1 = Math.max(x1, v.x); y0 = Math.min(y0, v.y); y1 = Math.max(y1, v.y);
    }
    const ext = Math.max(x1 - x0, y1 - y0) / 2;
    const cx = (x0 + x1) / 2 - xOffset, cy = (y0 + y1) / 2 - yOffset;
    const right = new THREE.Vector3().setFromMatrixColumn(camera.matrixWorld, 0);
    const up = new THREE.Vector3().setFromMatrixColumn(camera.matrixWorld, 1);
    target.addScaledVector(right, cx * dist * tanH * 0.9).addScaledVector(up, cy * dist * tanH * 0.9);
    dist *= Math.pow(ext / fill, 0.9);
  }
  return { target, dist };
}

const DEFAULTS = {
  exposure: 1.0,
  bgInner: "#EFFBF8",
  bgOuter: "#D3EFE8",
  bgCenter: [0.5, 0.56],
  bgRadius: 0.78,
  envTop: "#4d5856",
  envMid: "#39423f",
  envFloor: "#8aa39c", // lit mint sweep bouncing light back up
  envIntensity: 1.0,
  // [w, h, position, intensity, tint]
  softboxes: [
    [14, 14, [-14, 16, 12], 16, "#fffaf2"], // key, top-left front
    [16, 10, [18, 4, 14], 2, "#f4fbff"], // fill, right
    [4, 18, [12, 8, -16], 20, "#ffffff"], // rim right-back strip
    [4, 18, [-14, 8, -14], 13, "#ffffff"], // rim left-back strip
    [12, 12, [0, 26, 0], 7, "#ffffff"], // top
    [2.6, 16, [-16, 3, 9], 26, "#ffffff"], // vertical strip, left-front: highlight streaks on bottles
    [2.6, 16, [16, 3, 6], 13, "#ffffff"], // vertical strip, right-front
  ],
  keyDir: [-0.7, 0.9, 0.35],
  keyIntensity: 0.8,
  keySoftness: 0.08, // disc radius / distance
  skyIntensity: 0, // sky samples only cast floor occlusion (a moving point light would leave specular dots)
  keyProb: 0.55,
  minSkyY: 0.8, // sky samples stay within ~45 degrees of vertical
  shadowOpacity: 0.8,
  shadowColor: "#1d4a40",
  contactOpacity: 0.9,
  contactHeight: 2.0, // cm above the floor that still darkens it
  contactBlur: 2, // texel step of the tight blur kernel (25 taps); the wide one is 5x
  contactWide: 0.5, // mix between tight contact and wide ambient falloff
  fov: 26,
};

export async function renderProduct(mod, { frames = 48, ss = 2, quality = 0.9, override = {} }) {
  const cfg = { ...DEFAULTS, ...(mod.studio ?? {}), ...override };
  const W = OUT * ss;
  const canvas = document.createElement("canvas");
  document.body.appendChild(canvas);
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: false, preserveDrawingBuffer: true, powerPreference: "high-performance" });
  renderer.setPixelRatio(1);
  renderer.setSize(OUT, OUT, false);
  renderer.toneMapping = THREE.NoToneMapping; // tone mapping happens in our own final pass
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFShadowMap;

  const scene = new THREE.Scene();
  scene.environment = buildEnvironment(renderer, cfg);
  scene.environmentIntensity = cfg.envIntensity;
  const bg = buildBackground(cfg, toneJS);
  bg.material.uniforms.res.value.set(W, W);
  scene.add(bg);

  const built = await mod.build({ THREE, scene, renderer });
  const root = built.root;
  root.traverse((o) => { if (o.isMesh && o.userData.shadow !== false) { o.castShadow = true; o.receiveShadow = true; } });
  scene.add(root);

  const floor = new THREE.Mesh(new THREE.PlaneGeometry(400, 400), new THREE.ShadowMaterial({ color: cfg.shadowColor, opacity: cfg.shadowOpacity }));
  floor.rotation.x = -Math.PI / 2;
  floor.receiveShadow = true;
  floor.userData.noFrame = true;
  scene.add(floor);
  if (cfg.contactOpacity > 0) scene.add(contactShadow(renderer, scene, root, cfg));

  const camera = new THREE.PerspectiveCamera(cfg.fov, 1, 0.5, 2000);
  const { target } = frameCamera(camera, root, { ...(built.frame ?? {}), ...(cfg.frame ?? {}) });

  // Shadow light, re-positioned every frame.
  const bounds = new THREE.Box3().setFromObject(root);
  const bsize = bounds.getSize(new THREE.Vector3()).length();
  const bcenter = bounds.getCenter(new THREE.Vector3());
  bcenter.y = Math.max(0, bounds.min.y);
  const light = new THREE.DirectionalLight(0xffffff, 1);
  light.castShadow = true;
  light.shadow.mapSize.set(4096, 4096);
  const sc = light.shadow.camera;
  sc.left = sc.bottom = -bsize * 1.1;
  sc.right = sc.top = bsize * 1.1;
  sc.near = 1;
  sc.far = bsize * 8;
  sc.updateProjectionMatrix();
  light.shadow.bias = -0.0002;
  light.shadow.normalBias = cfg.normalBias ?? 0.02;
  light.shadow.radius = 3;
  light.target.position.copy(bcenter);
  scene.add(light, light.target);
  const keyDir = new THREE.Vector3(...cfg.keyDir).normalize();
  const lightDist = bsize * 4;
  const halton = (i, b) => { let f = 1, r = 0; while (i > 0) { f /= b; r += f * (i % b); i = Math.floor(i / b); } return r; };
  let keyFrames = 0;
  // Low-discrepancy (Halton) sampling: the key light fills a disc (area light), the sky light a
  // cosine-weighted cap above minSkyY (soft contact occlusion). One light per frame keeps shaders fixed.
  const placeLight = (i) => {
    const isKey = halton(i + 1, 5) < cfg.keyProb;
    const a = halton(i + 1, 7), b = halton(i + 1, 11);
    let d;
    if (isKey) {
      keyFrames++;
      const t1 = new THREE.Vector3(0, 1, 0).cross(keyDir).normalize();
      const t2 = keyDir.clone().cross(t1);
      const r = Math.sqrt(a) * cfg.keySoftness, th = b * Math.PI * 2;
      d = keyDir.clone().addScaledVector(t1, r * Math.cos(th)).addScaledVector(t2, r * Math.sin(th)).normalize();
      light.intensity = cfg.keyIntensity / cfg.keyProb;
    } else {
      const u = a * (1 - cfg.minSkyY * cfg.minSkyY), th = b * Math.PI * 2;
      const r = Math.sqrt(u);
      d = new THREE.Vector3(r * Math.cos(th), Math.sqrt(1 - u), r * Math.sin(th));
      light.intensity = cfg.skyIntensity / (1 - cfg.keyProb);
      light.visible = true;
    }
    light.position.copy(bcenter).addScaledVector(d, lightDist);
  };

  // Accumulation targets.
  const frameRT = new THREE.WebGLRenderTarget(W, W, { type: THREE.HalfFloatType, samples: cfg.msaa ?? 0 });
  const accOpts = { type: THREE.FloatType, depthBuffer: false, minFilter: THREE.LinearFilter, magFilter: THREE.LinearFilter };
  let accA = new THREE.WebGLRenderTarget(W, W, accOpts);
  let accB = new THREE.WebGLRenderTarget(W, W, accOpts);
  const quadCam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
  const quadGeo = new THREE.PlaneGeometry(2, 2);
  const blendMat = new THREE.ShaderMaterial({
    uniforms: { tNew: { value: null }, tAcc: { value: null }, w: { value: 1 } },
    vertexShader: "varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }",
    fragmentShader: "uniform sampler2D tNew; uniform sampler2D tAcc; uniform float w; varying vec2 vUv; void main(){ gl_FragColor = mix(texture2D(tAcc, vUv), texture2D(tNew, vUv), w); }",
    depthTest: false,
    depthWrite: false,
  });
  const blendScene = new THREE.Scene();
  blendScene.add(new THREE.Mesh(quadGeo, blendMat));

  const syncBuf = new Float32Array(4);
  const t0 = performance.now();
  for (let i = 0; i < frames; i++) {
    camera.setViewOffset(W, W, halton(i + 1, 2) - 0.5, halton(i + 1, 3) - 0.5, W, W);
    placeLight(i);
    renderer.setRenderTarget(frameRT);
    if (cfg.double) renderer.render(scene, camera);
    renderer.render(scene, camera);
    blendMat.uniforms.tNew.value = frameRT.texture;
    blendMat.uniforms.tAcc.value = accA.texture;
    blendMat.uniforms.w.value = 1 / (i + 1);
    renderer.setRenderTarget(accB);
    renderer.render(blendScene, quadCam);
    if (cfg.sync) renderer.readRenderTargetPixels(accB, 0, 0, 1, 1, syncBuf);
    [accA, accB] = [accB, accA];
    if (i % 4 === 3) await new Promise((r) => setTimeout(r, 0));
  }
  // Final: tone map + sRGB + dither, box-filtered down to OUT.
  const finalScene = new THREE.Scene();
  finalScene.add(new THREE.Mesh(quadGeo, new THREE.ShaderMaterial({
    uniforms: { tAcc: { value: accA.texture }, exposure: { value: cfg.exposure } },
    vertexShader: "varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }",
    fragmentShader: `uniform sampler2D tAcc; uniform float exposure; varying vec2 vUv; ${TONE_GLSL}
      float hash(vec2 p){ return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453); }
      void main(){ vec3 c = toSRGB(studioTone(texture2D(tAcc, vUv).rgb));
        float n = hash(gl_FragCoord.xy) + hash(gl_FragCoord.xy + 17.31) - 1.0; // triangular dither
        gl_FragColor = vec4(c + n / 255.0, 1.0); }`,
    depthTest: false,
  })));
  renderer.setRenderTarget(null);
  renderer.render(finalScene, quadCam);
  const ms = performance.now() - t0;
  const webp = canvas.toDataURL("image/webp", quality);
  const png = canvas.toDataURL("image/png");
  return { webp, png, info: `${keyFrames} key / ${frames} frames @ ${W}px in ${(ms / 1000).toFixed(1)}s (${renderer.capabilities.isWebGL2 ? "webgl2" : "webgl1"})` };
}
