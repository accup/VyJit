window.addEventListener('load', function (event) {
    const waveform_canvas = document.getElementById('waveform');

    const waveform_context = {
        size: 1,
    };
    const waveform_renderer = new r6r.PlotRenderer(
        waveform_canvas,
        { left: 0, top: 0, width: 1, height: 2 },
        bin => ({ x: ((bin + 0.5) / waveform_context.size), y: 1 }),
        value => ({ x: 0, y: -value }),
        { r: 0, g: 0, b: 1, a: 1 },
    );

    analyzer.on('results', function (data) {
        waveform_context.size = data.waveform.length;

        waveform_renderer.push(data.waveform);
        waveform_renderer.draw();
    });
});
