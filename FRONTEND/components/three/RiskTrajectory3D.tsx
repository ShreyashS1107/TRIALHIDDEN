'use client';

import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { AlertTriangle, TrendingDown, CheckCircle2, ShieldAlert } from 'lucide-react';

export default function RiskTrajectory3D() {
  const mountRef = useRef<HTMLDivElement>(null);
  const [activeStep, setActiveStep] = useState<'normal' | 'highlight' | 'divergence'>('divergence');

  useEffect(() => {
    const container = mountRef.current;
    if (!container) return;

    const width = container.clientWidth;
    const height = container.clientHeight;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x06131c);

    const camera = new THREE.PerspectiveCamera(40, width / height, 0.1, 1000);
    camera.position.set(20, 22, 36);
    camera.lookAt(0, 4, 0);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false, powerPreference: 'high-performance' });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.appendChild(renderer.domElement);

    // Ground Grid
    const grid = new THREE.GridHelper(60, 24, 0x133547, 0x081d29);
    grid.position.y = 0;
    scene.add(grid);

    // Ambient & Directional Lighting
    const amb = new THREE.AmbientLight(0x0b202b, 2.2);
    scene.add(amb);
    const dir = new THREE.DirectionalLight(0x39d9ff, 1.5);
    dir.position.set(20, 30, 20);
    scene.add(dir);

    // Amber warning spotlight on focal project
    const spotAmber = new THREE.SpotLight(0xf4b942, 4.0, 40, Math.PI / 4, 0.3);
    spotAmber.position.set(0, 18, 0);
    spotAmber.target.position.set(0, 2, 0);
    scene.add(spotAmber);
    scene.add(spotAmber.target);

    // 5 Miniature Infrastructure Project Models
    // Project 0 is focal (at center (0, 0, 0))
    const projectPositions = [
      { x: 0, z: 0, isFocal: true, name: 'Project 105236 (Expressway Pkg-IV)' },
      { x: -16, z: -8, isFocal: false, name: 'Project 10080 (Bypass Corridor)' },
      { x: 16, z: -10, isFocal: false, name: 'Project 107850 (4-Laning Highway)' },
      { x: -14, z: 12, isFocal: false, name: 'Project 102000 (Tunnel Package)' },
      { x: 18, z: 10, isFocal: false, name: 'Project 101280 (Hill Road Corridor)' },
    ];

    const projectMeshes: THREE.Group[] = [];

    projectPositions.forEach((pos) => {
      const group = new THREE.Group();
      group.position.set(pos.x, 0, pos.z);

      // Base pedestal
      const baseMat = new THREE.MeshStandardMaterial({
        color: pos.isFocal ? 0x2a2010 : 0x0c2534,
        roughness: 0.6,
      });
      const base = new THREE.Mesh(new THREE.CylinderGeometry(3.5, 4, 1, 16), baseMat);
      base.position.y = 0.5;
      group.add(base);

      // Concrete structure (Bridge Pier or Building column)
      const colMat = new THREE.MeshStandardMaterial({
        color: pos.isFocal ? 0x644820 : 0x334155,
        roughness: 0.4,
      });
      const column = new THREE.Mesh(new THREE.BoxGeometry(2, 6, 2), colMat);
      column.position.y = 4;
      group.add(column);

      // Project Node Top
      const nodeColor = pos.isFocal ? 0xf4b942 : 0x39d9ff;
      const nodeSphere = new THREE.Mesh(
        new THREE.SphereGeometry(1, 16, 16),
        new THREE.MeshStandardMaterial({
          color: nodeColor,
          emissive: nodeColor,
          emissiveIntensity: pos.isFocal ? 0.8 : 0.4,
        })
      );
      nodeSphere.position.y = 7.5;
      group.add(nodeSphere);

      scene.add(group);
      projectMeshes.push(group);
    });

    // 3D Trajectory Ribbons extending from the focal project
    const trajectoryGroup = new THREE.Group();
    trajectoryGroup.position.set(0, 7.5, 0);
    scene.add(trajectoryGroup);

    // 1. Planned Trajectory (Straight Cyan Line forward)
    const plannedPoints = [
      new THREE.Vector3(0, 0, 0),
      new THREE.Vector3(5, 0.5, 4),
      new THREE.Vector3(12, 0.8, 8),
      new THREE.Vector3(20, 1.0, 12),
    ];
    const plannedCurve = new THREE.CatmullRomCurve3(plannedPoints);
    const plannedGeo = new THREE.TubeGeometry(plannedCurve, 20, 0.15, 8, false);
    const plannedMat = new THREE.MeshBasicMaterial({ color: 0x39d9ff });
    const plannedMesh = new THREE.Mesh(plannedGeo, plannedMat);
    trajectoryGroup.add(plannedMesh);

    // 2. Actual Trajectory (Slow deceleration bending downward)
    const actualPoints = [
      new THREE.Vector3(0, 0, 0),
      new THREE.Vector3(5, -0.2, 4),
      new THREE.Vector3(10, -1.0, 7),
    ];
    const actualCurve = new THREE.CatmullRomCurve3(actualPoints);
    const actualGeo = new THREE.TubeGeometry(actualCurve, 20, 0.18, 8, false);
    const actualMat = new THREE.MeshStandardMaterial({ color: 0x94a3b8, roughness: 0.3 });
    const actualMesh = new THREE.Mesh(actualGeo, actualMat);
    trajectoryGroup.add(actualMesh);

    // 3. Predicted Trajectory (Divergence plunging sharply towards breach with Amber/Red glow)
    const predictedPoints = [
      new THREE.Vector3(10, -1.0, 7),
      new THREE.Vector3(15, -3.2, 11),
      new THREE.Vector3(20, -5.5, 14),
    ];
    const predictedCurve = new THREE.CatmullRomCurve3(predictedPoints);
    const predictedGeo = new THREE.TubeGeometry(predictedCurve, 20, 0.22, 8, false);
    const predictedMat = new THREE.MeshBasicMaterial({ color: 0xf4b942 });
    const predictedMesh = new THREE.Mesh(predictedGeo, predictedMat);
    trajectoryGroup.add(predictedMesh);

    // Warning Beacon at breach point (20, -5.5, 14)
    const beaconGeo = new THREE.OctahedronGeometry(0.8);
    const beaconMat = new THREE.MeshBasicMaterial({ color: 0xff5c5c, wireframe: true });
    const beaconMesh = new THREE.Mesh(beaconGeo, beaconMat);
    beaconMesh.position.set(20, -5.5, 14);
    trajectoryGroup.add(beaconMesh);

    // Animation Loop
    let animId: number;
    let clock = new THREE.Clock();

    const animate = () => {
      animId = requestAnimationFrame(animate);
      const delta = clock.getElapsedTime();

      // Camera subtle orbit
      camera.position.x = 22 * Math.cos(delta * 0.12);
      camera.position.z = 28 * Math.sin(delta * 0.12);
      camera.lookAt(2, 4, 2);

      // Warning beacon rotation & pulse
      beaconMesh.rotation.y = delta * 2;
      beaconMesh.rotation.z = delta;
      const s = 1.0 + Math.sin(delta * 4) * 0.25;
      beaconMesh.scale.set(s, s, s);

      renderer.render(scene, camera);
    };

    animate();

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
      cancelAnimationFrame(animId);
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
      renderer.dispose();
    };
  }, []);

  return (
    <div className="relative w-full h-[460px] sm:h-[500px] rounded-2xl overflow-hidden border border-amber-500/30 bg-navy-950 shadow-2xl">
      <div ref={mountRef} className="w-full h-full" />

      {/* Trajectory Legend Overlay */}
      <div className="absolute top-4 left-4 z-10 glass-panel-amber p-3.5 rounded-xl text-left border-amber-500/30 backdrop-blur-md">
        <div className="flex items-center gap-2 mb-2">
          <ShieldAlert className="w-4 h-4 text-amber" />
          <span className="text-xs font-bold uppercase tracking-wider text-amber font-mono">
            3D TRAJECTORY DIVERGENCE ENGINE
          </span>
        </div>

        <div className="space-y-1.5 text-[11px] font-mono">
          <div className="flex items-center gap-2">
            <span className="w-3 h-1 bg-cyan rounded-full" />
            <span className="text-concrete-300">PLANNED TRAJECTORY ────────→ (Baseline)</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-1 bg-slate-400 rounded-full" />
            <span className="text-concrete-300">ACTUAL REPORTED ───────↘ (Slippage)</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-1 bg-amber rounded-full animate-pulse" />
            <span className="text-amber font-bold">PREDICTED DIVERGENCE ─────↘ ⚠ (Breach)</span>
          </div>
        </div>
      </div>

      {/* Primary Reveal Box: 72% HIGH RISK */}
      <div className="absolute bottom-6 right-6 z-10 glass-panel-critical p-5 rounded-xl border-critical/40 text-right backdrop-blur-md shadow-glow-critical animate-fade-in max-w-xs">
        <div className="flex items-center justify-end gap-2 text-critical text-xs font-mono font-bold tracking-widest uppercase mb-1">
          <AlertTriangle className="w-4 h-4 animate-bounce" />
          <span>EARLY ANOMALY CONFIRMED</span>
        </div>
        <div className="text-4xl sm:text-5xl font-extrabold font-mono text-white tracking-tight">
          72<span className="text-amber">%</span>
        </div>
        <div className="text-xs font-bold text-amber uppercase tracking-wider mb-2 font-mono">
          HIGH RISK SCORE
        </div>
        <div className="text-[11px] text-concrete-300 font-sans leading-tight border-t border-critical/20 pt-2 font-medium">
          RISK DETECTED BEFORE FAILURE.
        </div>
        <div className="text-[9px] text-concrete-400 font-mono mt-1">
          Variables: Physical velocity collapse + ₹120 Cr spend divergence
        </div>
      </div>
    </div>
  );
}
