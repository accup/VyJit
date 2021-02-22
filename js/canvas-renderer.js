const d3 = require('d3');


/** [0.0, 1.0] または (0.0, 1.0] へ数値を変換する関数群 */
const AlphaConverters = {
    /** max(0.0, min(v, 1.0))
     * @param {number} value
     */
    linear(value) {
        return Math.max(0.0, Math.min(value, 1.0));
    },

    /** 1.0 - exp(-max(0.0, v))
     * @param {number} value
     */
    exponential(value) {
        return 1.0 - Math.exp(-Math.max(0.0, value));
    },

    /** 1.0 - 1.0 / (1.0 + max(0.0, v))
     * @param {number} value
     */
    inverse(value) {
        return 1.0 - 1.0 / (1.0 + Math.max(0.0, v))
    }
};


const AlignmentAnchorSelector = {
    start: (left, right) => left,
    end: (left, right) => right,
    left: (left, right) => left,
    right: (left, right) => right,
    center: (left, right) => 0.5 * (left + right)
};

const BaselineAnchorSelector = {
    top: (top, bottom) => top,
    hanging: (top, bottom) => 0.8 * top + 0.2 * bottom,
    middle: (top, bottom) => 0.5 * (top + bottom),
    alphabetic: (top, bottom) => 0.35 * top + 0.65 * bottom,
    ideographic: (top, bottom) => 0.2 * top + 0.8 * bottom,
    bottom: (top, bottom) => bottom
};


export class ColorBar {
    /**
     * 
     * @param {number} key キー値
     */
    getColor(key) {
        return { r: 0.0, g: 0.0, b: 0.0, a: 0.0 };
    }
}

export class SectionColorBar extends ColorBar {
    /**
     * 
     * @param {{key: number, color:{ r?: number, g?: number, b?: number, a?: number }}[]} sections key in Real, 0.0 <= r, g, b, a <= 1.0) の配列
     */
    constructor(sections) {
        super();

        const sorted_sections = sections
            .map(({ key, color = {} }) => ({
                key,
                color: {
                    r: ('r' in color) ? Math.max(0.0, Math.min(color.r, 1.0)) : 0.0,
                    g: ('g' in color) ? Math.max(0.0, Math.min(color.g, 1.0)) : 0.0,
                    b: ('b' in color) ? Math.max(0.0, Math.min(color.b, 1.0)) : 0.0,
                    a: ('a' in color) ? Math.max(0.0, Math.min(color.a, 1.0)) : 1.0,
                },
            }))
            .sort(({ key: key_a }, { key: key_b }) => key_a - key_b);
        this.keys = sorted_sections.map(({ key }) => key);
        this.colors = sorted_sections.map(({ color }) => color);
    }

    /**
     * 
     * @param {number} key キー値
     */
    getColor(key) {
        const index = d3.bisectLeft(this.keys, key);

        if (index == 0) {
            return {
                r: this.colors[index].r,
                g: this.colors[index].g,
                b: this.colors[index].b,
                a: this.colors[index].a,
            }
        } else if (index == this.colors.length) {
            return {
                r: this.colors[index - 1].r,
                g: this.colors[index - 1].g,
                b: this.colors[index - 1].b,
                a: this.colors[index - 1].a,
            }
        }

        const fromKey = this.keys[index - 1];
        const fromColor = this.colors[index - 1];
        const toKey = this.keys[index];
        const toColor = this.colors[index];

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


export class SpectrogramRenderer {
    /**
     * @param {HTMLCanvasElement} canvas
     * @param {number} n_frames
     * @param {number} n_bins
     * @param {ColorBar} colorbar
     */
    constructor(
        canvas,
        n_frames,
        n_bins,
        colorbar,
    ) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        this.nFrames = n_frames
        this.nBins = n_bins;
        this.colorbar = colorbar;

        this.canvas.width = n_frames;
        this.canvas.height = n_bins;

        this.imageData = this.ctx.createImageData(this.nFrames, this.nBins);
    }

    /**
     * @param {number} n_frames 
     */
    setNumFrames(n_frames) {
        const newImageData = this.ctx.createImageData(n_frames, this.nBins);
        const fromOffset = 4 * Math.min(0, this.nFrames - n_frames);
        const toOffset = 4 * Math.min(0, n_frames - this.nFrames);
        newImageData.data.set(this.imageData.data.subarray(fromOffset), toOffset);

        this.nFrames = n_frames;
        this.imageData = newImageData;
    }

    /**
     * @param {Float32Array|Float64Array} spectrum
     */
    push(spectrum) {
        this.imageData.data.copyWithin(0, 4);

        for (let i = 0; i < this.nBins; ++i) {
            const offset = this.imageData.data.length - 4 * this.nFrames * (i + 1) - 4;
            const color = this.colorbar.getColor(spectrum[i]);
            this.imageData.data[offset + 0] = 255 * color.r;
            this.imageData.data[offset + 1] = 255 * color.g;
            this.imageData.data[offset + 2] = 255 * color.b;
            this.imageData.data[offset + 3] = 255 * color.a;
        }
    }

    draw() {
        this.ctx.save();
        this.ctx.transform(0, 1, 1, 0, 0, 0);
        this.ctx.putImageData(this.imageData, 0, 0);
        this.ctx.restore();
    }
};