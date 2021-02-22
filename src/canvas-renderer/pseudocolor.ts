import { Renderer } from "./core"
import { Color, ColorMap } from "./color"


export class PseudoColorRenderer implements Renderer<Float32Array | Float64Array> {
    _canvas: HTMLCanvasElement
    _ctx: CanvasRenderingContext2D
    _frame: number
    _nFrames: number
    _colorMap: ColorMap

    _data: Float32Array | Float64Array


    constructor(
        canvas: HTMLCanvasElement,
        n_frames: number,
        color_map: ColorMap,
    ) {
        this._canvas = canvas;
        this._ctx = this._canvas.getContext('2d')!;
        this._nFrames = n_frames;
        this._colorMap = color_map;

        this._frame = this._nFrames - 1;
        this._data = new Float32Array();

        this._init();
    }

    _init() {
        this._ctx.save();
        this._ctx.globalAlpha = 1.0;
        this._ctx.fillStyle = Color.toRgba(this._colorMap.getColor(0));
        this._ctx.fillRect(0, 0, this._canvas.width, this._canvas.height);
        this._ctx.restore();
    }

    push(data: Float32Array | Float64Array) {
        this._data = data.slice();
        ++this._frame;
        if (this._nFrames <= this._frame) {
            this._frame = 0;
        }
    }

    draw() {
        const n_bins = this._data.length;
        if (n_bins == 0) return;

        const width = this._canvas.width;
        const height = this._canvas.height;
        /** 新しいフレームを描画する左端位置 */
        const left = Math.round(width * this._frame / this._nFrames);
        /** 新しいフレームを描画する右端位置 */
        const right = Math.round(width * (this._frame + 1) / this._nFrames);

        // 新しいフレームを描画する場所をクリア
        this._ctx.clearRect(left, 0, right - left, height);

        this._ctx.save();
        this._ctx.globalAlpha = 1.0;

        for (let index = 0; index < n_bins; ++index) {
            const top = height * index / n_bins;
            const bottom = height * (index + 1) / n_bins;

            /** データ値 */
            const value = this._data[index];

            // データ値にカラーマップを適用して描画色を決定
            this._ctx.fillStyle = Color.toRgba(this._colorMap.getColor(value));
            // データ値を矩形として描画
            this._ctx.fillRect(left, top, right - left, Math.max(1, bottom - top));
        }

        this._ctx.restore();
    }
};
