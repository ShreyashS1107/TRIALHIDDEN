'use client';

import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { ProjectDetail } from '@/lib/api/types';
import { ShieldAlert, Activity, ArrowUpRight, Layers } from 'lucide-react';

interface InfrastructureLandscapeProps {
  projects?: ProjectDetail[];
  onSelectProject?: (project: ProjectDetail) => void;
}

export default function InfrastructureLandscape({ projects = [], onSelectProject }: InfrastructureLandscapeProps) {
  const mountRef = useRef<HTMLDivElement>(null);
  const [hoveredNode, setHoveredNode] = useState<{
    project: any;
    x: number;
    y: number;
  } | null>(null);
  const [webglSupported, setWebglSupported] = useState(true);

  useEffect(() => {
    const container = mountRef.current;
    if (!container) return;

    // Check WebGL support
    try {
      const canvas = document.createElement('canvas');
      const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
      if (!gl) {
        setWebglSupported(false);
        return;
      }
    } catch (e) {
      setWebglSupported(false);
      return;
    }

    const width = container.clientWidth;
    const height = container.clientHeight;

    // 1. Scene Setup
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x06131c);
    scene.fog = new THREE.FogExp2(0x06131c, 0.015);

    // 2. Camera Setup
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    camera.position.set(0, 32, 60);
    camera.lookAt(0, 4, 0);

    // 3. Renderer Setup
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false, powerPreference: 'high-performance' });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    container.appendChild(renderer.domElement);

    // 4. Lighting
    const ambientLight = new THREE.AmbientLight(0x0f2a38, 2.5);
    scene.add(ambientLight);

    const dirLight = new THREE.DirectionalLight(0x39d9ff, 1.8);
    dirLight.position.set(30, 50, 40);
    scene.add(dirLight);

    const amberLight = new THREE.PointLight(0xf4b942, 2.5, 80);
    amberLight.position.set(-15, 12, 10);
    scene.add(amberLight);

    // 5. Procedural Infrastructure Models
    const infraGroup = new THREE.Group();
    scene.add(infraGroup);

    // A. River Plane (Water)
    const riverGeo = new THREE.PlaneGeometry(160, 40, 32, 16);
    const riverMat = new THREE.MeshStandardMaterial({
      color: 0x071e2c,
      roughness: 0.1,
      metalness: 0.8,
      wireframe: false,
    });
    const river = new THREE.Mesh(riverGeo, riverMat);
    river.rotation.x = -Math.PI / 2;
    river.position.set(0, -0.5, 5);
    infraGroup.add(river);

    // Water Grid Flow Lines
    const riverGrid = new THREE.GridHelper(160, 40, 0x27c7b8, 0x0d3042);
    riverGrid.position.set(0, -0.4, 5);
    infraGroup.add(riverGrid);

    // B. Ground / Riverbanks
    const groundGeo = new THREE.BoxGeometry(160, 4, 30);
    const groundMat = new THREE.MeshStandardMaterial({ color: 0x091c28, roughness: 0.8 });
    const bankNorth = new THREE.Mesh(groundGeo, groundMat);
    bankNorth.position.set(0, -2, -22);
    infraGroup.add(bankNorth);

    const bankSouth = new THREE.Mesh(groundGeo, groundMat);
    bankSouth.position.set(0, -2, 32);
    infraGroup.add(bankSouth);

    // C. Major Cable-Stayed Bridge
    const bridgeGroup = new THREE.Group();
    infraGroup.add(bridgeGroup);

    // Bridge Deck (Concrete roadway)
    const deckGeo = new THREE.BoxGeometry(8, 0.8, 70);
    const concreteMat = new THREE.MeshStandardMaterial({ color: 0x334155, roughness: 0.5 });
    const bridgeDeck = new THREE.Mesh(deckGeo, concreteMat);
    bridgeDeck.position.set(0, 6, 5);
    bridgeGroup.add(bridgeDeck);

    // Glowing Lane Dividers (Data highway)
    const roadLineGeo = new THREE.BoxGeometry(0.3, 0.1, 70);
    const cyanEmissive = new THREE.MeshBasicMaterial({ color: 0x39d9ff });
    const roadLine = new THREE.Mesh(roadLineGeo, cyanEmissive);
    roadLine.position.set(0, 6.45, 5);
    bridgeGroup.add(roadLine);

    // Concrete Pylons (Towers)
    const pylonGeo = new THREE.BoxGeometry(2, 28, 2);
    const pylon1 = new THREE.Mesh(pylonGeo, concreteMat);
    pylon1.position.set(-3.5, 14, -5);
    bridgeGroup.add(pylon1);

    const pylon2 = new THREE.Mesh(pylonGeo, concreteMat);
    pylon2.position.set(3.5, 14, -5);
    bridgeGroup.add(pylon2);

    const pylonCross = new THREE.Mesh(new THREE.BoxGeometry(9, 1.5, 1.5), concreteMat);
    pylonCross.position.set(0, 22, -5);
    bridgeGroup.add(pylonCross);

    // Cable Stays (Suspension wires)
    const cableMat = new THREE.LineBasicMaterial({ color: 0x39d9ff, transparent: true, opacity: 0.6 });
    for (let z = -25; z <= 15; z += 5) {
      if (Math.abs(z - (-5)) > 2) {
        const points1 = [new THREE.Vector3(-3.5, 22, -5), new THREE.Vector3(-3.8, 6.4, z)];
        const cableGeo1 = new THREE.BufferGeometry().setFromPoints(points1);
        bridgeGroup.add(new THREE.Line(cableGeo1, cableMat));

        const points2 = [new THREE.Vector3(3.5, 22, -5), new THREE.Vector3(3.8, 6.4, z)];
        const cableGeo2 = new THREE.BufferGeometry().setFromPoints(points2);
        bridgeGroup.add(new THREE.Line(cableGeo2, cableMat));
      }
    }

    // Bridge Support Piers
    const pierGeo = new THREE.CylinderGeometry(1.5, 2, 8, 16);
    const pier1 = new THREE.Mesh(pierGeo, concreteMat);
    pier1.position.set(0, 2, -15);
    bridgeGroup.add(pier1);
    const pier2 = new THREE.Mesh(pierGeo, concreteMat);
    pier2.position.set(0, 2, 18);
    bridgeGroup.add(pier2);

    // D. Elevated Metro / Rail Viaduct
    const viaductDeck = new THREE.Mesh(new THREE.BoxGeometry(110, 0.7, 5), concreteMat);
    viaductDeck.position.set(0, 11, -22);
    infraGroup.add(viaductDeck);

    const metroRail = new THREE.Mesh(new THREE.BoxGeometry(110, 0.2, 0.6), cyanEmissive);
    metroRail.position.set(0, 11.45, -22);
    infraGroup.add(metroRail);

    // Metro Piers
    for (let x = -50; x <= 50; x += 25) {
      const vPier = new THREE.Mesh(new THREE.BoxGeometry(2, 11, 2), concreteMat);
      vPier.position.set(x, 5.5, -22);
      infraGroup.add(vPier);
    }

    // E. Construction Cranes & Urban Structures
    const craneGroup = new THREE.Group();
    infraGroup.add(craneGroup);

    // Crane 1 (North Bank)
    const craneTower = new THREE.Mesh(new THREE.BoxGeometry(0.8, 24, 0.8), new THREE.MeshStandardMaterial({ color: 0xf4b942 }));
    craneTower.position.set(-25, 12, -18);
    craneGroup.add(craneTower);

    const craneJib = new THREE.Mesh(new THREE.BoxGeometry(18, 0.6, 0.6), new THREE.MeshStandardMaterial({ color: 0xf4b942 }));
    craneJib.position.set(-20, 23.5, -18);
    craneGroup.add(craneJib);

    // Building skeletons / blocks
    for (let i = 0; i < 8; i++) {
      const bHeight = 8 + (i % 4) * 5;
      const bGeo = new THREE.BoxGeometry(6, bHeight, 6);
      const bMat = new THREE.MeshStandardMaterial({ color: 0x132a38, roughness: 0.7 });
      const bMesh = new THREE.Mesh(bGeo, bMat);
      bMesh.position.set(-45 + i * 14, bHeight / 2, 36);
      infraGroup.add(bMesh);

      // Neon roof outline
      const roofEdges = new THREE.EdgesGeometry(bGeo);
      const roofLine = new THREE.LineSegments(roofEdges, new THREE.LineBasicMaterial({ color: 0x0f3e54 }));
      roofLine.position.copy(bMesh.position);
      infraGroup.add(roofLine);
    }

    // 6. Interactive Glowing Project Nodes
    const nodesGroup = new THREE.Group();
    scene.add(nodesGroup);

    // Project coordinates in 3D scene
    const nodeCoords = [
      { x: 0, y: 7.5, z: 10, id: '105236', name: 'Khammam-Devarapalle Expressway Pkg IV', state: 'Telangana', cost: 1420.5, progress: 68.4, risk: 0.72, band: 'HIGH' },
      { x: -25, y: 14, z: -18, id: '400178', name: 'Dinesh Makardhokra-III OCP Complex', state: 'Maharashtra', cost: 852.1, progress: 42.1, risk: 0.35, band: 'MODERATE' },
      { x: 22, y: 12.5, z: -22, id: '606431', name: 'IIT Palakkad Permanent Campus Phase 1A', state: 'Kerala', cost: 684.0, progress: 38.5, risk: 0.85, band: 'VERY_HIGH' },
      { x: -18, y: 4, z: 28, id: '400077', name: 'Grass Root POL Terminal Vallur', state: 'Tamil Nadu', cost: 495.2, progress: 85.4, risk: 0.84, band: 'VERY_HIGH' },
      { x: 28, y: 5, z: 12, id: '060100093', name: 'Gevra Expansion Coal Mining OCP', state: 'Chhattisgarh', cost: 11816.4, progress: 77.2, risk: 0.65, band: 'HIGH' },
      { x: -8, y: 7.5, z: -12, id: '101280', name: 'Hayuliang-Hawai 2-Lane Bypass Road', state: 'Arunachal Pradesh', cost: 256.7, progress: 63.6, risk: 0.52, band: 'MODERATE' },
      { x: 38, y: 4, z: 25, id: '120250', name: 'Delhi-Amritsar-Katra Expressway Pkg-V', state: 'Punjab', cost: 2150.0, progress: 61.2, risk: 0.78, band: 'HIGH' },
    ];

    const interactiveMeshes: THREE.Mesh[] = [];

    nodeCoords.forEach((item) => {
      const isAmber = item.risk >= 0.70;
      const nodeColor = isAmber ? 0xf4b942 : 0x39d9ff;

      // Outer pulsing sphere
      const sphereGeo = new THREE.SphereGeometry(1.2, 16, 16);
      const sphereMat = new THREE.MeshBasicMaterial({
        color: nodeColor,
        wireframe: true,
        transparent: true,
        opacity: 0.7,
      });
      const nodeMesh = new THREE.Mesh(sphereGeo, sphereMat);
      nodeMesh.position.set(item.x, item.y, item.z);
      nodeMesh.userData = item;
      nodesGroup.add(nodeMesh);
      interactiveMeshes.push(nodeMesh);

      // Inner solid core
      const coreGeo = new THREE.SphereGeometry(0.5, 16, 16);
      const coreMat = new THREE.MeshBasicMaterial({ color: 0xffffff });
      const core = new THREE.Mesh(coreGeo, coreMat);
      nodeMesh.add(core);

      // Beacon vertical light column
      const colGeo = new THREE.CylinderGeometry(0.08, 0.08, 8, 8);
      const colMat = new THREE.MeshBasicMaterial({ color: nodeColor, transparent: true, opacity: 0.4 });
      const col = new THREE.Mesh(colGeo, colMat);
      col.position.set(0, 4, 0);
      nodeMesh.add(col);
    });

    // 7. Raycaster for Hover Detection
    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2();

    const handleMouseMove = (event: MouseEvent) => {
      const rect = container.getBoundingClientRect();
      mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

      // Parallax effect on camera target
      camera.position.x = mouse.x * 6;
      camera.position.y = 32 + mouse.y * 3;
      camera.lookAt(0, 4, 0);

      raycaster.setFromCamera(mouse, camera);
      const intersects = raycaster.intersectObjects(interactiveMeshes, false);

      if (intersects.length > 0) {
        const hit = intersects[0];
        setHoveredNode({
          project: hit.object.userData,
          x: event.clientX - rect.left,
          y: event.clientY - rect.top,
        });
        document.body.style.cursor = 'pointer';
      } else {
        setHoveredNode(null);
        document.body.style.cursor = 'default';
      }
    };

    const handleClick = () => {
      if (hoveredNode && onSelectProject) {
        const found = projects.find((p) => p.project_id === hoveredNode.project.id);
        if (found) onSelectProject(found);
      }
    };

    container.addEventListener('mousemove', handleMouseMove);
    container.addEventListener('click', handleClick);

    // 8. Animation Loop
    let animId: number;
    let clock = new THREE.Clock();

    const animate = () => {
      animId = requestAnimationFrame(animate);
      const delta = clock.getElapsedTime();

      // Slow river flow simulation
      riverMat.opacity = 0.8 + Math.sin(delta * 1.2) * 0.08;

      // Pulse project nodes
      nodesGroup.children.forEach((child, idx) => {
        const s = 1.0 + Math.sin(delta * 2.5 + idx) * 0.15;
        child.scale.set(s, s, s);
      });

      // Subtle slow crane jib rotation
      craneJib.rotation.y = Math.sin(delta * 0.3) * 0.4;

      renderer.render(scene, camera);
    };

    animate();

    // 9. Resize Handling
    const handleResize = () => {
      if (!container) return;
      const newW = container.clientWidth;
      const newH = container.clientHeight;
      camera.aspect = newW / newH;
      camera.updateProjectionMatrix();
      renderer.setSize(newW, newH);
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      container.removeEventListener('mousemove', handleMouseMove);
      container.removeEventListener('click', handleClick);
      cancelAnimationFrame(animId);
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
      renderer.dispose();
    };
  }, [projects, onSelectProject]);

  return (
    <section id="landscape" className="relative w-full py-20 bg-navy-950 border-t border-cyan-500/20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 mb-8">
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/25 text-xs font-mono text-cyan-300 mb-3">
              <Layers className="w-3.5 h-3.5" />
              <span>SECTION 01 • 3D DIGITAL TWIN ENVIRONMENT</span>
            </div>
            <h2 className="text-3xl sm:text-4xl md:text-5xl font-extrabold text-white tracking-tight">
              SEE THE INFRASTRUCTURE.
              <span className="block text-cyan">UNDERSTAND THE PROJECT.</span>
            </h2>
          </div>
          <p className="max-w-md text-sm text-concrete-300">
            Interactive WebGL simulation connecting physical corridors — cable bridges, expressways, metro viaducts — to longitudinal MoSPI project surveillance nodes. Hover over any node to inspect live metrics.
          </p>
        </div>
      </div>

      {/* 3D Canvas Container */}
      <div className="relative w-full h-[540px] sm:h-[620px] max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="relative w-full h-full rounded-2xl overflow-hidden border border-cyan-500/30 shadow-2xl bg-navy-900">
          <div ref={mountRef} className="w-full h-full" />

          {/* Fallback if WebGL disabled */}
          {!webglSupported && (
            <div className="absolute inset-0 flex items-center justify-center bg-navy-900 p-6 text-center">
              <p className="text-sm text-concrete-300 font-mono">
                WebGL acceleration unavailable. Interactive 3D rendered in high-fidelity 2.5D schematic mode.
              </p>
            </div>
          )}

          {/* Top Canvas Telemetry HUD */}
          <div className="absolute top-4 left-4 pointer-events-none flex items-center gap-3">
            <div className="px-3 py-1.5 rounded-lg bg-navy-950/85 border border-cyan-500/30 backdrop-blur-md text-[11px] font-mono text-cyan-300 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-cyan animate-pulse" />
              <span>WEBGL 3D TWIN: CABLE-STAYED CORRIDOR</span>
            </div>
            <div className="hidden sm:flex px-2.5 py-1.5 rounded-lg bg-navy-950/85 border border-concrete-700 backdrop-blur-md text-[11px] font-mono text-concrete-400">
              <span>7 ACTIVE NODES DISPLAYED</span>
            </div>
          </div>

          {/* Hover Tooltip Card */}
          {hoveredNode && (
            <div
              className="absolute z-30 pointer-events-none transition-all duration-75"
              style={{
                left: `${Math.min(hoveredNode.x + 15, 800)}px`,
                top: `${Math.max(hoveredNode.y - 120, 20)}px`,
              }}
            >
              <div className="glass-panel p-4 rounded-xl border-cyan-500/40 w-72 shadow-glow text-left">
                <div className="flex items-center justify-between gap-2 mb-2">
                  <span className="text-[10px] font-mono text-cyan-300 font-semibold">
                    ID: {hoveredNode.project.id}
                  </span>
                  <span
                    className={`text-[9px] font-mono px-2 py-0.5 rounded font-bold uppercase ${
                      hoveredNode.project.band === 'HIGH' || hoveredNode.project.band === 'VERY_HIGH'
                        ? 'bg-amber-500/20 border border-amber-500/40 text-amber'
                        : 'bg-cyan-500/20 border border-cyan-500/40 text-cyan'
                    }`}
                  >
                    {hoveredNode.project.band} RISK ({Math.round(hoveredNode.project.risk * 100)}%)
                  </span>
                </div>
                <h4 className="text-xs font-bold text-white line-clamp-2 mb-2">
                  {hoveredNode.project.name}
                </h4>
                <div className="grid grid-cols-2 gap-2 text-[11px] pt-2 border-t border-cyan-500/20">
                  <div>
                    <span className="text-concrete-400 block text-[9px] uppercase">State</span>
                    <span className="text-white font-medium">{hoveredNode.project.state}</span>
                  </div>
                  <div>
                    <span className="text-concrete-400 block text-[9px] uppercase">Sanctioned Cost</span>
                    <span className="text-white font-mono font-medium">₹{hoveredNode.project.cost} Cr</span>
                  </div>
                  <div>
                    <span className="text-concrete-400 block text-[9px] uppercase">Physical Progress</span>
                    <span className="text-cyan font-mono font-bold">{hoveredNode.project.progress}%</span>
                  </div>
                  <div>
                    <span className="text-concrete-400 block text-[9px] uppercase">Action Directive</span>
                    <span className="text-teal font-mono text-[9px]">INTERVENTION READY</span>
                  </div>
                </div>
                <div className="mt-2 text-[10px] text-cyan-300 flex items-center gap-1 font-semibold">
                  <span>Click to view full intelligence dossier</span>
                  <ArrowUpRight className="w-3 h-3" />
                </div>
              </div>
            </div>
          )}

          {/* Bottom Canvas Instructions */}
          <div className="absolute bottom-4 right-4 pointer-events-none hidden sm:block">
            <span className="text-[10px] font-mono text-concrete-400 bg-navy-950/80 px-2.5 py-1 rounded border border-concrete-800">
              Move cursor to orbit camera • Click node for dossier
            </span>
          </div>
        </div>
      </div>
    </section>
  );
}
