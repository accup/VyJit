# VyJit

## Installation
1. `git clone` this repository
1. `cd` the root of the cloned directory
1. `pipenv sync`
1. `npm install`
1. `npm run build`

## Usage
1. `pipenv run serve`
1. Create some stuff in the `analyzers` directory.
1. Open your browser `http://localhost:8080/analyzers/<analyzer name>` (no trailing slash).
1. Configure the properties of the analyzer in browser and check the output.
1. Update some stuff in the `analyzers` directory.
1. Reload the openned page, then the output would be update.
1. Stop the running server with <kbd>Ctrl</kbd>+<kbd>C</kbd>.

## Advanced usage
1. `pipenv run serve`
1. `npm run build/watch` in another terminal, then the webpack starts in watch mode.
1. Update some TypeScript files in the `src` directory.
1. Update some stuff in the `analyzers` directory.
1. Force-reload the openned page, then the output would be update.

## Error handling
- When an error message is raised in the analyzer, the message will be displayed in the client side.

## Logs
- v1.1.0
    - [ ] Add a built-in field 'field.select' to select a value or values from the choices.
    - [ ] Add a source selector to select a signal source from available sources (Microphones or audio files).
    - Add the second argument into every analyzer_property constructor to specify a client-side display name.
    - Make a change to every `index.html` file to use the interpolation `{{ analyzer_name }}` to specify the name of the analyzer directory. This might have been able to be used from the v0.9.9.
    - [ ] Optimize the property update routine so that property update events are dispatched after all property setting events have been processed.
    - Make the conversion between Python data and JavaScript data more strict.
    - Optimize some type annotations.
    - Update Python packages.
    - Update NPM packages.
- v1.0.1
    - Suppress the exception for static file routing when the static file directory does not exist.
    - Add an built-in analyzer 'waveform'.
    - Add an argument to specify the input device.
    - Add an analyzer property `channels` that represents the number of input signal channels.
    - Fix a problem where the input signal was not being written to the buffer correctly.
    - Catch exceptions when the input stream cannot be initialized properly.
- v1.0.0
    - Organized the `analyzers` directory.
    - Fixed some issue.
- v0.9.9
    - Implemented the basic features.
