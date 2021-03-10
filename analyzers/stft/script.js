window.addEventListener('load', function (event) {
    const window_canvas = document.getElementById('window');
    const spectrogram_canvas = document.getElementById('spectrogram');

    const window_context = {
        size: 1,
    };
    const window_renderer = new r6r.PlotRenderer(
        window_canvas,
        { left: 0, top: 0, width: 1, height: 1 },
        bin => ({ x: 0, y: (1 - (bin + 0.5) / window_context.size) }),
        value => ({ x: (0.1 + 0.8 * (1 - value)), y: 0 }),
    );
    const spectrum_renderers = [
        new r6r.PseudoColorRenderer(
            spectrogram_canvas,
            256,
            new r6r.SectionColorMap([
                { key: 0, color: { r: 0, g: 0, b: 0, a: 1 } },
                { key: 1, color: { r: 0, g: 1, b: 0, a: 1 } },
            ]),
        ),
        new r6r.PseudoColorRenderer(
            spectrogram_canvas,
            256,
            new r6r.SectionColorMap([
                { key: 0, color: { r: 0, g: 0, b: 1, a: 0 } },
                { key: 1, color: { r: 0, g: 0, b: 1, a: 1 } },
            ]),
        ),
    ];
    analyzer.on('results', function (data) {
        window_context.size = data.window.length;

        window_renderer.push(data.window);
        window_renderer.draw();

        for (let channel = 0; channel < data.spectrum.length; ++channel) {
            spectrum_renderers[channel].push(data.spectrum[channel].reverse());
            spectrum_renderers[channel].draw();
        }
    });
});
