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
                            {props.message}
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