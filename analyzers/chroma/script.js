window.addEventListener('load', function (event) {
    const canvas = document.getElementById('spectrogram');

    const spectrum_renderer = new r6r.PseudoColorRenderer(
        canvas,
        256,
        new r6r.SectionColorMap([
            { key: 0, color: { r: 0, g: 0, b: 0, a: 1 } },
            { key: 1, color: { r: 1, g: 0, b: 0, a: 1 } },
        ]),
    );
    analyzer.on('results', function (data) {
        spectrum_renderer.push(data.spectrum.reverse());
        spectrum_renderer.draw();
    });
});
