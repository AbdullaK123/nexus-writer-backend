import type { Editor } from "@tiptap/core";

export function selectTextBetweenQuotes(editor: Editor, startQuote = '', endQuote = '') {
  const text = editor.getText()
  let currentPos = editor.state.selection.from

  // FIX: If cursor is at the start (common on new page load), scan from the end of the text
  if (currentPos <= 1) {
    currentPos = text.length
  }

  // Find the opening quote
  const openingIdx = text.lastIndexOf(startQuote, currentPos - 1)
  if (openingIdx === -1) return false

  // Find the closing quote
  const closingIdx = text.indexOf(endQuote, openingIdx + 1)
  if (closingIdx === -1) return false

  // Map text indices to ProseMirror positions (+1 offsets the 0-based index)
  // Note: Plain text indices don't perfectly map to ProseMirror positions 
  // if you have paragraphs or HTML tags, but this works for flat text blocks.
  const selectionStart = openingIdx + 1 
  const selectionEnd = closingIdx + endQuote.length + 1

  editor.chain().setTextSelection({ 
    from: selectionStart, 
    to: selectionEnd 
  }).setMark('highlight', { color: "yellow" }).run()

  return true
}
