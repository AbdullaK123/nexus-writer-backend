import { describe, expect, test } from "vitest"

import { SingleFlightGate } from "../../../src/shared/singleFlight"

describe("SingleFlightGate", () => {
    test("allows only one in-flight operation", () => {
        const gate = new SingleFlightGate()

        expect(gate.tryStart()).toBe(true)
        expect(gate.tryStart()).toBe(false)
        expect(gate.isActive).toBe(true)
    })

    test("allows another operation after completion", () => {
        const gate = new SingleFlightGate()

        expect(gate.tryStart()).toBe(true)
        gate.finish()
        expect(gate.tryStart()).toBe(true)
    })
})
