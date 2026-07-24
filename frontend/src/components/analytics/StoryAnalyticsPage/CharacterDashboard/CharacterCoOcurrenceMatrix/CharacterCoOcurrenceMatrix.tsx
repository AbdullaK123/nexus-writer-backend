import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { CoOccurenceStatisticsRow } from "../../../../../infrastructure/api/types/analytics";


export type CharacterCoOccurenceMatrixProps = 
{
    data: CoOccurenceStatisticsRow[]
}

export function CharacterCoOccurenceMatrix(props: CharacterCoOccurenceMatrixProps) {
    return (
        <div>
            <div>
                <span>
                    [STRONGEST PAIRINGS]
                </span>
                <p>Who shares the page with whom</p>
            </div>
            <ResponsiveContainer
                width="100%"
                height="100%"
            >
                <BarChart
                    layout="vertical"
                    data={props.data}
                >
                    <CartesianGrid 
                        strokeDasharray="3 3" 
                        horizontal={false}
                    />
                    <XAxis 
                        type="number"
                        tickLine={false}
                    />
                    <YAxis 
                        dataKey={
                            (row: CoOccurenceStatisticsRow) => 
                                `${row.character_a} & ${row.character_b}`
                        }
                    />
                    <Tooltip />
                    <Legend />
                    <Bar 
                        dataKey="scene_count"
                        name="Number of scenes"
                    />
                    <Bar 
                        dataKey="word_count"
                        name="Word count"
                    />
                </BarChart>
            </ResponsiveContainer>
        </div>
    )
}