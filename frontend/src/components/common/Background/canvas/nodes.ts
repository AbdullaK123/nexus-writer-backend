import { KdTreeSet } from "@thi.ng/geom-accel"
import { samplePoisson } from "@thi.ng/poisson"
import { randMinMax2 } from "@thi.ng/vectors"
import { Smush32, type IRandom } from "@thi.ng/random"
import { None } from "oxide.ts"
import type { Node } from "./types"

export type GenerateNodesOptions = {
    width: number
    height: number
    minDistance: number
    max?: number
    rnd?: IRandom
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
        x,
        y,
        neighbours: None,        // populated later by delaunay step
    }))
}