import { zxcvbn, zxcvbnOptions } from '@zxcvbn-ts/core'
import * as zxcvbnCommonPackage from '@zxcvbn-ts/language-common'
import * as zxcvbnEnPackage from '@zxcvbn-ts/language-en'


const options = {
  translations: zxcvbnEnPackage.translations,
  graphs: zxcvbnCommonPackage.adjacencyGraphs,
  dictionary: {
    ...zxcvbnCommonPackage.dictionary,
    ...zxcvbnEnPackage.dictionary,
  },
}

zxcvbnOptions.setOptions(options)

export type PasswordStrengthResult = {
    score: number
    warning: string | null
    suggestions: string[]
}

export function getPasswordStrength(password: string): PasswordStrengthResult  {
    const result = zxcvbn(password)
    return {
        score: result.score,
        warning: result.feedback.warning,
        suggestions: result.feedback.suggestions
    }
}
