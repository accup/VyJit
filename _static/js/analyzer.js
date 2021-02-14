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

    /**
     * @param typed {Int8Array|Uint8Array|Int16Array|Uint16Array|Int32Array|Uint32Array|Float32Array|Float64Array}
     */
    function make_buffer(typed) {
        if (typed instanceof Int8Array) {
            return {
                '_dtype': "int8",
                '_buffer': typed.buffer,
            }
        } else if (typed instanceof Uint8Array) {
            return {
                '_dtype': "uint8",
                '_buffer': typed.buffer,
            }
        } else if (typed instanceof Int16Array) {
            const buffer = new ArrayBuffer(typed.byteLength);
            const view = new DataView(buffer);
            const length = typed.length;
            for (let index = 0; index < length; ++index) {
                const offset = index * Int16Array.BYTES_PER_ELEMENT;
                view.setInt16(offset, typed[index], false);
            }
            return {
                '_dtype': "int16",
                '_buffer': buffer,
            }
        } else if (typed instanceof Uint16Array) {
            const buffer = new ArrayBuffer(typed.byteLength);
            const view = new DataView(buffer);
            const length = typed.length;
            for (let index = 0; index < length; ++index) {
                const offset = index * Uint16Array.BYTES_PER_ELEMENT;
                view.setUint16(offset, typed[index], false);
            }
            return {
                '_dtype': "uint16",
                '_buffer': buffer,
            }
        } else if (typed instanceof Int32Array) {
            const buffer = new ArrayBuffer(typed.byteLength);
            const view = new DataView(buffer);
            const length = typed.length;
            for (let index = 0; index < length; ++index) {
                const offset = index * Int32Array.BYTES_PER_ELEMENT;
                view.setInt32(offset, typed[index], false);
            }
            return {
                '_dtype': "int32",
                '_buffer': buffer,
            }
        } else if (typed instanceof Uint32Array) {
            const buffer = new ArrayBuffer(typed.byteLength);
            const view = new DataView(buffer);
            const length = typed.length;
            for (let index = 0; index < length; ++index) {
                const offset = index * Uint32Array.BYTES_PER_ELEMENT;
                view.setUint32(offset, typed[index], false);
            }
            return {
                '_dtype': "uint32",
                '_buffer': buffer,
            }
        } else if (typed instanceof Float32Array) {
            const buffer = new ArrayBuffer(typed.byteLength);
            const view = new DataView(buffer);
            const length = typed.length;
            for (let index = 0; index < length; ++index) {
                const offset = index * Float32Array.BYTES_PER_ELEMENT;
                view.setFloat32(offset, typed[index], false);
            }
            return {
                '_dtype': "float32",
                '_buffer': buffer,
            }
        } else if (typed instanceof Float64Array) {
            const buffer = new ArrayBuffer(typed.byteLength);
            const view = new DataView(buffer);
            const length = typed.length;
            for (let index = 0; index < length; ++index) {
                const offset = index * Float64Array.BYTES_PER_ELEMENT;
                view.setFloat64(offset, typed[index], false);
            }
            return {
                '_dtype': "float64",
                '_buffer': buffer,
            }
        } else {
            throw new Error('Unknown typed array.');
        }
    }

    function typed_to_bytes(typed) {
        if (typeof typed == "object") {
            if (typed instanceof Int8Array
                || typed instanceof Uint8Array
                || typed instanceof Int16Array
                || typed instanceof Uint16Array
                || typed instanceof Int32Array
                || typed instanceof Uint32Array
                || typed instanceof Float32Array
                || typed instanceof Float64Array) {
                return make_buffer(typed);
            } else if (typed instanceof ArrayBuffer) {
                return typed;
            } else if (Array.isArray(typed)) {
                return typed.map(typed_to_bytes);
            } else {
                if ('_dtype' in typed) {
                    throw new Error("Illegal property '_dtype'.");
                }
                const data = {};
                for (const prop in typed) {
                    data[prop] = typed_to_bytes(typed[prop]);
                }
                return data;
            }
        } else {
            return typed;
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
    let socket = null;
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
         * 
         * @param {Object.<string, any>} properties 
         */
        setProperties(properties) {
            if (socket == null) {
                throw new Error('Not connected to an analyzer.');
            }

            socket.emit('set_properties', typed_to_bytes(properties));
        },

        /**
         * @param analyzer_name {string}
         */
        connect(analyzer_name) {
            if (socket != null) {
                throw new Error('Already connected to the analyzer.');
            }

            socket = io();
            socket.on('connect', function () {
                socket.emit('start_analysis', analyzer_name);
            });
            socket.on('disconnect', function () {
                socket = null;
            });
            socket.on('properties', function (data) {
                target.dispatchEvent(new CustomEvent('properties', {
                    detail: bytes_to_typed(data),
                }));
            });
            socket.on('results', function (data) {
                target.dispatchEvent(new CustomEvent('results', {
                    detail: bytes_to_typed(data),
                }));
            });
        }
    };
})();