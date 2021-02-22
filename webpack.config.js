const path = require('path');


module.exports = {
    mode: "production",
    entry: path.resolve(__dirname, 'src/index.ts'),
    output: {
        filename: 'bundle.js',
        path: path.resolve(__dirname, 'dist'),
    },
    resolve: {
        extensions: ['.tsx', '.ts', '.mjs', '.js'],
    },
    module: {
        rules: [
            {
                test: /\.m?js$/i,
                exclude: /node_modules/,
                use: {
                    loader: 'babel-loader',
                    options: {
                        presets: [
                            ['@babel/preset-env', { targets: "defaults" }],
                        ],
                    },
                },
            },
            {
                test: /\.tsx?$/i,
                exclude: /node_modules/,
                use: {
                    loader: 'babel-loader',
                    options: {
                        presets: [
                            ['@babel/preset-env', { targets: "defaults" }],
                            ['@babel/preset-typescript'],
                        ],
                    },
                },
            },
            {
                test: /\.css$/i,
                use: [
                    {
                        loader: 'style-loader'
                    },
                    {
                        loader: 'css-loader'
                    },
                ],
            },
        ],
    },
};