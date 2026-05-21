

export type Edge = {
    a: Node 
    b: Node
}

export type Node = Vector2D


export type DelaunayGraph = {
    nodes: Node[]
    edges: Edge[]
    adjacency: number[][]
}

// type to model a packet 
export type Vector2D = {
    x: number
    y: number
}


export type PacketState = {
    pos: Vector2D
    heading: Vector2D // unit vector for direction
    opacity: number 
}

export type Packet = {
    nodes: Node[]
    edgeLengths: number[]
    totalPathLength: number 
    startTime: number 
    speed: number
}


export type Renderer = {
    start: () => void;
    stop: () => void;
    resize: (cssWidth: number, cssHeight: number) => void;
}