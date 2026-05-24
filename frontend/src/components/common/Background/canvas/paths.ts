import { Err, match, None, Ok, Result, Some, type Option } from "oxide.ts";
import type { BackgroundConfig } from "./config";
import type { DelaunayGraph, Node, SpawnConfig, Vector2D } from "./types";
import { dist, randInt, randItem } from "./utils";

export function getSpawnConfig(
    type: 'random' | 'point' | 'center', 
    origin: Option<Vector2D>
): Result<SpawnConfig, string> {

    if (type !== "point" && origin.isSome()) return Err("You can only provide an origin if type = 'point'!")
    if (type === "point" && origin.isNone()) return Err("If type = 'point' you must provide an origin!")

    switch (type) {
        case 'center': 
            return Ok({
                type: 'point', 
                origin: {
                    x: window.innerWidth / 2, 
                    y: window.innerHeight / 2
                }
            })
        case 'point':
            return Ok({
                type: 'point',
                origin: {
                    x: origin.unwrap().x,
                    y: origin.unwrap().y
                }
            })
        default:
            return Ok({
                type: 'random'
            })
    }
}

export function filterNodes(
    nodes: Node[],
    predicate: (node: Node) => boolean
): number[] {
    return nodes
        .map((node, idx) => ({node, idx}))
        .filter((item) => predicate(item.node))
        .map(({idx}) => idx)
}

export function getStartingPointsBySpawnType(
    nodes: Node[],
    config: BackgroundConfig,
    spawnOrigin: Option<Vector2D>,
    spawnType: 'random' | 'point' | 'center'
): number[] {

    const spawnConfig  = getSpawnConfig(spawnType, spawnOrigin).expect("Invalid spawn config!")

    switch (spawnConfig.type) {
        case "point": 
            return filterNodes(
                nodes,
                (node: Node) => (dist(spawnConfig.origin.x, spawnConfig.origin.y, node.initialPos.x, node.initialPos.y) < 12*config.sampler.minDistancePx)
            )
        case "random":
            return filterNodes(
                nodes,
                (node: Node) => (
                    (node.initialPos.x >= 2*config.sampler.minDistancePx) &&
                    (node.initialPos.x <= window.innerWidth - 2*config.sampler.minDistancePx) &&
                    (node.initialPos.y >= 2*config.sampler.minDistancePx) &&
                    (node.initialPos.y <= window.innerHeight - 2*config.sampler.minDistancePx)
                )
            )
    }
}

export function selectRandomPath(
    graph: DelaunayGraph, 
    config: BackgroundConfig,
    spawnOrigin: Option<Vector2D> = None,
    spawnType: 'random' | 'point' | 'center' = 'random',
): Option<number[]> {

    if (!graph.adjacency) return None
    if (graph.nodes.length === 0) return None

    const allowedStarting = getStartingPointsBySpawnType(graph.nodes, config, spawnOrigin, spawnType)

    if (allowedStarting.length === 0) return None
    
    const allowed = filterNodes(
        graph.nodes,
        (node: Node) => (
            (node.initialPos.x >= 2*config.sampler.minDistancePx) &&
            (node.initialPos.x <= window.innerWidth - 2*config.sampler.minDistancePx) &&
            (node.initialPos.y >= 2*config.sampler.minDistancePx) &&
            (node.initialPos.y <= window.innerHeight - 2*config.sampler.minDistancePx)
        )
    )

    if (allowed.length === 0) {
        return None
    }

    const allowedSet = new Set(allowed)

    // select a random length between min and max
    const pathLength = randInt(config.pathSelection.minEdges, config.pathSelection.maxEdges)

    let previousNodeIdx: Option<number> = None

    let currentNodeIdx = allowedStarting[Math.floor(Math.random()*allowedStarting.length)] 

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