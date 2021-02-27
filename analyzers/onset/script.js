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
    const bank_renderer = new r6r.PseudoColorRenderer(
        canvas,
        256,
        new r6r.SectionColorMap([
            { key: 0, color: { r: 1, g: 1, b: 1, a: 0.0 } },
            { key: 1, color: { r: 1, g: 1, b: 1, a: 0.1 } },
        ]),
    );
    analyzer.on('results', function (data) {
        spectrum_renderer.push(data.spectrum.reverse());
        spectrum_renderer.draw();

        bank_renderer.push(data.filter_bank_sum.reverse());
        bank_renderer.draw();
    });
});
