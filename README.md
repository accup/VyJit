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


## Remarks
- Currently, all my signal processing developments are contained in the `analyzers` directory, but it would be so ugly for the cloners (when there are). So, I should think about cutting git branch for my developments and the master branch would be maintained as only **enviromnents**.
