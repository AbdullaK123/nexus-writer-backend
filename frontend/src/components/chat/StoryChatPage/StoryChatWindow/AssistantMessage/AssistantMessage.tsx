import { None } from "oxide.ts";
import { AvatarBadge } from "../../../../common";
import { format } from "date-fns"



export type AssistantMessageProps = 
| { status: "streaming", content: string }
| {
    status: "done"
    createdAt: Date
    latency: number
    message: string
  }


export function AssistantMessage(props: AssistantMessageProps) {
    switch (props.status) {
        case "streaming": {
            return (
                <div>
                    <AvatarBadge 
                        username="Nexus"
                        profileImgUrl={None}
                    />
                    <div>
                        <span>
                            NEXUS
                        </span>
                        <p>
                            {props.content}
                        </p>
                    </div>
                </div>
            )
        }
        case "done": {
            return (
                <div>
                    <AvatarBadge 
                        username="Nexus"
                        profileImgUrl={None}
                    />
                    <div>
                        <span>
                            {`NEXUS · ${format(props.createdAt, "HH:mm")} · ${(props.latency / 1000).toFixed(2)}s`}
                        </span>
                        <p>
                            {props.message}
                        </p>
                    </div>
                </div>
            )
        }
    }
}