// Procedural material helpers: object-space noise injected into MeshPhysicalMaterial, so meshes
// need no UVs (soap speckles, bamboo grain, ...).
import * as THREE from "three";

export const NOISE_GLSL = `
  float h31(vec3 p){ p = fract(p * 0.3183099 + 0.1); p *= 17.0; return fract(p.x * p.y * p.z * (p.x + p.y + p.z)); }
  float vnoise(vec3 x){ vec3 i = floor(x); vec3 f = fract(x); f = f * f * (3.0 - 2.0 * f);
    return mix(mix(mix(h31(i), h31(i + vec3(1,0,0)), f.x), mix(h31(i + vec3(0,1,0)), h31(i + vec3(1,1,0)), f.x), f.y),
               mix(mix(h31(i + vec3(0,0,1)), h31(i + vec3(1,0,1)), f.x), mix(h31(i + vec3(0,1,1)), h31(i + vec3(1,1,1)), f.x), f.y), f.z); }
  float fbm(vec3 p){ float a = 0.5, s = 0.0; for (int i = 0; i < 5; i++) { s += a * vnoise(p); p *= 2.03; a *= 0.5; } return s; }`;

const glslType = (v) => (typeof v === "number" ? "float" : v.isColor || v.isVector3 ? "vec3" : v.isVector2 ? "vec2" : "float");

/**
 * Inject object-space procedural shading. `body` is GLSL that may read `vec3 p` (object position)
 * and write `vec3 col` (base colour, starts as diffuseColor.rgb) and `float rough`.
 */
export function proceduralMaterial(mat, body, uniforms = {}) {
  mat.onBeforeCompile = (sh) => {
    Object.assign(sh.uniforms, uniforms);
    const decl = Object.entries(uniforms).map(([k, u]) => `uniform ${glslType(u.value)} ${k};`).join("\n");
    sh.vertexShader = sh.vertexShader
      .replace("#include <common>", "#include <common>\nvarying vec3 vObjPos;")
      .replace("#include <begin_vertex>", "#include <begin_vertex>\nvObjPos = position;");
    sh.fragmentShader = sh.fragmentShader
      .replace("#include <common>", `#include <common>\nvarying vec3 vObjPos;\n${decl}\n${NOISE_GLSL}`)
      .replace("void main() {", "void main() {\n  float procRough = roughness;")
      .replace("#include <map_fragment>", `#include <map_fragment>\n  { vec3 p = vObjPos; vec3 col = diffuseColor.rgb; float rough = roughness;\n${body}\n  diffuseColor.rgb = col; procRough = rough; }`)
      .replace("#include <roughnessmap_fragment>", "#include <roughnessmap_fragment>\n  roughnessFactor = procRough;");
  };
  mat.customProgramCacheKey = () => body;
  return mat;
}

/** Bamboo / light wood: fibres along `axis`, occasional darker growth nodes. */
export function bambooMaterial({ seed = 0, axis = "x", base = "#d8b27a", dark = "#a8763f", nodeEvery = 6.5 } = {}) {
  const along = axis, a = along === "x" ? "p.x" : along === "y" ? "p.y" : "p.z";
  const across = along === "x" ? "p.yz" : along === "y" ? "p.xz" : "p.xy";
  const m = new THREE.MeshPhysicalMaterial({ color: base, roughness: 0.55, clearcoat: 0.35, clearcoatRoughness: 0.45, sheen: 0.2, sheenRoughness: 0.5 });
  return proceduralMaterial(
    m,
    `
    vec2 q = ${across} * vec2(9.0, 26.0) + seed;
    float warp = fbm(vec3(${a} * 0.6, q * 0.15)) * 2.0;
    float fib = fbm(vec3(${a} * 0.35 + seed, q.x * 0.6 + warp, q.y * 0.6));
    float streak = smoothstep(0.35, 0.75, fbm(vec3(${a} * 0.08, q.x * 1.6 + seed, q.y * 1.6)));
    float lines = pow(abs(sin((q.y + warp * 3.0) * 1.3)), 18.0);
    float node = exp(-pow(mod(${a} + seed * 3.1, nodeEvery) - nodeEvery * 0.5, 2.0) * 22.0);
    vec3 c0 = baseC * (0.86 + 0.28 * fib);
    c0 = mix(c0, darkC, 0.28 * streak + 0.35 * lines + 0.55 * node);
    col = c0;
    rough = 0.5 + 0.15 * fib;`,
    { seed: { value: seed }, baseC: { value: new THREE.Color(base) }, darkC: { value: new THREE.Color(dark) }, nodeEvery: { value: nodeEvery } },
  );
}
