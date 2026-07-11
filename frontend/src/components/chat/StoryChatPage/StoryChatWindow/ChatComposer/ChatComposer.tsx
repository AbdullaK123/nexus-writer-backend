import { Button, Nothing } from "../../../../common";


export type ChatComposerProps = 
| { status: "idle"}
| { status: "loading" }
| { status: "error" }
| { status: "empty"}
| { 
    status: "ready"
    query: string
    onQueryChange: (query: string) => void
    onEnterDown: (query: string) => void
    onSubmit: (query: string) => void
  }


export function ChatComposer(props: ChatComposerProps) {
    switch (props.status) {
        case "idle":
        case "empty":
        case "error":
        case "loading": {
            return <Nothing /> // We'll show a 'page' loading skeleton if anything is still loading
        }
        case "ready": {
            return (
                <div>
                    {/*We'll use the field-sizing property to make it auto resizing */}
                    <textarea 
                        value={props.query}
                        onChange={(e) => props.onQueryChange(e.target.value)}
                        onKeyDown={(e) => {
                            if (e.key === "Enter" && !e.shiftKey) {
                                e.preventDefault()
                                props.onEnterDown(props.query)
                            }
                        }}
                        placeholder="Ask anything about your story..."
                    />
                    <Button
                        variant="primary"
                        onClick={() => props.onSubmit(props.query)}
                    >   
                        Ask →
                    </Button>
                </div>
            )
        }
    }
}