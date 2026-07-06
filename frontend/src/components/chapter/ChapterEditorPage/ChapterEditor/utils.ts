import type { Editor } from "@tiptap/react";

export function selectTextBetweenQuotes(editor: Editor, startQuote = '"', endQuote = '"') {
  // 1. Get the entire document text and the current cursor position
  const text = editor.getText()
  const currentPos = editor.state.selection.from

  // 2. Find the opening quote before the cursor
  const openingIdx = text.lastIndexOf(startQuote, currentPos - 1)
  if (openingIdx === -1) return false

  // 3. Find the closing quote after that opening quote
  const closingIdx = text.indexOf(endQuote, openingIdx + 1)
  if (closingIdx === -1) return false

  // 4. Map text indices to ProseMirror positions (+1 offsets the 0-based index)
  const selectionStart = openingIdx + 1 + 1 
  const selectionEnd = closingIdx + 1

  // 5. Apply the selection highlight
  editor.commands.setTextSelection({ 
    from: selectionStart, 
    to: selectionEnd 
  })

  return true
}
