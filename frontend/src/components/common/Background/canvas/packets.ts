import { Some, Option, None } from "oxide.ts";
import type { DelaunayGraph, Packet, PacketState, Vector2D } from "./types";
import { dist2, lerp2 } from "./utils";
import type { BackgroundConfig } from "./config";
import { selectRandomPath } from "./paths";




export function getPacketState(packet: Packet, t: number): Option<PacketState> {
    
    if (packet.nodes.length <= 1) return None
    if (t < packet.startTime) return None
    

    const dist = packet.speed * (t - packet.startTime)

    if (dist > packet.totalPathLength) return None

    let remaining = dist
    let onEdgeIdx = 0

    for (const length of packet.edgeLengths) {

        if (remaining > length) {
            remaining -= length
            onEdgeIdx += 1
        } else {
            break
        }
    }

    const progress = remaining / packet.edgeLengths[onEdgeIdx]

    const coords = lerp2(packet.nodes[onEdgeIdx].x, packet.nodes[onEdgeIdx].y, packet.nodes[onEdgeIdx + 1].x, packet.nodes[onEdgeIdx + 1].y, progress)
    const heading: Vector2D = {
        x: (packet.nodes[onEdgeIdx + 1].x - packet.nodes[onEdgeIdx].x) / packet.edgeLengths[onEdgeIdx],
        y: (packet.nodes[onEdgeIdx + 1].y - packet.nodes[onEdgeIdx].y) / packet.edgeLengths[onEdgeIdx]
    }

    const totalProgress = dist / packet.totalPathLength

    return Some({
        pos: { x: coords[0], y: coords[1]},
        heading: heading,
        opacity: 3*Math.pow(totalProgress, 2) - 2*Math.pow(totalProgress, 3)
    })
}


export function spawnPacket(graph: DelaunayGraph, config: BackgroundConfig): Option<Packet> {

    const path = selectRandomPath(graph, config).unwrapOr([])

    if (path.length <= 1) return None
    
    const nodes = path.map((idx) => graph.nodes[idx])
    const edgeLengths = nodes.slice(1).map((node, i) => dist2(nodes[i].x, nodes[i].y, node.x, node.y))
    const totalPacketLength = edgeLengths.reduce((a, b) => a + b, 0)

    const startTime = performance.now() / 1000

    return Some({
        nodes: nodes,
        edgeLengths: edgeLengths,
        totalPathLength: totalPacketLength,
        startTime: startTime,
        speed: config.packet.speedPxPerSec
    })
}   