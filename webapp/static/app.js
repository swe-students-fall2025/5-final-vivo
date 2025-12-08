import * as THREE from "https://cdn.skypack.dev/three@0.129.0/build/three.module.js";
import { GLTFLoader } from "https://cdn.skypack.dev/three@0.129.0/examples/jsm/loaders/GLTFLoader.js";
import { gsap } from "https://cdn.skypack.dev/gsap";

const camera = new THREE.PerspectiveCamera(
  10,
  window.innerWidth / window.innerHeight,
  0.1,
  1000,
);
camera.position.z = 13;

const scene = new THREE.Scene();
let bath;
let mixer;
const loader = new GLTFLoader();
loader.load(
  "/static/plastic_toilet_cabin.glb",
  function (gltf) {
    bath = gltf.scene;
    bath.scale.set(0.18, 0.18, 0.18);
    bath.position.set(0, -1.4, -3.5);
    scene.add(bath);
    modelMove();
  },
  undefined,
  function (error) {
    console.error("Error loading model:", error);
  },
);

const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(window.devicePixelRatio);
document.getElementById("container3D").appendChild(renderer.domElement);

//light
const ambientLight = new THREE.AmbientLight(0xffffff, 1.3);
scene.add(ambientLight);

const topLight = new THREE.DirectionalLight(0xffffff, 1);
topLight.position.set(500, 500, 500);
scene.add(topLight);

const clock = new THREE.Clock();

const reRender3D = () => {
  requestAnimationFrame(reRender3D);
  renderer.render(scene, camera);
  if (mixer) mixer.update(clock.getDelta());
};
reRender3D();

let arrPositionModel = [
  {
    id: "banner",
    position: { x: 0, y: -1.2, z: -3 },
    rotation: { x: 0, y: 1.3, z: 0 },
  },
  {
    id: "intro",
    position: { x: -0.6, y: -1.4, z: -5 },
    rotation: { x: 0.05, y: 0.3, z: 0 },
  },
  {
    id: "description",
    position: { x: 1.5, y: -1.1, z: -5.2 },
    rotation: { x: 0.35, y: -0.4, z: 0 },
  },
];

const modelMove = () => {
  const sections = document.querySelectorAll(".section");
  let currentSection;
  sections.forEach((section) => {
    const rect = section.getBoundingClientRect();
    if (rect.top <= window.innerHeight / 3) {
      currentSection = section.id;
    }
  });
  let position_active = arrPositionModel.findIndex(
    (val) => val.id == currentSection,
  );
  if (position_active >= 0) {
    let new_coordinates = arrPositionModel[position_active];
    gsap.to(bath.position, {
      x: new_coordinates.position.x,
      y: new_coordinates.position.y,
      z: new_coordinates.position.z,
      duration: 1.8,
      ease: "power2.out",
    });
    gsap.to(bath.rotation, {
      x: new_coordinates.rotation.x,
      y: new_coordinates.rotation.y,
      z: new_coordinates.rotation.z,
      duration: 1.8,
      ease: "power2.out",
    });
  }
};
window.addEventListener("scroll", () => {
  if (bath) {
    modelMove();
  }
});
window.addEventListener("resize", () => {
  renderer.setSize(window.innerWidth, window.innerHeight);
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
});
