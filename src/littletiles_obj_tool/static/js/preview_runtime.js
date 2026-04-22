import * as THREE from "../vendor/three/build/three.module.js";
import { OrbitControls } from "../vendor/three/examples/jsm/controls/OrbitControls.js";
import { OBJLoader } from "../vendor/three/examples/jsm/loaders/OBJLoader.js";
import { MTLLoader } from "../vendor/three/examples/jsm/loaders/MTLLoader.js";

export function createPreviewRuntime({ viewer, viewerEmpty, getCurrentColor }) {
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
