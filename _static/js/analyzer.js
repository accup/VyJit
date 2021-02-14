var analyzer;

(function () {
    /**
     * @param dtype {string}
     * @param buffer {ArrayBuffer}
     */
    function make_typed(dtype, buffer) {
        switch (dtype) {
            case "int8": {
                return new Int8Array(buffer);
            }
            case "uint8": {
                return new Uint8Array(buffer);
            }
            case "int16": {
                const view = new DataView(buffer);
                const length = view.byteLength / Int16Array.BYTES_PER_ELEMENT;
                const data = new Int16Array(length);
                for (let index = 0; index < length; ++index) {
                    const offset = index * Int16Array.BYTES_PER_ELEMENT;
                    data[index] = view.getInt16(offset, false);
                }
                return data;
            }
            case "uint16": {
                const view = new DataView(buffer);
                const length = view.byteLength / Uint16Array.BYTES_PER_ELEMENT;
                const data = new Uint16Array(length);
                for (let index = 0; index < length; ++index) {
                    const offset = index * Uint16Array.BYTES_PER_ELEMENT;
                    data[index] = view.getUint16(offset, false);
                }
                return data;
            }
            case "int32": {
                const view = new DataView(buffer);
                const length = view.byteLength / Int32Array.BYTES_PER_ELEMENT;
                const data = new Int32Array(length);
                for (let index = 0; index < length; ++index) {
                    const offset = index * Int32Array.BYTES_PER_ELEMENT;
                    data[index] = view.getInt32(offset, false);
                }
                return data;
            }
            case "uint32": {
                const view = new DataView(buffer);
                const length = view.byteLength / Uint32Array.BYTES_PER_ELEMENT;
                const data = new Uint32Array(length);
                for (let index = 0; index < length; ++index) {
                    const offset = index * Uint32Array.BYTES_PER_ELEMENT;
                    data[index] = view.getUint32(offset, false);
                }
                return data;
            }
            case "float32": {
                const view = new DataView(buffer);
                const length = view.byteLength / Float32Array.BYTES_PER_ELEMENT;
                const data = new Float32Array(length);
                for (let index = 0; index < length; ++index) {
                    const offset = index * Float32Array.BYTES_PER_ELEMENT;
                    data[index] = view.getFloat32(offset, false);
                }
                return data;
            }
            case "float64": {
                const view = new DataView(buffer);
                const length = view.byteLength / Float64Array.BYTES_PER_ELEMENT;
                const data = new Float64Array(length);
                for (let index = 0; index < length; ++index) {
                    const offset = index * Float64Array.BYTES_PER_ELEMENT;
                    data[index] = view.getFloat64(offset, false);
                }
                return data;
            }
            default: {
                throw new Error(`Unknown dtype '${dtype}'.`);
            }
        }
    }

    function bytes_to_typed(data) {
        if (typeof data == "object") {
            if (data instanceof ArrayBuffer) {
                return data;
            } else if (Array.isArray(data)) {
                return data.map(bytes_to_typed);
            } else if ('_dtype' in data) {
                return make_typed(data['_dtype'], data['_buffer']);
            } else {
                const typed = {};
                for (const prop in data) {
                    typed[prop] = bytes_to_typed(data[prop]);
                }
                return typed;
            }
        } else {
            return data;
        }
    }

    let target = new EventTarget();
    analyzer = {
        /**
         * @param event {string}
         * @param listener {(data: any) => void}
         */
        on(event, listener) {
            target.addEventListener(event, function (event) {
                listener(event.detail);
            });
        },

        /**
         * @param analyzer_name {string}
         */
        connect(analyzer_name) {
            let socket = io();
            socket.on('connect', function () {
                socket.emit('start_analysis', analyzer_name);
            });
            socket.on('properties', function (data) {
                // target.dispatchEvent(new CustomEvent('properties', {
                //     detail: bytes_to_typed(data),
                // }));
            });
            socket.on('results', function (data) {
                target.dispatchEvent(new CustomEvent('results', {
                    detail: bytes_to_typed(data),
                }));
            });
        }
    };
})();