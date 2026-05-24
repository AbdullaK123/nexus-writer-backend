import type { BackgroundConfig, PacketAnimConfig } from "./config";
import { applyPhysics } from "./nodes";
import { getPacketState, spawnPacket } from "./packets";
import { type DelaunayGraph, type Renderer, type Packet, type PacketState, type Vector2D, type RadialWave } from "./types"
import { None, Option, Some } from "oxide.ts"


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
    let cachedRect = ctx.canvas.getBoundingClientRect()
    let cursorPosX = 0
    let cursorPosY = 0

    const renderEdges = () => {
        const { color, widthPx, baseOpacity } = config.edge
        ctx.strokeStyle = color 
        ctx.lineWidth = widthPx
        ctx.globalAlpha = baseOpacity
        ctx.beginPath()
        for (const e of graph.edges) {
            ctx.moveTo(e.a.currentPos.x, e.a.currentPos.y)
            ctx.lineTo(e.b.currentPos.x, e.b.currentPos.y)
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
            ctx.moveTo(n.currentPos.x + radiusPx, n.currentPos.y)
            ctx.arc(n.currentPos.x, n.currentPos.y, radiusPx, 0, Math.PI*2)
        }
        ctx.fill()
        ctx.globalAlpha = 1
    }

    const renderTrail = (packet: PacketState, config: PacketAnimConfig) => {
        const grad = ctx.createLinearGradient(
            packet.pos.x, 
            packet.pos.y, 
            packet.pos.x - packet.heading.x * config.trailLength,
            packet.pos.y - packet.heading.y * config.trailLength
        )
        grad.addColorStop(0, config.color)
        grad.addColorStop(1, `rgba(255, 255, 255, ${packet.opacity})`)
        ctx.strokeStyle = grad 
        ctx.lineWidth = 4
        ctx.beginPath()
        ctx.moveTo(packet.pos.x, packet.pos.y)
        ctx.lineTo(
            packet.pos.x - packet.heading.x * config.trailLength,
            packet.pos.y - packet.heading.y * config.trailLength
        )
        ctx.stroke()
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
    let waves: RadialWave[] = []
    let rafId: number | null = null
    let lastTime = 0
    let lastKeypressTime = 0
    let lastClick = 0

    const onWindowResize = () => {
        cachedRect = ctx.canvas.getBoundingClientRect()
    }

    const onMouseMove = (e: MouseEvent) => {
        cursorPosX = e.clientX - cachedRect.left
        cursorPosY = e.clientY - cachedRect.top
    }

    const spawnPacketBurst = (
        n: number, 
        spawnOrigin: Option<Vector2D>, 
        spawnType: 'random' | 'point' | 'center'
    ) => {
        for (let _ = 0; _ <= (n+1); _++) {
            const packet = spawnPacket(
                graph, 
                config, 
                spawnOrigin,
                spawnType
            )
            if (packet.isSome()) {
                packets.push(packet.unwrap())
            }
        }
    }

    const onKeyDown = () => {
        if (performance.now() - lastKeypressTime < 100) return
        lastKeypressTime = performance.now()
        spawnPacketBurst(25, None, 'center')
    }

    const onMouseDown = () => {
        if (performance.now() - lastClick < 100) return
        lastClick = performance.now()
        waves.push({
            origin: { x: cursorPosX, y: cursorPosY },
            startTime: performance.now() / 1000,
            amplitude: config.physics.radialWaveInitialAmplitude,
            velocity: config.physics.radialWaveInitialVelocity
        })
        spawnPacketBurst(
            25,
            Some({ x: cursorPosX, y: cursorPosY }),
            "point"
        )
    }

    window.addEventListener('resize', onWindowResize)
    window.addEventListener('mousemove', onMouseMove)
    window.addEventListener('keydown', onKeyDown)
    window.addEventListener('mousedown', onMouseDown)

    return {
        start: () => {
            const tick = (timestamp: number) => {
                
                ctx.clearRect(0, 0, cssWidth, cssHeight)

                const t = timestamp / 1000
                const dt = Math.min((timestamp - lastTime) / 1000, 0.05)
                lastTime = timestamp

                waves.forEach((wave) => {
                    wave.amplitude *= Math.exp(-config.physics.radialWaveDecayConstant*dt)
                    wave.velocity *= Math.exp(-config.physics.radialWaveDecayConstant*dt)
                })

                applyPhysics(
                    t,
                    dt,
                    graph.nodes,
                    waves,
                    {x: cursorPosX, y: cursorPosY},
                    config.physics
                )

                
                renderEdges()
                renderNodes()

                if (Math.random() < 0.10) {
                    const packet = spawnPacket(graph, config)
                    if (packet.isSome()) {
                        packets.push(packet.unwrap())
                    }
                }

                packets = packets.filter((packet) => t < packet.startTime + packet.totalPathLength / packet.speed)
                waves = waves.filter((wave) => wave.amplitude > 0.01*config.physics.radialWaveInitialAmplitude || wave.velocity > 0.01*config.physics.radialWaveInitialVelocity)

                packets.forEach((packet) => {
                    const packetState = getPacketState(packet, t)
                    if (packetState.isSome()) {
                        renderPacket(packetState.unwrap())
                        renderTrail(packetState.unwrap(), config.packet)
                    }
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
            window.removeEventListener('mousemove', onMouseMove)
            window.removeEventListener('resize', onWindowResize)
            window.removeEventListener('keydown', onKeyDown)
            window.removeEventListener('mousedown', onMouseDown)
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