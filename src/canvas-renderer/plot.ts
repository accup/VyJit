import { Renderer } from "./core"
import { Color } from "./color"


interface Point {
    x: number;
    y: number;
}

interface ViewBox {
    left: number;
    top: number;
    width: number;
    height: number;
}


export class PlotRenderer implements Renderer<Float32Array | Float64Array> {
    _canvas: HTMLCanvasElement
    _ctx: CanvasRenderingContext2D
    _viewBox: ViewBox;
    _binToPoint: (bin: number) => Point;
    _valueToPoint: (value: number) => Point;
    _color: Color

    _data: Float32Array | Float64Array


    constructor(
        canvas: HTMLCanvasElement,
        viewBox: ViewBox,
        binToPoint: (bin: number) => Point,
        valueToPoint: (value: number) => Point,
        color: Color,
    ) {
        this._canvas = canvas;
        this._ctx = this._canvas.getContext('2d')!;
        this._viewBox = Object.assign({}, viewBox);
        this._binToPoint = binToPoint;
        this._valueToPoint = valueToPoint;
        this._color = Object.assign({}, color);

        if (Math.abs(this._viewBox.width) < 1) {
            if (this._viewBox.width < 0) {
                this._viewBox.width = -1;
            } else {
                this._viewBox.width = 1;
            }
        }
        if (Math.abs(this._viewBox.height) < 1) {
            if (this._viewBox.height < 0) {
                this._viewBox.height = -1;
            } else {
                this._viewBox.height = 1;
            }
        }

        this._data = new Float32Array();

        this._init();
    }

    _init() {
        this._ctx.save();
        this._ctx.globalAlpha = 1.0;
        this._ctx.fillStyle = Color.toRgba(this._color);
        this._ctx.fillRect(0, 0, this._canvas.width, this._canvas.height);
        this._ctx.restore();
    }

    push(data: Float32Array | Float64Array) {
        this._data = data.slice();
    }

    draw() {
        const n_bins = this._data.length;
        if (n_bins == 0) return;

        const width = this._canvas.width;
        const height = this._canvas.height;
        const viewBox = this._viewBox;

        // 新しいデータを描画する場所をクリア
        this._ctx.clearRect(0, 0, width, height);

        this._ctx.save();
        this._ctx.globalAlpha = 1.0;
        this._ctx.strokeStyle = Color.toRgba(this._color);

        this._ctx.beginPath();
        for (let index = 0; index < n_bins; ++index) {
            const value = this._data[index];
            const binPoint = this._binToPoint(index);
            const valuePoint = this._valueToPoint(value);

            const x = (binPoint.x + valuePoint.x - viewBox.left) * width / viewBox.width;
            const y = (binPoint.y + valuePoint.y - viewBox.top) * height / viewBox.height;

            if (index == 0) {
                this._ctx.moveTo(x, y);
            } else {
                this._ctx.lineTo(x, y);
            }
        }
        this._ctx.stroke();
        this._ctx.restore();
    }
};
