import { None, Option, Some } from "oxide.ts";


export const lerp = (a: number, b: number, t: number): number =>
    a + (b-a)*t 

export const easeInOutQuad = (t: number): number => 
    t < 0.5 ? 2*t*t : 1 - Math.pow(-2*t + 2, 2) / 2

export const lerp2 = (
    ax: number, ay: number,
    bx: number, by: number,
    t: number
): [number, number] => [lerp(ax, bx, t), lerp(ay, by, t)]

export const oscillate = (
    tMs: number,
    periodMs: number,
    amplitude: number,
    phase = 0
): number => 
        amplitude*Math.sin((2*Math.PI*tMs) / periodMs + phase)

export const clamp = (v: number, lo: number, hi: number): number => 
        v < lo ? lo : v > hi ? hi : v

export const clamp01 = (v: number): number => clamp(v, 0, 1)

export const dist2 = (
    ax: number, ay: number,
    bx: number, by: number
): number => {
    const dx = bx - ax 
    const dy = by - ay 
    return dx * dx + dy *dy 
}

export const dist = (
    ax: number, ay: number, 
    bx: number, by: number 
): number => Math.sqrt(dist2(ax, ay, bx, by))

export const randInt = (
    min: number,
    max: number
) => Math.floor(Math.random() * (max - min + 1)) + min

export function randItem<T>(items: T[]): Option<T> {
    if (items.length === 0) return None
    const idx = randInt(0, items.length - 1)
    return Some(items[idx])
}