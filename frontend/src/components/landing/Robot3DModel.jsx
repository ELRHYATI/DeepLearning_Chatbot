import { Canvas } from '@react-three/fiber'
import { useGLTF, Float, OrbitControls, Environment } from '@react-three/drei'
import { Suspense } from 'react'

// Robot Model Component
function RobotModel() {
  // CUSTOMIZE: Update the path to your robot .glb file
  // Place your robot.glb file in: frontend/public/robot.glb
  const { scene } = useGLTF('/robot.glb')

  return (
    <Float
      speed={2}
      floatIntensity={0.5}
      rotationIntensity={0.3}
    >
      <primitive 
        object={scene} 
        scale={2}
        position={[0, -1, 0]}
      />
    </Float>
  )
}

// Preload the model for better performance
// Note: This is called at module level, so it will preload when the module is imported
try {
  useGLTF.preload('/robot.glb')
} catch (error) {
  // Silently fail if preload doesn't work - the model will still load when needed
}

// Main Robot 3D Component
export default function Robot3D() {
  return (
    <div className="w-full h-full">
      <Canvas 
        camera={{ position: [0, 0, 5], fov: 50 }}
        gl={{ antialias: true, alpha: true }}
        shadows
      >
        {/* Lighting */}
        <ambientLight intensity={0.5} />
        <spotLight 
          position={[10, 10, 10]} 
          angle={0.3}
          penumbra={1}
          intensity={1}
          castShadow
        />
        <pointLight position={[-10, -10, -10]} intensity={0.3} color="#00D9FF" />
        <pointLight position={[10, -10, 10]} intensity={0.3} color="#6366F1" />

        {/* Environment for reflections */}
        <Environment preset="city" />

        {/* Robot Model */}
        <Suspense fallback={
          <mesh>
            <boxGeometry args={[1, 1, 1]} />
            <meshStandardMaterial color="#00D9FF" />
          </mesh>
        }>
          <RobotModel />
        </Suspense>

        {/* Camera Controls */}
        <OrbitControls 
          enableZoom={false}
          enablePan={false}
          minPolarAngle={Math.PI / 3}
          maxPolarAngle={Math.PI / 2.2}
          autoRotate
          autoRotateSpeed={0.5}
        />
      </Canvas>
    </div>
  )
}

