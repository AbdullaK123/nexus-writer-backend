import { match, None, Some, type Option } from "oxide.ts";
import type { BackgroundConfig } from "./config";
import type { DelaunayGraph } from "./types";
import { randInt, randItem } from "./utils";

export function selectRandomPath(graph: DelaunayGraph, config: BackgroundConfig): Option<number[]> {

    if (!graph.adjacency) return None
    if (graph.nodes.length === 0) return None

    const allowed = graph.nodes
        .map((node, idx) => ({node, idx}))
        .filter((item) => (
            (item.node.x >= 15) &&
            (item.node.x <= window.innerWidth - 15) &&
            (item.node.y >= 15) &&
            (item.node.y <= window.innerHeight - 15)
        ))
        .map(({idx}) => idx)

    if (allowed.length === 0) {
        return None
    }

    const allowedSet = new Set(allowed)

    // select a random length between min and max
    const pathLength = randInt(config.pathSelection.minEdges, config.pathSelection.maxEdges)

    let previousNodeIdx: Option<number> = None
    let currentNodeIdx = allowed[Math.floor(Math.random()*allowed.length)] 

    const path = [currentNodeIdx]

    for (let i = 0; i < pathLength; i++) {

        const neighbours = graph.adjacency[currentNodeIdx].filter(n => {
            return match(previousNodeIdx, {
                Some: (val) => (n !== val) && (allowedSet.has(n)),
                None: () => true
            })
        })

        if (neighbours.length === 0) {
            return Some(path) // end it early
        }

        previousNodeIdx = Some(currentNodeIdx)
        const nextNodeIdx = randItem(neighbours).expect("filtered neighbours non-empty by guard above")

        path.push(nextNodeIdx)

        currentNodeIdx = nextNodeIdx
    }

    return Some(path)
}