window.addEventListener('load', function (event) {
    const canvas = document.getElementById('spectrogram');

    const renderer = new r6r.PseudoColorRenderer(
        canvas,
        256,
        new r6r.SectionColorMap([
            { key: -1, color: { r: 0, g: 1, b: 1, a: 1 } },
            { key: 0, color: { r: 0, g: 0, b: 0, a: 1 } },
            { key: 1, color: { r: 0, g: 1, b: 0, a: 1 } },
        ]),
    );
    analyzer.on('results', function (data) {
        renderer.push(data.reverse());
        renderer.draw();
    });
});
