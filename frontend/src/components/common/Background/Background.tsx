import { useRef, useEffect } from "react"
import styles from "./Background.module.css"
import { initCanvas2D, createRenderer, handleCanvas2DResize } from "./canvas/renderer"
import { generateNodes } from "./canvas/nodes"
import { triangulate } from "./canvas/triangulation"
import { DEFAULT_BACKGROUND_CONFIG } from "./canvas/config"




export function Background() {

    const canvasRef = useRef<HTMLCanvasElement>(null)

    useEffect(() => {

        if (!canvasRef.current) return 

        const rect = canvasRef.current.getBoundingClientRect()

        const config = DEFAULT_BACKGROUND_CONFIG

        const ctx = initCanvas2D(
            canvasRef.current, 
            rect.width, 
            rect.height
        )

        const nodes = generateNodes({
            width: rect.width,
            height: rect.height,
            minDistance: config.sampler.minDistancePx,
            max: config.sampler.maxNodes
        })

        const graph = triangulate(nodes)

        const renderer = createRenderer(ctx, graph, config)

        renderer.start()

        const observer = new ResizeObserver((entries) => {
            for (const entry of entries) {
                const { width, height } = entry.contentRect
                handleCanvas2DResize(ctx, width, height)
                renderer.resize(width, height)
            }
        })

        observer.observe(canvasRef.current)

        return () => {
            observer.disconnect()
            renderer.stop()
        }
    }, [])

    return <canvas ref={canvasRef} className={styles.canvas} />
}