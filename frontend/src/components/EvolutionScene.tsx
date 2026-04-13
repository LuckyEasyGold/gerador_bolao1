import { Canvas } from "@react-three/fiber";
import { OrbitControls, Float, Stars, Text } from "@react-three/drei";
import type { VisualGoal, VisualSnapshot } from "../types/api";

interface EvolutionSceneProps {
  snapshot?: VisualSnapshot | null;
  goal?: VisualGoal | null;
}

function GoalMarker({ goal }: { goal: VisualGoal }) {
  return (
    <group position={[goal.target.x, goal.target.y, goal.target.z]}>
      <Float speed={2} rotationIntensity={0.8} floatIntensity={1.5}>
        <mesh>
          <icosahedronGeometry args={[0.9, 1]} />
          <meshStandardMaterial color="#fff1a8" emissive="#ffad33" emissiveIntensity={1.2} />
        </mesh>
      </Float>
      <Text position={[0, 1.6, 0]} fontSize={0.45} color="#ffeccf" anchorX="center">
        {goal.label}
      </Text>
    </group>
  );
}

export function EvolutionScene({ snapshot, goal }: EvolutionSceneProps) {
  return (
    <section className="panel scene-panel">
      <div className="panel-heading">
        <p className="eyebrow">Espaço Evolutivo</p>
        <h2>Indivíduos como organismos visuais</h2>
      </div>

      <div className="scene-wrapper">
        {!snapshot || snapshot.individuals.length === 0 ? (
          <div className="scene-empty">
            <strong>Aguardando população visual</strong>
            <p>Assim que o experimento gerar indivíduos, eles aparecem nesta cena 3D.</p>
          </div>
        ) : (
          <Canvas camera={{ position: [15, 9, 15], fov: 50 }}>
            <color attach="background" args={["#07111f"]} />
            <fog attach="fog" args={["#07111f", 16, 38]} />
            <ambientLight intensity={0.7} />
            <directionalLight position={[12, 12, 6]} intensity={2.2} color="#fff1c1" />
            <pointLight position={[-8, -3, -8]} intensity={1.4} color="#4dd0e1" />
            <Stars radius={80} depth={30} count={3500} factor={4} saturation={0.3} fade />

            <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -5.9, 0]}>
              <circleGeometry args={[13, 64]} />
              <meshStandardMaterial color="#0d2336" emissive="#071725" emissiveIntensity={0.4} />
            </mesh>

            {goal ? <GoalMarker goal={goal} /> : null}

            {snapshot.individuals.map((individual) => (
              <Float
                key={individual.id}
                speed={individual.is_elite ? 3 : 1.6}
                rotationIntensity={individual.is_elite ? 1.4 : 0.5}
                floatIntensity={individual.is_elite ? 1.2 : 0.6}
              >
                <mesh position={[individual.x, individual.y, individual.z]} scale={individual.scale}>
                  <sphereGeometry args={[0.35, 32, 32]} />
                  <meshStandardMaterial
                    color={individual.color}
                    transparent
                    opacity={individual.opacity}
                    emissive={individual.color}
                    emissiveIntensity={individual.is_elite ? 0.9 : 0.35}
                    roughness={0.25}
                    metalness={0.12}
                  />
                </mesh>
              </Float>
            ))}

            <OrbitControls enablePan={false} minDistance={10} maxDistance={32} />
          </Canvas>
        )}
      </div>

      <div className="scene-caption">
        <p>
          O alvo luminoso representa a combinação desejada de alto fitness, alto ROI e risco reduzido.
        </p>
        <p>
          Cada esfera muda de cor e posição conforme a população evolui em direção a esse objetivo.
        </p>
      </div>
    </section>
  );
}
