/**
 * Puts a background behind Xana's face: Tavus renders her on a solid green screen
 * (`apply_greenscreen`, roughly rgb(0, 255, 155)), and this keys the green out on the GPU and
 * draws the chosen background in its place, every video frame.
 *
 * The key is how much greener a pixel is than its red and blue, with a soft edge so hair
 * doesn't look cut out, and the leftover green fringe is pulled back to neutral ("despill").
 * The numbers were tuned on a real frame of the Rose face (2026-09-30).
 */

const VERTEX = `
attribute vec2 a_pos;
varying vec2 v_uv;
void main() {
  v_uv = vec2(a_pos.x * 0.5 + 0.5, 0.5 - a_pos.y * 0.5);
  gl_Position = vec4(a_pos, 0.0, 1.0);
}`;

const FRAGMENT = `
precision mediump float;
uniform sampler2D u_video;
uniform sampler2D u_bg;
varying vec2 v_uv;
void main() {
  vec3 c = texture2D(u_video, v_uv).rgb;
  float k = c.g - max(c.r, c.b * 0.85);
  float a = clamp(1.0 - (k - 0.12) / 0.23, 0.0, 1.0);
  c.g = min(c.g, max(c.r, c.b));
  vec3 bg = texture2D(u_bg, v_uv).rgb;
  gl_FragColor = vec4(mix(bg, c, a), 1.0);
}`;

export type GreenScreen = {
  /** Draw the current video frame over the background. */
  render: () => void;
  setBackground: (image: HTMLImageElement) => void;
  dispose: () => void;
};

/** null when the browser has no WebGL; the caller then shows the plain video. */
export function createGreenScreen(canvas: HTMLCanvasElement, video: HTMLVideoElement): GreenScreen | null {
  const gl = canvas.getContext("webgl", { premultipliedAlpha: false, preserveDrawingBuffer: false });
  if (!gl) return null;

  const shader = (type: number, src: string) => {
    const s = gl.createShader(type)!;
    gl.shaderSource(s, src);
    gl.compileShader(s);
    return gl.getShaderParameter(s, gl.COMPILE_STATUS) ? s : null;
  };
  const vs = shader(gl.VERTEX_SHADER, VERTEX);
  const fs = shader(gl.FRAGMENT_SHADER, FRAGMENT);
  if (!vs || !fs) return null;
  const program = gl.createProgram()!;
  gl.attachShader(program, vs);
  gl.attachShader(program, fs);
  gl.linkProgram(program);
  if (!gl.getProgramParameter(program, gl.LINK_STATUS)) return null;
  gl.useProgram(program);

  const quad = gl.createBuffer();
  gl.bindBuffer(gl.ARRAY_BUFFER, quad);
  gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW);
  const pos = gl.getAttribLocation(program, "a_pos");
  gl.enableVertexAttribArray(pos);
  gl.vertexAttribPointer(pos, 2, gl.FLOAT, false, 0, 0);

  const texture = (unit: number, name: string) => {
    const t = gl.createTexture()!;
    gl.activeTexture(gl.TEXTURE0 + unit);
    gl.bindTexture(gl.TEXTURE_2D, t);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    // One pixel until the real image arrives.
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGB, 1, 1, 0, gl.RGB, gl.UNSIGNED_BYTE, new Uint8Array([243, 233, 220]));
    gl.uniform1i(gl.getUniformLocation(program, name), unit);
    return t;
  };
  const videoTex = texture(0, "u_video");
  const bgTex = texture(1, "u_bg");

  return {
    render() {
      if (video.readyState < 2 || !video.videoWidth) return;
      if (canvas.width !== video.videoWidth || canvas.height !== video.videoHeight) {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
      }
      gl.viewport(0, 0, canvas.width, canvas.height);
      gl.activeTexture(gl.TEXTURE0);
      gl.bindTexture(gl.TEXTURE_2D, videoTex);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGB, gl.RGB, gl.UNSIGNED_BYTE, video);
      gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
    },
    setBackground(image) {
      gl.activeTexture(gl.TEXTURE1);
      gl.bindTexture(gl.TEXTURE_2D, bgTex);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGB, gl.RGB, gl.UNSIGNED_BYTE, image);
    },
    dispose() {
      gl.deleteTexture(videoTex);
      gl.deleteTexture(bgTex);
      gl.deleteBuffer(quad);
      gl.deleteProgram(program);
    },
  };
}
