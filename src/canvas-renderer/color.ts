const d3 = require('d3');


interface Color {
    r: number,
    g: number,
    b: number,
    a: number,
}

export const Color = {
    toRgba(color: Color) {
        const r = Math.round(color.r * 255);
        const g = Math.round(color.g * 255);
        const b = Math.round(color.b * 255);
        return `rgba(${r}, ${g}, ${b}, ${color.a})`;
    }
};

interface ColorLike {
    r?: number,
    g?: number,
    b?: number,
    a?: number,
}

export class ColorMap {
    getColor(key: number): Color {
        return { r: 0.0, g: 0.0, b: 0.0, a: 0.0 };
    }
}

export class SectionColorMap extends ColorMap {
    _keys: number[]
    _colors: Color[]

    constructor(sections: { key: number, color: ColorLike }[]) {
        super();

        const sorted_sections = sections
            .map(({ key, color = {} }) => ({
                key,
                color: {
                    r: ('r' in color) ? Math.max(0.0, Math.min(color.r!, 1.0)) : 0.0,
                    g: ('g' in color) ? Math.max(0.0, Math.min(color.g!, 1.0)) : 0.0,
                    b: ('b' in color) ? Math.max(0.0, Math.min(color.b!, 1.0)) : 0.0,
                    a: ('a' in color) ? Math.max(0.0, Math.min(color.a!, 1.0)) : 1.0,
                },
            }))
            .sort(({ key: key_a }, { key: key_b }) => key_a - key_b);

        this._keys = sorted_sections.map(({ key }) => key);
        this._colors = sorted_sections.map(({ color }) => color);
    }

    getColor(key: number): Color {
        const index = d3.bisectLeft(this._keys, key);

        if (index == 0) {
            return {
                r: this._colors[index].r,
                g: this._colors[index].g,
                b: this._colors[index].b,
                a: this._colors[index].a,
            }
        } else if (index == this._colors.length) {
            return {
                r: this._colors[index - 1].r,
                g: this._colors[index - 1].g,
                b: this._colors[index - 1].b,
                a: this._colors[index - 1].a,
            }
        }

        const fromKey = this._keys[index - 1];
        const fromColor = this._colors[index - 1];
        const toKey = this._keys[index];
        const toColor = this._colors[index];

        const d = toKey - fromKey;
        const a = toKey - key;
        const b = key - fromKey;

        return {
            r: Math.max(0, Math.min((a * fromColor.r + b * toColor.r) / d, 1.0)),
            g: Math.max(0, Math.min((a * fromColor.g + b * toColor.g) / d, 1.0)),
            b: Math.max(0, Math.min((a * fromColor.b + b * toColor.b) / d, 1.0)),
            a: Math.max(0, Math.min((a * fromColor.a + b * toColor.a) / d, 1.0)),
        }
    }
}
