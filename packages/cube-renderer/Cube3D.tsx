import { Canvas } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import { useMemo } from "react";
import type { CubeColor, CubeState } from "../cube-core/CubeState";
import { DEFAULT_FACE_COLORS } from "../shared/constants";
import type { FaceName } from "../shared/types";
import type { Move } from "../cube-core/Move";

export interface Cube3DProps {
  state: CubeState;
  animationMove?: Move | undefined;
  animationProgress?: number | undefined;
  onFaceMove?: ((face: FaceName) => void) | undefined;
  className?: string | undefined;
}

type Vector = [number, number, number];

interface StickerDefinition {
  face: FaceName;
  index: number;
  position: Vector;
  rotation: Vector;
  cubie: Vector;
}

const FACE_LAYOUT: Record<FaceName, { normal: Vector; right: Vector; down: Vector }> = {
  U: { normal: [0, 1, 0], right: [1, 0, 0], down: [0, 0, 1] },
  D: { normal: [0, -1, 0], right: [1, 0, 0], down: [0, 0, -1] },
  F: { normal: [0, 0, 1], right: [1, 0, 0], down: [0, -1, 0] },
  B: { normal: [0, 0, -1], right: [-1, 0, 0], down: [0, -1, 0] },
  L: { normal: [-1, 0, 0], right: [0, 0, 1], down: [0, -1, 0] },
  R: { normal: [1, 0, 0], right: [0, 0, -1], down: [0, -1, 0] },
};

const FACE_ORDER: FaceName[] = ["U", "D", "F", "B", "L", "R"];

function addVector(a: Vector, b: Vector, scale = 1): Vector {
  return [a[0] + b[0] * scale, a[1] + b[1] * scale, a[2] + b[2] * scale];
}

function stickerDefinitions(): StickerDefinition[] {
  return FACE_ORDER.flatMap((face) => {
    const layout = FACE_LAYOUT[face];
    return Array.from({ length: 9 }, (_, index) => {
      const row = Math.floor(index / 3);
      const column = index % 3;
      const position = addVector(
        addVector(layout.normal, layout.right, column - 1),
        layout.down,
        row - 1,
      );
      return {
        face,
        index,
        position: addVector(position, layout.normal, 0.51),
        rotation: faceRotation(face),
        cubie: position,
      };
    });
  });
}

function faceRotation(face: FaceName): Vector {
  switch (face) {
    case "U": return [-Math.PI / 2, 0, 0];
    case "D": return [Math.PI / 2, 0, 0];
    case "R": return [0, Math.PI / 2, 0];
    case "L": return [0, -Math.PI / 2, 0];
    case "B": return [0, Math.PI, 0];
    default: return [0, 0, 0];
  }
}

function cubiePositions(): Vector[] {
  return [-1, 0, 1].flatMap((y) =>
    [-1, 0, 1].flatMap((z) =>
      [-1, 0, 1].map((x) => [x, y, z] as Vector),
    ),
  );
}

function animationTransform(move?: Move, progress = 0): { rotation: Vector; angle: number } {
  if (!move || progress <= 0 || progress >= 1) return { rotation: [0, 0, 0], angle: 0 };
  const axis: Record<FaceName, Vector> = {
    U: [0, 1, 0], D: [0, -1, 0], F: [0, 0, 1], B: [0, 0, -1], L: [-1, 0, 0], R: [1, 0, 0],
  };
  const turns = move.endsWith("2") ? 2 : 1;
  const direction = move.includes("'") ? -1 : 1;
  return { rotation: axis[move[0] as FaceName], angle: direction * turns * Math.PI / 2 * progress };
}

function isTurningLayer(position: Vector, move?: Move): boolean {
  if (!move) return false;
  const normal = FACE_LAYOUT[move[0] as FaceName].normal;
  return position[0] * normal[0] + position[1] * normal[1] + position[2] * normal[2] > 0.5;
}

function Cubie({
  position,
  stickers,
  state,
  onFaceMove,
}: {
  position: Vector;
  stickers: StickerDefinition[];
  state: CubeState;
  onFaceMove?: ((face: FaceName) => void) | undefined;
}) {
  return (
    <group position={position}>
      <mesh>
        <boxGeometry args={[0.94, 0.94, 0.94]} />
        <meshStandardMaterial color="#101412" roughness={0.5} />
      </mesh>
      {stickers.map(({ face, index, rotation }) => (
        <mesh
          key={`${face}-${index}`}
          position={FACE_LAYOUT[face].normal.map((axis) => axis * 0.51) as Vector}
          rotation={rotation}
          onClick={(event) => {
            event.stopPropagation();
            onFaceMove?.(face);
          }}
        >
          <planeGeometry args={[0.8, 0.8]} />
          <meshStandardMaterial color={DEFAULT_FACE_COLORS[state[face][index] as CubeColor]} roughness={0.32} />
        </mesh>
      ))}
    </group>
  );
}

export function Cube3D({
  state,
  animationMove,
  animationProgress = 0,
  onFaceMove,
  className,
}: Cube3DProps) {
  const stickers = useMemo(() => stickerDefinitions(), []);
  const cubies = useMemo(() => cubiePositions(), []);
  const animation = animationTransform(animationMove, animationProgress);

  return (
    <div className={className} style={{ width: "100%", height: "100%", minHeight: 320 }}>
      <Canvas camera={{ position: [5, 4, 6], fov: 42 }} dpr={[1, 2]}>
        <color attach="background" args={["#10151c"]} />
        <ambientLight intensity={1.8} />
        <directionalLight position={[4, 6, 5]} intensity={3} />
        <group>
          {cubies.map((position) => {
            const cubieStickers = stickers.filter((sticker) =>
              sticker.cubie[0] === position[0] &&
              sticker.cubie[1] === position[1] &&
              sticker.cubie[2] === position[2],
            );
            const turnsWithFace = isTurningLayer(position, animationMove);
            const rotation: Vector = turnsWithFace
              ? [
                  animation.rotation[0] * animation.angle,
                  animation.rotation[1] * animation.angle,
                  animation.rotation[2] * animation.angle,
                ]
              : [0, 0, 0];
            return <group key={position.join(":")} rotation={rotation}><Cubie position={position} stickers={cubieStickers} state={state} onFaceMove={onFaceMove} /></group>;
          })}
        </group>
        <OrbitControls enablePan={false} minDistance={4} maxDistance={10} />
      </Canvas>
    </div>
  );
}

export interface CubeCanvasProps extends Cube3DProps {
  canvasClassName?: string;
}

export function CubeCanvas({ canvasClassName, ...props }: CubeCanvasProps) {
  return <Cube3D {...props} className={canvasClassName ?? props.className} />;
}
