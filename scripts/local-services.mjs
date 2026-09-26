// Runs PostgreSQL, OpenSearch, and Qdrant directly on this machine, without containers.
//   node scripts/local-services.mjs up | down | status
// Uses an installed PostgreSQL (PG_BIN, or the newest C:\Program Files\PostgreSQL\<n>\bin,
// or pg_ctl on PATH) with a private data folder, and downloads OpenSearch and Qdrant on first use.
// Everything lives in LOCAL_SERVICES_DIR (default %LOCALAPPDATA%\ai-commerce or
// ~/.local/share/ai-commerce), outside the repo. Redis, Temporal, and telemetry are not
// needed to run the app, so they stay in infra/compose.yaml.
import { spawn, spawnSync } from "node:child_process";
import { appendFileSync, existsSync, mkdirSync, openSync, readdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { createWriteStream } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";
import { Readable } from "node:stream";
import { pipeline } from "node:stream/promises";

const isWindows = process.platform === "win32";
const OPENSEARCH_VERSION = "3.8.0";
const QDRANT_VERSION = "1.19.1";
const QDRANT_PORT = "6333";
const PG_PORT = "5432";
const DATABASES = ["commerce", "commerce_test"];

const dir =
  process.env.LOCAL_SERVICES_DIR ??
  (isWindows ? join(process.env.LOCALAPPDATA, "ai-commerce") : join(homedir(), ".local", "share", "ai-commerce"));
const pgData = join(dir, "pgdata");
const pgLog = join(dir, "postgres.log");
const osHome = join(dir, `opensearch-${OPENSEARCH_VERSION}`);
const osLog = join(dir, "opensearch.log");
const osPidFile = join(dir, "opensearch.pid");
const qdHome = join(dir, `qdrant-${QDRANT_VERSION}`);
const qdStorage = join(dir, "qdrant-storage");
const qdLog = join(dir, "qdrant.log");
const qdPidFile = join(dir, "qdrant.pid");

const exe = (name) => (isWindows ? `${name}.exe` : name);
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

function pgBin() {
  if (process.env.PG_BIN) return process.env.PG_BIN;
  const root = "C:\\Program Files\\PostgreSQL";
  if (isWindows && existsSync(root)) {
    const versions = readdirSync(root).filter((v) => existsSync(join(root, v, "bin", "pg_ctl.exe")));
    versions.sort((a, b) => Number(b) - Number(a));
    if (versions.length) return join(root, versions[0], "bin");
  }
  return ""; // rely on PATH
}

function pg(tool, args, options = {}) {
  const bin = pgBin();
  return spawnSync(bin ? join(bin, exe(tool)) : tool, args, {
    encoding: "utf8",
    env: { ...process.env, PGPASSWORD: "commerce" },
    ...options,
  });
}

const pgReady = () => pg("pg_isready", ["-h", "localhost", "-p", PG_PORT], { stdio: "ignore" }).status === 0;

async function postgresUp() {
  if (!existsSync(pgData)) {
    console.log(`Creating a PostgreSQL data folder in ${pgData}`);
    const pwfile = join(dir, "pwfile");
    writeFileSync(pwfile, "commerce");
    const init = pg("initdb", ["-D", pgData, "-U", "commerce", `--pwfile=${pwfile}`, "--auth=scram-sha-256", "-E", "UTF8", "--locale=C"]);
    rmSync(pwfile);
    if (init.status !== 0) throw new Error(`initdb failed:\n${init.stderr || init.error}`);
  }
  if (pgReady()) {
    console.log(`PostgreSQL: already accepting connections on :${PG_PORT}`);
  } else {
    // stdio "ignore": postgres inherits pg_ctl's handles, and a pipe here would never close.
    const start = pg("pg_ctl", ["-D", pgData, "-l", pgLog, "-o", `-p ${PG_PORT}`, "-w", "start"], { stdio: "ignore" });
    if (start.status !== 0) throw new Error(`PostgreSQL didn't start; see ${pgLog}`);
    console.log(`PostgreSQL: started on :${PG_PORT} (log: ${pgLog})`);
  }
  const existing = pg("psql", ["-h", "localhost", "-p", PG_PORT, "-U", "commerce", "-d", "postgres", "-tAc", "select datname from pg_database"]);
  if (existing.status !== 0) throw new Error(`Can't connect as commerce:\n${existing.stderr}`);
  for (const db of DATABASES) {
    if (!existing.stdout.split(/\r?\n/).includes(db)) {
      pg("psql", ["-h", "localhost", "-p", PG_PORT, "-U", "commerce", "-d", "postgres", "-c", `CREATE DATABASE ${db}`]);
      console.log(`PostgreSQL: created database ${db}`);
    }
  }
}

function postgresDown() {
  if (!existsSync(pgData)) return;
  const stop = pg("pg_ctl", ["-D", pgData, "-m", "fast", "-w", "stop"], { stdio: "ignore" });
  console.log(stop.status === 0 ? "PostgreSQL: stopped" : "PostgreSQL: not running");
}

async function openSearchHealthy() {
  try {
    const res = await fetch("http://127.0.0.1:9200/_cluster/health", { signal: AbortSignal.timeout(2000) });
    return res.ok;
  } catch {
    return false;
  }
}

async function installOpenSearch() {
  const file = isWindows ? `opensearch-${OPENSEARCH_VERSION}-windows-x64.zip` : `opensearch-${OPENSEARCH_VERSION}-linux-x64.tar.gz`;
  const archive = join(dir, file);
  if (!existsSync(archive)) {
    const url = `https://artifacts.opensearch.org/releases/bundle/opensearch/${OPENSEARCH_VERSION}/${file}`;
    console.log(`Downloading ${url} (about 1 GB)`);
    const res = await fetch(url);
    if (!res.ok) throw new Error(`Download failed: ${res.status}`);
    await pipeline(Readable.fromWeb(res.body), createWriteStream(archive));
  }
  // bsdtar (bundled with Windows 10+) extracts zip files too.
  const untar = spawnSync("tar", ["-xf", archive, "-C", dir], { stdio: "inherit" });
  if (untar.status !== 0) throw new Error("Couldn't extract OpenSearch");
}

function configureOpenSearch() {
  const config = join(osHome, "config", "opensearch.yml");
  if (readFileSync(config, "utf8").includes("cluster.name: ai-commerce")) return;
  appendFileSync(
    config,
    [
      "",
      "# ai-commerce local development: one node, localhost only, no security plugin",
      "# (same as infra/compose.yaml).",
      "cluster.name: ai-commerce",
      "discovery.type: single-node",
      "network.host: 127.0.0.1",
      "http.port: 9200",
      "plugins.security.disabled: true",
      "# Disk limits as free space, not percent: on a large, nearly full disk the percent",
      "# defaults block index creation even with plenty of room left.",
      "cluster.routing.allocation.disk.watermark.low: 3gb",
      "cluster.routing.allocation.disk.watermark.high: 2gb",
      "cluster.routing.allocation.disk.watermark.flood_stage: 1gb",
      "",
    ].join("\n"),
  );
}

async function openSearchUp() {
  if (await openSearchHealthy()) {
    console.log("OpenSearch: already running on :9200");
    return;
  }
  if (!existsSync(osHome)) await installOpenSearch();
  configureOpenSearch();
  const log = openSync(osLog, "a");
  const bin = join(osHome, "bin", isWindows ? "opensearch.bat" : "opensearch");
  const child = spawn(isWindows ? "cmd.exe" : bin, isWindows ? ["/c", bin, "-p", osPidFile] : ["-p", osPidFile], {
    detached: true,
    stdio: ["ignore", log, log],
    windowsHide: true,
    env: { ...process.env, OPENSEARCH_JAVA_OPTS: "-Xms1g -Xmx1g" },
  });
  child.unref();
  process.stdout.write("OpenSearch: starting");
  for (let i = 0; i < 90; i++) {
    if (await openSearchHealthy()) {
      console.log(` ... ready on :9200 (log: ${osLog})`);
      return;
    }
    process.stdout.write(".");
    await sleep(2000);
  }
  throw new Error(`OpenSearch didn't become healthy; see ${osLog}`);
}

function openSearchDown() {
  if (!existsSync(osPidFile)) {
    console.log("OpenSearch: not running");
    return;
  }
  const pid = readFileSync(osPidFile, "utf8").trim();
  if (isWindows) spawnSync("taskkill", ["/PID", pid, "/T", "/F"], { stdio: "ignore" });
  else spawnSync("kill", [pid], { stdio: "ignore" });
  rmSync(osPidFile, { force: true });
  console.log("OpenSearch: stopped");
}

async function qdrantReady() {
  try {
    const res = await fetch(`http://127.0.0.1:${QDRANT_PORT}/readyz`, { signal: AbortSignal.timeout(2000) });
    return res.ok;
  } catch {
    return false;
  }
}

async function installQdrant() {
  const file = isWindows ? "qdrant-x86_64-pc-windows-msvc.zip" : "qdrant-x86_64-unknown-linux-gnu.tar.gz";
  const archive = join(dir, `qdrant-${QDRANT_VERSION}-${file}`);
  if (!existsSync(archive)) {
    const url = `https://github.com/qdrant/qdrant/releases/download/v${QDRANT_VERSION}/${file}`;
    console.log(`Downloading ${url} (about 30 MB)`);
    const res = await fetch(url);
    if (!res.ok) throw new Error(`Download failed: ${res.status}`);
    await pipeline(Readable.fromWeb(res.body), createWriteStream(archive));
  }
  mkdirSync(qdHome, { recursive: true });
  const untar = spawnSync("tar", ["-xf", archive, "-C", qdHome], { stdio: "inherit" });
  if (untar.status !== 0) throw new Error("Couldn't extract Qdrant");
}

async function qdrantUp() {
  if (await qdrantReady()) {
    console.log(`Qdrant: already running on :${QDRANT_PORT}`);
    return;
  }
  if (!existsSync(join(qdHome, exe("qdrant")))) await installQdrant();
  const log = openSync(qdLog, "a");
  const child = spawn(join(qdHome, exe("qdrant")), [], {
    cwd: qdHome,
    detached: true,
    stdio: ["ignore", log, log],
    windowsHide: true,
    env: {
      ...process.env,
      // Localhost only, no API key (like PostgreSQL and OpenSearch here), no telemetry.
      QDRANT__SERVICE__HOST: "127.0.0.1",
      QDRANT__SERVICE__HTTP_PORT: QDRANT_PORT,
      QDRANT__SERVICE__GRPC_PORT: "6334",
      QDRANT__STORAGE__STORAGE_PATH: qdStorage,
      QDRANT__STORAGE__SNAPSHOTS_PATH: join(qdStorage, "snapshots"),
      QDRANT__TELEMETRY_DISABLED: "true",
    },
  });
  child.unref();
  writeFileSync(qdPidFile, String(child.pid));
  process.stdout.write("Qdrant: starting");
  for (let i = 0; i < 30; i++) {
    if (await qdrantReady()) {
      console.log(` ... ready on :${QDRANT_PORT} (log: ${qdLog})`);
      return;
    }
    process.stdout.write(".");
    await sleep(1000);
  }
  throw new Error(`Qdrant didn't become ready; see ${qdLog}`);
}

function qdrantDown() {
  if (!existsSync(qdPidFile)) {
    console.log("Qdrant: not running");
    return;
  }
  const pid = readFileSync(qdPidFile, "utf8").trim();
  if (isWindows) spawnSync("taskkill", ["/PID", pid, "/T", "/F"], { stdio: "ignore" });
  else spawnSync("kill", [pid], { stdio: "ignore" });
  rmSync(qdPidFile, { force: true });
  console.log("Qdrant: stopped");
}

async function status() {
  console.log(`PostgreSQL :${PG_PORT}  ${pgReady() ? "running" : "stopped"}`);
  console.log(`OpenSearch :9200  ${(await openSearchHealthy()) ? "running" : "stopped"}`);
  console.log(`Qdrant     :${QDRANT_PORT}  ${(await qdrantReady()) ? "running" : "stopped"}`);
  console.log(`Data and logs: ${dir}`);
}

mkdirSync(dir, { recursive: true });
const command = process.argv[2];
try {
  if (command === "up") {
    await postgresUp();
    await openSearchUp();
    await qdrantUp();
  } else if (command === "down") {
    qdrantDown();
    openSearchDown();
    postgresDown();
  } else if (command === "status") {
    await status();
  } else {
    console.error("usage: node scripts/local-services.mjs up | down | status");
    process.exit(2);
  }
} catch (err) {
  console.error(err instanceof Error ? err.message : err);
  process.exit(1);
}
