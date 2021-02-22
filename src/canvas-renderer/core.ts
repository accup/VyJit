

export interface Renderer<T> {
    push(data: T): void;

    draw(): void;
}