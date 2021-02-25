window.addEventListener('load', function (event) {
    const canvas = document.getElementById('spectrogram');

    const chroma_renderer = new r6r.PseudoColorRenderer(
        canvas,
        256,
        new r6r.SectionColorMap([
            { key: -1, color: { r: 0, g: 1, b: 1, a: 1 } },
            { key: 0, color: { r: 0, g: 0, b: 0, a: 1 } },
            { key: 1, color: { r: 0, g: 1, b: 0, a: 1 } },
        ]),
    );
    const pass_filter_renderer = new r6r.PseudoColorRenderer(
        canvas,
        256,
        new r6r.SectionColorMap([
            { key: 0, color: { r: 1, g: 1, b: 1, a: 0.0 } },
            { key: 1, color: { r: 1, g: 1, b: 1, a: 0.2 } },
        ]),
    );
    analyzer.on('results', function (data) {
        chroma_renderer.push(data.chroma.reverse());
        chroma_renderer.draw();

        pass_filter_renderer.push(data.pass_filter.reverse());
        if (data.use_pass_filter) {
            pass_filter_renderer.draw();
        }
    });
});
