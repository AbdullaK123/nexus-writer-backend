import { KdTreeSet } from "@thi.ng/geom-accel"
import { samplePoisson } from "@thi.ng/poisson"
import { randMinMax2 } from "@thi.ng/vectors"
import { Smush32, type IRandom } from "@thi.ng/random"
import type { Node, RadialWave, Vector2D } from "./types"
import type { PhysicsConfig } from "./config";

export type GenerateNodesOptions = {
    width: number
    height: number
    minDistance: number
    max?: number
    rnd?: IRandom
}

export function applyPhysics(
    t: number,
    dt: number,
    nodes: Node[], 
    waves: RadialWave[],
    cursorPos: Vector2D, 
    config: PhysicsConfig
): void {
    nodes.forEach((node) => {

        // spring force
        let fx = - config.springConstant *(node.currentPos.x - node.initialPos.x)
        let fy = - config.springConstant *(node.currentPos.y - node.initialPos.y)

        // damping
        fx += - config.dampingConstant*node.velocity.x
        fy += - config.dampingConstant*node.velocity.y

        // distance 
        const dx = node.currentPos.x - cursorPos.x 
        const dy = node.currentPos.y - cursorPos.y
        const dist = Math.sqrt(dx*dx + dy*dy)

        if (dist < config.repulsionRadius && dist > 0) {
            const mag = config.repulsionStrength * Math.pow((1 - dist / config.repulsionRadius), 2)
            fx += (dx/dist)*mag 
            fy += (dy/dist)*mag 
        }


        // radial wave calculations
        waves.forEach((wave) => {

            const dx = node.currentPos.x - wave.origin.x 
            const dy = node.currentPos.y - wave.origin.y 
            const dist = Math.sqrt(dx*dx + dy*dy)

            const innerRadius = wave.velocity * (t - wave.startTime)
            const outerRadius = innerRadius + config.radialWaveThickness

            if (dist > innerRadius && dist < outerRadius) {
                fx += (dx/dist) * wave.amplitude
                fy += (dy/dist) * wave.amplitude
            }
        })

        node.velocity.x += fx*dt
        node.velocity.y += fy*dt

        node.currentPos.x += node.velocity.x * dt 
        node.currentPos.y += node.velocity.y * dt
    })
}


export function generateNodes({
    width,
    height,
    minDistance,
    max = 2000,
    rnd = new Smush32(0xdecafbad),
}: GenerateNodesOptions): Node[] {
    
    const points = samplePoisson({
        index: new KdTreeSet(2),
        points: () => randMinMax2(null, [0, 0], [width, height], rnd),
        density: minDistance,
        max,
        quality: 500,
    })

    return points.map(([x, y]) => ({
        initialPos: { x: x, y: y},
        currentPos: { x: x, y: y},
        velocity: { x: 0, y: 0}
    }))
}