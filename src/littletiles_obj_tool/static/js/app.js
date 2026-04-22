const sourceInputs = Object.fromEntries(
  Array.from(document.querySelectorAll("[data-source-input]")).map((input) => [input.dataset.sourceInput, input])
);
const sourceCards = Object.fromEntries(
  Array.from(document.querySelectorAll("[data-source-card]")).map((card) => [card.dataset.sourceCard, card])
);
const uploadLabels = Object.fromEntries(
  Array.from(document.querySelectorAll("[data-upload-label]")).map((label) => [label.dataset.uploadLabel, label])
);
const fileNames = Object.fromEntries(
  Array.from(document.querySelectorAll("[data-file-name]")).map((node) => [node.dataset.fileName, node])
);
const clearButtons = Object.fromEntries(
  Array.from(document.querySelectorAll("[data-clear-source]")).map((button) => [button.dataset.clearSource, button])
);

const actionButtons = Array.from(document.querySelectorAll(".action-button"));
const refreshPreviewButton = document.getElementById("refresh-preview");
const actionStatus = document.getElementById("action-status");
const previewStatus = document.getElementById("preview-status");
const viewerEmpty = document.getElementById("viewer-empty");

const hueWheel = document.getElementById("hue-wheel");
const hueThumb = document.getElementById("hue-thumb");
const colorPreview = document.getElementById("color-preview");
const colorReadout = document.getElementById("color-readout");
const satRange = document.getElementById("sat_range");
const valRange = document.getElementById("val_range");
const alphaRange = document.getElementById("alpha_range");
const satValue = document.getElementById("sat_value");
const valValue = document.getElementById("val_value");
const alphaValue = document.getElementById("alpha_value");

const colorR = document.getElementById("color_r");
const colorG = document.getElementById("color_g");
const colorB = document.getElementById("color_b");
const colorA = document.getElementById("color_a");
const gridInput = document.getElementById("grid");
const sizeInput = document.getElementById("max_size");
const blockInput = document.getElementById("block");
const objOptionFields = [colorR, colorG, colorB, colorA, gridInput, sizeInput, blockInput];
const objOnlyFields = [
  gridInput.closest(".obj-only-field"),
  sizeInput.closest(".obj-only-field"),
  blockInput.closest(".obj-only-field"),
].filter(Boolean);

const previewModes = {
  old: "old-to-obj",
  new: "snbt-to-obj",
  obj: "obj-to-snbt",
};

const sourceLabels = {
  old: "1.12 SNBT / TXT",
  new: "1.20 / 1.21 SNBT",
  obj: "OBJ",
};

const colorState = {
  hue: 0,
  sat: 1,
  val: 1,
  alpha: 255,
};
const desktopConfig = window.LTDesktopConfig || { autoExitOnBrowserClose: false, assetUrls: {} };

let previewRuntime = null;
let previewRuntimePromise = null;
let threeModulesPromise = null;

function getThreeModules() {
  if (!threeModulesPromise) {
    threeModulesPromise = (async () => {
      const assetUrls = desktopConfig.assetUrls || {};
      const [THREE, orbitModule, objModule, mtlModule] = await Promise.all([
        import(assetUrls.three),
        import(assetUrls.orbitControls),
        import(assetUrls.objLoader),
        import(assetUrls.mtlLoader),
      ]);
      return {
        THREE,
        OrbitControls: orbitModule.OrbitControls,
        OBJLoader: objModule.OBJLoader,
        MTLLoader: mtlModule.MTLLoader,
      };
    })();
  }
  return threeModulesPromise;
}

function clampByte(value) {
  const numeric = Number.parseInt(value, 10);
  if (Number.isNaN(numeric)) return 0;
  return Math.max(0, Math.min(255, numeric));
}

function clampUnit(value) {
  const numeric = Number.parseFloat(value);
  if (Number.isNaN(numeric)) return 0;
  return Math.max(0, Math.min(1, numeric));
}

function hsvToRgb(h, s, v) {
  const c = v * s;
  const hueSector = ((h % 360) + 360) % 360 / 60;
  const x = c * (1 - Math.abs((hueSector % 2) - 1));
  let r1 = 0;
  let g1 = 0;
  let b1 = 0;

  if (hueSector >= 0 && hueSector < 1) [r1, g1, b1] = [c, x, 0];
  else if (hueSector < 2) [r1, g1, b1] = [x, c, 0];
  else if (hueSector < 3) [r1, g1, b1] = [0, c, x];
  else if (hueSector < 4) [r1, g1, b1] = [0, x, c];
  else if (hueSector < 5) [r1, g1, b1] = [x, 0, c];
  else [r1, g1, b1] = [c, 0, x];

  const m = v - c;
  return {
    r: Math.round((r1 + m) * 255),
    g: Math.round((g1 + m) * 255),
    b: Math.round((b1 + m) * 255),
  };
}

function rgbToHsv(r, g, b) {
  const rn = r / 255;
  const gn = g / 255;
  const bn = b / 255;
  const max = Math.max(rn, gn, bn);
  const min = Math.min(rn, gn, bn);
  const delta = max - min;
  let hue = 0;

  if (delta !== 0) {
    if (max === rn) hue = 60 * (((gn - bn) / delta) % 6);
    else if (max === gn) hue = 60 * ((bn - rn) / delta + 2);
    else hue = 60 * ((rn - gn) / delta + 4);
  }

  if (hue < 0) hue += 360;
  return {
    hue,
    sat: max === 0 ? 0 : delta / max,
    val: max,
  };
}

function rgbToHex(r, g, b) {
  return `#${r.toString(16).padStart(2, "0")}${g.toString(16).padStart(2, "0")}${b.toString(16).padStart(2, "0")}`;
}

function getCurrentColor() {
  const rgb = hsvToRgb(colorState.hue, colorState.sat, colorState.val);
  return {
    ...rgb,
    a: colorState.alpha,
    hex: rgbToHex(rgb.r, rgb.g, rgb.b),
    opacity: colorState.alpha / 255,
  };
}

function setColorFromRgba(r, g, b, a) {
  const hsv = rgbToHsv(clampByte(r), clampByte(g), clampByte(b));
  colorState.hue = hsv.hue;
  colorState.sat = hsv.sat;
  colorState.val = hsv.val;
  colorState.alpha = clampByte(a);
  updateColorUI(true);
}

function updateSliderBackgrounds(rgb) {
  const satStart = hsvToRgb(colorState.hue, 0, colorState.val);
  const satEnd = hsvToRgb(colorState.hue, 1, colorState.val);
  satRange.style.background = `linear-gradient(90deg, rgb(${satStart.r}, ${satStart.g}, ${satStart.b}), rgb(${satEnd.r}, ${satEnd.g}, ${satEnd.b}))`;

  const valEnd = hsvToRgb(colorState.hue, colorState.sat, 1);
  valRange.style.background = `linear-gradient(90deg, rgb(0, 0, 0), rgb(${valEnd.r}, ${valEnd.g}, ${valEnd.b}))`;

  alphaRange.style.background = `linear-gradient(90deg, rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, 0), rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, 1))`;
}

function updateHueThumb() {
  const rect = hueWheel.getBoundingClientRect();
  const radius = rect.width / 2;
  const thumbRadius = radius - 14;
  const angle = (colorState.hue - 90) * Math.PI / 180;
  const x = radius + Math.cos(angle) * thumbRadius;
  const y = radius + Math.sin(angle) * thumbRadius;
  hueThumb.style.left = `${x}px`;
  hueThumb.style.top = `${y}px`;
  const pure = hsvToRgb(colorState.hue, 1, 1);
  hueThumb.style.background = `rgb(${pure.r}, ${pure.g}, ${pure.b})`;
}

function updateColorUI(pushPreview) {
  const current = getCurrentColor();
  const previewColor = `rgba(${current.r}, ${current.g}, ${current.b}, ${current.opacity.toFixed(3)})`;

  colorPreview.style.background = previewColor;
  colorReadout.innerHTML = `${current.hex.toUpperCase()}<br>A${current.a}`;

  satRange.value = Math.round(colorState.sat * 100);
  valRange.value = Math.round(colorState.val * 100);
  alphaRange.value = current.a;

  satValue.textContent = `${satRange.value}%`;
  valValue.textContent = `${valRange.value}%`;
  alphaValue.textContent = `${current.a}`;

  colorR.value = current.r;
  colorG.value = current.g;
  colorB.value = current.b;
  colorA.value = current.a;

  updateSliderBackgrounds(current);
  updateHueThumb();

  if (pushPreview) {
    applyPreviewMaterial();
  }
}

function setHueFromPointer(event) {
  const rect = hueWheel.getBoundingClientRect();
  const centerX = rect.left + rect.width / 2;
  const centerY = rect.top + rect.height / 2;
  const dx = event.clientX - centerX;
  const dy = event.clientY - centerY;
  const angle = Math.atan2(dy, dx) * 180 / Math.PI;
  colorState.hue = (angle + 90 + 360) % 360;
  updateColorUI(true);
}

function onWheelPointerDown(event) {
  event.preventDefault();
  setHueFromPointer(event);
  hueWheel.setPointerCapture(event.pointerId);
}

function onWheelPointerMove(event) {
  if (!hueWheel.hasPointerCapture(event.pointerId)) return;
  setHueFromPointer(event);
}

function getActiveSource() {
  return Object.entries(sourceInputs).find(([, input]) => input.files.length > 0)?.[0] || null;
}

function updateSourceState() {
  const activeSource = getActiveSource();
  const objActive = activeSource === "obj";

  Object.entries(sourceInputs).forEach(([source, input]) => {
    const hasFile = input.files.length > 0;
    const disabled = activeSource && activeSource !== source;
    sourceCards[source].classList.toggle("is-active", hasFile);
    sourceCards[source].classList.toggle("is-disabled", Boolean(disabled));
    uploadLabels[source].classList.toggle("is-disabled", Boolean(disabled));
    input.disabled = Boolean(disabled);
    clearButtons[source].hidden = !hasFile;
    fileNames[source].textContent = hasFile ? input.files[0].name : "No file selected.";
  });

  actionButtons.forEach((button) => {
    const matches = activeSource && button.dataset.source === activeSource;
    button.hidden = !matches;
    button.disabled = !matches;
  });

  refreshPreviewButton.disabled = !activeSource;
  objOptionFields.forEach((field) => {
    field.disabled = !objActive;
  });
  objOnlyFields.forEach((field) => {
    field.dataset.objOnlyLocked = String(!objActive);
  });

  if (!activeSource) {
    actionStatus.textContent = "Choose one source file.";
    previewStatus.textContent = "Choose a source file to preview.";
    return;
  }

  actionStatus.textContent = `${sourceLabels[activeSource]} selected.`;
  if (activeSource !== "obj") {
    previewStatus.textContent = "Preview uses exported OBJ/MTL colors from the NBT data.";
  }
}

function clearSource(source) {
  sourceInputs[source].value = "";
  updateSourceState();
  clearPreview();
  previewStatus.textContent = "Choose a source file to preview.";
}

function buildFormData(mode) {
  const activeSource = getActiveSource();
  if (!activeSource) {
    throw new Error("Choose a source file first.");
  }

  const current = getCurrentColor();
  const formData = new FormData();
  formData.append("mode", mode);
  formData.append("input_file", sourceInputs[activeSource].files[0]);
  formData.append("color_hex", current.hex);
  formData.append("color_r", String(current.r));
  formData.append("color_g", String(current.g));
  formData.append("color_b", String(current.b));
  formData.append("color_a", String(current.a));
  formData.append("grid", gridInput.value);
  formData.append("max_size", sizeInput.value);
  formData.append("block", blockInput.value);
  return formData;
}

function filenameFromDisposition(header, fallback) {
  const match = /filename=\"?([^\";]+)\"?/i.exec(header || "");
  return match ? match[1] : fallback;
}

async function downloadConversion(mode) {
  actionStatus.textContent = "Preparing download...";

  try {
    const response = await fetch("/api/convert", {
      method: "POST",
      body: buildFormData(mode),
    });

    if (!response.ok) {
      const payload = await response.json();
      throw new Error(payload.error || "Conversion failed.");
    }

    const blob = await response.blob();
    const filename = filenameFromDisposition(
      response.headers.get("Content-Disposition"),
      mode.endsWith("to-obj") ? "converted_obj.zip" : "converted_1_20.snbt"
    );
    const href = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = href;
    anchor.download = filename;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    URL.revokeObjectURL(href);
    actionStatus.textContent = `Download ready: ${filename}`;
  } catch (error) {
    actionStatus.textContent = error.message;
  }
}

async function ensurePreviewRuntime() {
  if (previewRuntime) return previewRuntime;
  if (!previewRuntimePromise) {
    previewRuntimePromise = createPreviewRuntime();
  }
  try {
    previewRuntime = await previewRuntimePromise;
    return previewRuntime;
  } catch (error) {
    previewRuntimePromise = null;
    throw error;
  }
}

async function createPreviewRuntime() {
  const viewer = document.getElementById("viewer");
  const { THREE, OrbitControls, OBJLoader, MTLLoader } = await getThreeModules();

  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  viewer.appendChild(renderer.domElement);

  const scene = new THREE.Scene();
  scene.background = new THREE.Color("#ede1cf");

  const camera = new THREE.PerspectiveCamera(50, 1, 0.01, 5000);
  camera.position.set(18, 16, 18);

  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.target.set(0, 0, 0);
  renderer.domElement.addEventListener("contextmenu", (event) => {
    event.preventDefault();
  });

  const hemi = new THREE.HemisphereLight(0xffffff, 0x9e8464, 1.1);
  scene.add(hemi);

  const keyLight = new THREE.DirectionalLight(0xffffff, 1.4);
  keyLight.position.set(14, 20, 10);
  scene.add(keyLight);

  const fillLight = new THREE.DirectionalLight(0xfff2de, 0.6);
  fillLight.position.set(-12, 10, -10);
  scene.add(fillLight);

  const gridHelper = new THREE.GridHelper(64, 64, 0x8d5d2f, 0xc5b49e);
  gridHelper.position.y = -0.001;
  scene.add(gridHelper);

  const axesHelper = new THREE.AxesHelper(8);
  scene.add(axesHelper);

  let currentObject = null;
  let currentKind = null;

  function resizeRenderer() {
    const width = viewer.clientWidth;
    const height = viewer.clientHeight;
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    renderer.setSize(width, height, false);
  }

  function clearCurrentObject() {
    if (!currentObject) return;
    scene.remove(currentObject);
    currentObject.traverse((child) => {
      if (child.geometry) child.geometry.dispose();
      if (Array.isArray(child.material)) child.material.forEach((material) => material.dispose());
      else if (child.material) child.material.dispose();
    });
    currentObject = null;
    currentKind = null;
  }

  function frameObject(object) {
    const box = new THREE.Box3().setFromObject(object);
    if (box.isEmpty()) return;

    const center = box.getCenter(new THREE.Vector3());
    const size = box.getSize(new THREE.Vector3());
    const maxDim = Math.max(size.x, size.y, size.z, 1);
    const distance = maxDim * 1.8;

    controls.target.copy(center);
    camera.position.set(center.x + distance, center.y + distance * 0.8, center.z + distance);
    camera.near = Math.max(maxDim / 1000, 0.01);
    camera.far = maxDim * 100;
    camera.updateProjectionMatrix();
    controls.update();
  }

  function installWireOverlay(root) {
    root.traverse((child) => {
      if (!child.isMesh) return;
      const edges = new THREE.EdgesGeometry(child.geometry);
      const line = new THREE.LineSegments(
        edges,
        new THREE.LineBasicMaterial({ color: 0x3d3125, transparent: true, opacity: 0.22 })
      );
      child.add(line);
    });
  }

  function applyObjMaterial(color) {
    if (!currentObject || currentKind !== "obj") return;
    currentObject.traverse((child) => {
      if (!child.isMesh || Array.isArray(child.material)) return;
      child.material.color.set(color.hex);
      child.material.opacity = color.opacity;
      child.material.transparent = color.opacity < 0.999;
      child.material.needsUpdate = true;
    });
  }

  async function load(payload) {
    clearCurrentObject();
    viewerEmpty.hidden = true;

    let object;
    if (payload.kind === "obj_mtl") {
      const materials = new MTLLoader().parse(payload.mtl, "");
      materials.preload();
      const objLoader = new OBJLoader();
      objLoader.setMaterials(materials);
      object = objLoader.parse(payload.obj);
      currentKind = "obj_mtl";
    } else {
      const objLoader = new OBJLoader();
      object = objLoader.parse(payload.obj);
      const current = getCurrentColor();
      object.traverse((child) => {
        if (!child.isMesh) return;
        child.material = new THREE.MeshStandardMaterial({
          color: current.hex,
          roughness: 0.88,
          metalness: 0.05,
          transparent: current.opacity < 0.999,
          opacity: current.opacity,
        });
      });
      currentKind = "obj";
    }

    installWireOverlay(object);
    scene.add(object);
    currentObject = object;
    frameObject(object);
    resizeRenderer();
  }

  function animate() {
    controls.update();
    renderer.render(scene, camera);
    requestAnimationFrame(animate);
  }

  window.addEventListener("resize", resizeRenderer);
  resizeRenderer();
  animate();

  return {
    load,
    clear() {
      clearCurrentObject();
      viewerEmpty.hidden = false;
    },
    applyObjMaterial,
  };
}

async function requestPreview() {
  const activeSource = getActiveSource();
  if (!activeSource) {
    previewStatus.textContent = "Choose a source file to preview.";
    return;
  }

  previewStatus.textContent = "Generating preview...";

  try {
    const response = await fetch("/preview", {
      method: "POST",
      body: buildFormData(previewModes[activeSource]),
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || "Preview request failed.");
    }

    const runtime = await ensurePreviewRuntime();
    await runtime.load(payload);
    previewStatus.textContent = "Preview loaded.";
  } catch (error) {
    previewStatus.textContent = error.message;
  }
}

function clearPreview() {
  if (previewRuntime) {
    previewRuntime.clear();
  } else {
    viewerEmpty.hidden = false;
  }
}

function applyPreviewMaterial() {
  if (!previewRuntime) return;
  previewRuntime.applyObjMaterial(getCurrentColor());
}

function startDesktopHeartbeat() {
  if (!desktopConfig.autoExitOnBrowserClose) return;

  const sendHeartbeat = () => {
    fetch("/api/client/heartbeat", {
      method: "POST",
      keepalive: true,
      cache: "no-store",
    }).catch(() => {});
  };

  sendHeartbeat();
  window.setInterval(sendHeartbeat, 2000);
}

sourceInputs.old.addEventListener("change", () => {
  updateSourceState();
  if (sourceInputs.old.files.length > 0) requestPreview();
});
sourceInputs.new.addEventListener("change", () => {
  updateSourceState();
  if (sourceInputs.new.files.length > 0) requestPreview();
});
sourceInputs.obj.addEventListener("change", () => {
  updateSourceState();
  if (sourceInputs.obj.files.length > 0) requestPreview();
});

Object.entries(clearButtons).forEach(([source, button]) => {
  button.addEventListener("click", () => clearSource(source));
});

actionButtons.forEach((button) => {
  button.addEventListener("click", () => {
    if (!button.disabled) {
      downloadConversion(button.dataset.mode);
    }
  });
});

refreshPreviewButton.addEventListener("click", () => {
  requestPreview();
});

hueWheel.addEventListener("pointerdown", onWheelPointerDown);
hueWheel.addEventListener("pointermove", onWheelPointerMove);
hueWheel.addEventListener("pointerup", (event) => {
  if (hueWheel.hasPointerCapture(event.pointerId)) hueWheel.releasePointerCapture(event.pointerId);
});
hueWheel.addEventListener("pointercancel", (event) => {
  if (hueWheel.hasPointerCapture(event.pointerId)) hueWheel.releasePointerCapture(event.pointerId);
});

satRange.addEventListener("input", () => {
  colorState.sat = clampUnit(Number(satRange.value) / 100);
  updateColorUI(true);
});
valRange.addEventListener("input", () => {
  colorState.val = clampUnit(Number(valRange.value) / 100);
  updateColorUI(true);
});
alphaRange.addEventListener("input", () => {
  colorState.alpha = clampByte(alphaRange.value);
  updateColorUI(true);
});

[colorR, colorG, colorB, colorA].forEach((field) => {
  field.addEventListener("input", () => {
    setColorFromRgba(colorR.value, colorG.value, colorB.value, colorA.value);
  });
});

window.addEventListener("resize", () => {
  updateHueThumb();
});

updateSourceState();
updateColorUI(false);
startDesktopHeartbeat();
