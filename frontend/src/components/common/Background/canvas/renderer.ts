import type { BackgroundConfig } from "./config";
import { getPacketState, spawnPacket } from "./packets";
import { type DelaunayGraph, type Renderer, type Packet, type PacketState } from "./types"

export function initCanvas2D(
    canvasEl: HTMLCanvasElement, 
    cssWidth: number, 
    cssHeight: number
): CanvasRenderingContext2D {
    const dpr = window.devicePixelRatio || 1
    canvasEl.width = cssWidth * dpr 
    canvasEl.height = cssHeight * dpr 
    canvasEl.style.width = cssWidth + 'px'
    canvasEl.style.height = cssHeight + 'px'
    const ctx = canvasEl.getContext('2d')
    if (!ctx) {
        throw Error('Canvas context is null!')
    }
    ctx.scale(dpr, dpr)
    return ctx
}

export function handleCanvas2DResize(
    ctx: CanvasRenderingContext2D,
    cssWidth: number,
    cssHeight: number
): void {
    const dpr = window.devicePixelRatio || 1
    ctx.canvas.width = cssWidth * dpr 
    ctx.canvas.height = cssHeight * dpr 
    ctx.canvas.style.width = cssWidth + 'px'
    ctx.canvas.style.height = cssHeight + 'px'
    ctx.scale(dpr, dpr)
}

export function createRenderer(
    ctx: CanvasRenderingContext2D,
    graph: DelaunayGraph,
    config: BackgroundConfig
): Renderer {
    
    let cssWidth = ctx.canvas.clientWidth
    let cssHeight = ctx.canvas.clientHeight

    const renderEdges = () => {
        const { color, widthPx, baseOpacity } = config.edge
        ctx.strokeStyle = color 
        ctx.lineWidth = widthPx
        ctx.globalAlpha = baseOpacity
        ctx.beginPath()
        for (const e of graph.edges) {
            ctx.moveTo(e.a.x, e.a.y)
            ctx.lineTo(e.b.x, e.b.y)
        }
        ctx.stroke()
        ctx.globalAlpha = 1
    }

    const renderNodes = () => {
        const { color, radiusPx, baseOpacity } = config.node
        ctx.fillStyle = color 
        ctx.globalAlpha = baseOpacity
        ctx.beginPath()
        for (const n of graph.nodes) {
            ctx.moveTo(n.x + radiusPx, n.y)
            ctx.arc(n.x, n.y, radiusPx, 0, Math.PI*2)
        }
        ctx.fill()
        ctx.globalAlpha = 1
    }

    const renderPacket = (packetState: PacketState) => {
        const packetConfig = config.packet
        ctx.globalAlpha = packetState.opacity
        ctx.fillStyle = packetConfig.color
        ctx.beginPath()
        ctx.arc(packetState.pos.x, packetState.pos.y, packetConfig.radius, 0, Math.PI * 2)
        ctx.fill()
        ctx.globalAlpha = 1
    }

    let packets: Packet[] = [] 
    let rafId: number | null = null


    return {
        start: () => {
            const tick = (timestamp: number) => {
                const t = timestamp / 1000

                ctx.clearRect(0, 0, cssWidth, cssHeight)
                renderEdges()
                renderNodes()

                if (Math.random() < 0.8) {
                    const packet = spawnPacket(graph, config)
                    if (packet.isSome()) {
                        packets = [...packets, packet.unwrap()]
                    }
                }

                packets = packets.filter((packet) => t < packet.startTime + packet.totalPathLength / packet.speed)

                packets.forEach((packet) => {
                    const packetState = getPacketState(packet, t)
                    if (packetState.isSome()) renderPacket(packetState.unwrap())
                })

                rafId = requestAnimationFrame(tick)
            }
            rafId = requestAnimationFrame(tick)
        },
        stop: () => {
            if (rafId !== null) {
                cancelAnimationFrame(rafId)
                rafId = null
            }
        },
        resize: (w, h) => {
            cssWidth = w 
            cssHeight = h 
            ctx.clearRect(0, 0, cssWidth, cssHeight)
            renderEdges()
            renderNodes()
        }
    }
}