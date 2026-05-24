import { Delaunay } from "d3-delaunay"
import { type Node, type Edge, type DelaunayGraph} from './types'


export function triangulate(nodes: Node[]): DelaunayGraph {
    
    const delaunay = Delaunay.from(
        nodes,
        (n) => n.initialPos.x,
        (n) => n.initialPos.y
    )

    const seen = new Set<number>()
    const edges: Edge[] = []
    const adjacency: number[][] = nodes.map(() => [])
    const N = nodes.length

    for (let k = 0; k < delaunay.triangles.length; k += 3) {
        const t0 = delaunay.triangles[k]
        const t1 = delaunay.triangles[k+1]
        const t2 = delaunay.triangles[k+2]

        for (const [i, j] of [[t0, t1], [t1, t2], [t2, t0]] as const) {
            const lo = i < j ? i : j 
            const hi = i < j ? j : i 
            const key = lo*N + hi
            if (seen.has(key)) continue
            seen.add(key)
            adjacency[lo].push(hi)
            adjacency[hi].push(lo)
            edges.push({
                a: nodes[lo],
                b: nodes[hi]
            })
        }
    }

    return {
        nodes: nodes,
        edges: edges,
        adjacency: adjacency
    }
    
}