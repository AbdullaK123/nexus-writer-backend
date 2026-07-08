import { Mark, mergeAttributes, type RawCommands } from "@tiptap/core"
import { Plugin } from "@tiptap/pm/state";



export const Highlight = Mark.create({
    name: "highlight",
    inclusive: false,
    addAttributes() {
        return {
            color: {
                default: 'rgba(255, 255, 0, 0.5)',
                parseHTML: (e) => e.getAttribute('data-color'),
                renderHTML: (attrs) => ({
                    'data-color': attrs.color,
                    style: `background-color: ${attrs.color}`
                })
            }
        }
    },
    renderHTML({ HTMLAttributes}) {
        return ["span", mergeAttributes(HTMLAttributes, { class: "highlight" }), 0]
    },
    parseHTML() {
        return [
            {tag: "span.highlight"},
            {tag: "span[data-color]"}
        ]
    },
    addCommands() {
        return {
            ...this.parent?.(),
            toggleHighlight: (attrs: Record<string, unknown>) => ({ commands }: { commands: RawCommands}) => {
                return commands.toggleMark(this.name, attrs)
            },
            setHighlight: (attrs: Record<string, unknown>) => ({ commands }: { commands: RawCommands}) => {
                return commands.setMark(this.name, attrs)
            },
            unsetHighlight: () => ({ commands }: { commands: RawCommands}) => {
                return commands.unsetMark(this.name)
            }
        }
    },
    addProseMirrorPlugins() {
        return [
            new Plugin({
                props: {
                    handleClickOn(view) {
                        const { state, dispatch } = view
                        const markType = state.schema.marks.highlight

                        if (!markType) return false

                        // Find if the highlight mark exists anywhere in the document
                        let hasHighlight = false
                        state.doc.descendants((node) => {
                            if (node.marks.some(mark => mark.type === markType)) {
                                hasHighlight = true;
                                return false; // stop scanning this branch
                            }
                        })

                        // If a highlight exists in the doc, remove it on click
                        if (hasHighlight) {
                            const tr = state.tr.removeMark(0, state.doc.content.size, markType)
                            dispatch(tr)
                            return true // Event handled
                        }

                        return false
                    }
                }
            })
        ]
    }
})