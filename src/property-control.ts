

interface IPropertyControl<T> {
    readonly name: string;
    readonly element: HTMLElement;
    value: T | null;
}


export class StringPropertyControl implements IPropertyControl<string> {
    _name;
    _control;
    _input;

    constructor(
        name: string,
        value: string,
        detail: { readonly?: boolean },
        onChange: (control: StringPropertyControl) => any,
    ) {
        this._name = name;
        const control = document.createElement('div');
        const inputId = 'property_control_input_' + name;
        control.classList.add('form-floating');
        {
            const input = document.createElement('input');
            input.classList.add('form-control');
            input.type = 'text';
            input.id = inputId;
            input.readOnly = detail.readonly ?? false;
            input.addEventListener('change', (event) => {
                onChange(this);
            });
            control.appendChild(input);
            this._input = input;
        }
        {
            const label = document.createElement('label');
            label.classList.add('form-label');
            label.htmlFor = inputId;
            label.textContent = name;
            control.appendChild(label);
        }

        this._control = control;
        this.value = value;
    }

    get name() {
        return this._name;
    }

    get element() {
        return this._control;
    }

    get value() {
        return this._input.value;
    }
    set value(value: string | null) {
        if (value == null) return;
        this._input.value = value;
    }
}


export class NumberPropertyControl implements IPropertyControl<number> {
    _name;
    _control;
    _input;

    constructor(
        name: string,
        value: number,
        detail: { readonly?: boolean, min: number | null, max: number | null, step: number | null },
        onChange: (control: NumberPropertyControl) => any,
    ) {
        this._name = name;
        const control = document.createElement('div');
        const inputId = 'property_control_input_' + name;
        control.classList.add('form-floating');
        {
            const input = document.createElement('input');
            input.classList.add('form-control');
            input.type = 'number';
            input.id = inputId;
            input.readOnly = detail.readonly ?? false;
            if (detail.min != null) input.min = detail.min.toString();
            if (detail.max != null) input.max = detail.max.toString();
            if (detail.step != null) input.step = detail.step.toString();
            input.addEventListener('change', (event) => {
                onChange(this);
            });
            control.appendChild(input);
            this._input = input;
        }
        {
            const label = document.createElement('label');
            label.classList.add('form-label');
            label.htmlFor = inputId;
            label.textContent = name;
            control.appendChild(label);
        }

        this._control = control;
        this.value = value;
    }

    get name() {
        return this._name;
    }

    get element() {
        return this._control;
    }

    get value() {
        const value = this._input.valueAsNumber;
        if (isNaN(value)) {
            return null;
        } else {
            return value;
        }
    }
    set value(value: number | null) {
        if (value == null) return;
        this._input.valueAsNumber = value;
    }
}

export class IntegerPropertyControl extends NumberPropertyControl {
    constructor(
        name: string,
        value: number,
        detail: { readonly?: boolean, min: number | null, max: number | null, step: number | null },
        onChange: (control: IntegerPropertyControl) => any,
    ) {
        super(
            name,
            value,
            {
                readonly: detail.readonly,
                min: (detail.min == null) ? null : Math.floor(detail.min),
                max: (detail.max == null) ? null : Math.ceil(detail.max),
                step: (detail.step == null) ? null : Math.round(detail.step),
            },
            onChange,
        );
    }

    get value() {
        const value = this._input.valueAsNumber;
        if (isNaN(value)) {
            return null;
        } else {
            return Math.round(value);
        }
    }
    set value(value: number | null) {
        if (value == null) return;
        this._input.valueAsNumber = Math.round(value);
    }
}



export class BooleanPropertyControl implements IPropertyControl<boolean> {
    _name;
    _control;
    _input;

    constructor(
        name: string,
        value: boolean,
        detail: { readonly?: boolean },
        onChange: (control: BooleanPropertyControl) => any,
    ) {
        this._name = name;
        const control = document.createElement('div');
        const inputId = 'property_control_input_' + name;
        control.classList.add('form-check');
        {
            const input = document.createElement('input');
            input.classList.add('form-check-input');
            input.type = 'checkbox';
            input.id = inputId;
            input.readOnly = detail.readonly ?? false;
            input.addEventListener('change', (event) => {
                onChange(this);
            });
            control.appendChild(input);
            this._input = input;
        }
        {
            const label = document.createElement('label');
            label.classList.add('form-check-label');
            label.htmlFor = inputId;
            label.textContent = name;
            control.appendChild(label);
        }

        this._control = control;
        this.value = value;
    }

    get name() {
        return this._name;
    }

    get element() {
        return this._control;
    }

    get value() {
        return this._input.checked;
    }
    set value(value: boolean | null) {
        if (value == null) return;
        this._input.checked = value;
    }
}
