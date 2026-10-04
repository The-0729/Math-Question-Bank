export type InlinePart =
    | { kind: "text"; value: string }
    | { kind: "formula"; value: string; libreOffice: boolean };

type Token = { kind: "group" | "value" | "quoted"; value: string };

const commands: Record<string, string> = {
    alpha: "\\alpha",
    beta: "\\beta",
    cdot: "\\cdot",
    cos: "\\cos",
    div: "\\div",
    ge: "\\geq",
    infty: "\\infty",
    int: "\\int",
    le: "\\leq",
    ln: "\\ln",
    log: "\\log",
    neq: "\\neq",
    pi: "\\pi",
    sin: "\\sin",
    sqrt: "\\sqrt",
    sum: "\\sum",
    tan: "\\tan",
    theta: "\\theta",
    times: "\\times",
};

const symbols: Record<string, string> = {
    "−": "-",
    "–": "-",
    "×": "\\times",
    "·": "\\cdot",
    "÷": "\\div",
    "≤": "\\leq",
    "≥": "\\geq",
    "≠": "\\neq",
    "±": "\\pm",
    "∞": "\\infty",
    "π": "\\pi",
    "∈": "\\in",
    "∉": "\\notin",
    "∑": "\\sum",
    "∫": "\\int",
    "√": "\\sqrt",
};

function readGroup(source: string, start: number): { value: string; end: number } | undefined {
    let depth = 0;
    let quoted = false;

    for (let index = start; index < source.length; index += 1) {
        const character = source[index];
        if (character === '"') quoted = !quoted;
        if (quoted) continue;
        if (character === "{") depth += 1;
        if (character === "}") {
            depth -= 1;
            if (depth === 0) return { value: source.slice(start + 1, index), end: index + 1 };
        }
    }

    return undefined;
}

function tokenize(source: string): Token[] {
    const tokens: Token[] = [];

    for (let index = 0; index < source.length;) {
        const character = source[index];
        if (/\s/.test(character)) {
            index += 1;
            continue;
        }

        if (character === "{") {
            const group = readGroup(source, index);
            if (group) {
                tokens.push({ kind: "group", value: libreOfficeMathToTex(group.value) });
                index = group.end;
                continue;
            }
        }

        if (character === '"') {
            const end = source.indexOf('"', index + 1);
            if (end >= 0) {
                tokens.push({ kind: "quoted", value: source.slice(index + 1, end) });
                index = end + 1;
                continue;
            }
        }

        const word = source.slice(index).match(/^[A-Za-z][A-Za-z0-9]*/)?.[0];
        if (word) {
            tokens.push({ kind: "value", value: word });
            index += word.length;
            continue;
        }

        const number = source.slice(index).match(/^\d+(?:\.\d+)?/)?.[0];
        if (number) {
            tokens.push({ kind: "value", value: number });
            index += number.length;
            continue;
        }

        tokens.push({ kind: "value", value: symbols[character] || character });
        index += 1;
    }

    return tokens;
}

function tokenTex(token: Token): string {
    if (token.kind === "group") return `{${token.value}}`;
    if (token.kind === "quoted") {
        if (token.value.length === 1) return symbols[token.value] || token.value;
        return `\\text{${token.value.replace(/[{}\\]/g, "\\$&")}}`;
    }
    if (token.value === "left") return "\\left";
    if (token.value === "right") return "\\right";
    if (token.value === "lbrace") return "\\{";
    if (token.value === "rbrace") return "\\}";
    return commands[token.value] || token.value;
}

function splitTerms(tokens: Token[]): { terms: Token[][]; operators: string[] } {
    const terms: Token[][] = [];
    const operators: string[] = [];
    let current: Token[] = [];
    let parentheses = 0;

    for (const token of tokens) {
        if (token.value === "(") parentheses += 1;
        if (token.value === ")") parentheses = Math.max(0, parentheses - 1);
        const isOperator = ["+", "-", "=", "\\neq", "\\leq", "\\geq"].includes(token.value);
        if (isOperator && parentheses === 0 && current.length > 0) {
            terms.push(current);
            operators.push(token.value);
            current = [];
        } else {
            current.push(token);
        }
    }

    if (current.length > 0) terms.push(current);
    return { terms, operators };
}

function convertTerm(tokens: Token[]): string {
    let parentheses = 0;
    const overIndex = tokens.findIndex((token) => {
        if (token.value === "(") parentheses += 1;
        if (token.value === ")") parentheses = Math.max(0, parentheses - 1);
        return token.value === "over" && parentheses === 0;
    });

    if (overIndex > 0 && overIndex < tokens.length - 1) {
        const numerator = convertTokens(tokens.slice(0, overIndex));
        const denominator = convertTokens(tokens.slice(overIndex + 1));
        return `\\frac{${numerator}}{${denominator}}`;
    }

    const output: string[] = [];
    for (let index = 0; index < tokens.length; index += 1) {
        const token = tokens[index];
        if (token.value === "nroot" && tokens[index + 1] && tokens[index + 2]) {
            output.push(`\\sqrt[${tokenTex(tokens[index + 1])}]{${tokenTex(tokens[index + 2])}}`);
            index += 2;
            continue;
        }
        output.push(tokenTex(token));
    }

    return output.join(" ");
}

function convertTokens(tokens: Token[]): string {
    const { terms, operators } = splitTerms(tokens);
    if (terms.length <= 1) return convertTerm(tokens);

    return terms.reduce((result, term, index) => {
        if (index === 0) return convertTerm(term);
        const operator = operators[index - 1];
        const spacing = operator === "+" || operator === "-" ? ` ${operator} ` : ` ${operator} `;
        return result + spacing + convertTerm(term);
    }, "");
}

export function libreOfficeMathToTex(source: string): string {
    return convertTokens(tokenize(source));
}

export function asInlineFormula(source: string): string {
    const value = source.trim();
    if (!value || value.includes("{{") || value.includes("[[")) return value;
    return `{{${value}}}`;
}

function findLibreOfficeEnd(source: string, start: number): number {
    let depth = 0;
    let quoted = false;
    for (let index = start; index < source.length; index += 1) {
        if (source[index] === '"') quoted = !quoted;
        if (quoted) continue;
        if (source[index] === "{") depth += 1;
        if (source[index] === "}") {
            if (depth === 0 && source[index + 1] === "}") return index;
            depth = Math.max(0, depth - 1);
        }
    }
    return -1;
}

export function splitInlineMath(source: string): InlinePart[] {
    const parts: InlinePart[] = [];
    let cursor = 0;

    while (cursor < source.length) {
        const libreOfficeStart = source.indexOf("{{", cursor);
        const latexStart = source.indexOf("[[", cursor);
        const nextStart = [libreOfficeStart, latexStart].filter((index) => index >= 0).sort((a, b) => a - b)[0];
        if (nextStart === undefined) break;
        if (nextStart > cursor) parts.push({ kind: "text", value: source.slice(cursor, nextStart) });

        if (nextStart === libreOfficeStart) {
            const contentStart = nextStart + 2;
            const end = findLibreOfficeEnd(source, contentStart);
            if (end < 0) {
                parts.push({ kind: "text", value: source.slice(nextStart) });
                cursor = source.length;
                break;
            }
            parts.push({ kind: "formula", value: source.slice(contentStart, end), libreOffice: true });
            cursor = end + 2;
        } else {
            const end = source.indexOf("]]", nextStart + 2);
            if (end < 0) {
                parts.push({ kind: "text", value: source.slice(nextStart) });
                cursor = source.length;
                break;
            }
            parts.push({ kind: "formula", value: source.slice(nextStart + 2, end), libreOffice: false });
            cursor = end + 2;
        }
    }

    if (cursor < source.length) parts.push({ kind: "text", value: source.slice(cursor) });
    return parts.length ? parts : [{ kind: "text", value: source }];
}