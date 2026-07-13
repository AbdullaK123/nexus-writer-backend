import { None } from "oxide.ts";
import { AvatarBadge } from "../../../../common";



export type AssistantMessageProps = 
| { status: "streaming", message: string }
| {
    status: "done"
    message: string
  }


export function AssistantMessage(props: AssistantMessageProps) {
    switch (props.status) {
        case "streaming": {
            return (
                <div className="flex-row">
                    <AvatarBadge 
                        username="Nexus"
                        profileImgUrl={None}
                    />
                    <div className="flex-col properly-wrap-text">
                        <span className="color-cyan">
                            NEXUS
                        </span>
                        <p>
                            {props.message}
                        </p>
                    </div>
                </div>
            )
        }
        case "done": {
            return (
                <div className="flex-row">
                    <AvatarBadge 
                        username="Nexus"
                        profileImgUrl={None}
                    />
                    <div className="flex-col properly-wrap-text">
                        <span className="color-cyan">
                            NEXUS
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