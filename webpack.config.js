const path = require('path');
const ExtReloader = require('webpack-ext-reloader');
const CopyPlugin = require('copy-webpack-plugin');

module.exports = {
  mode: 'development',
  entry: {
    background: './background.js',
    sidepanel: './scripts/sidepanel.js'
  },
  output: {
    filename: '[name].js',
    path: path.resolve(__dirname, 'dist'),
  },
  plugins: [
    new ExtReloader({
      port: 9090,
      reloadPage: true,
      entries: {
        background: 'background',
        extensionPage: ['sidepanel'],
      }
    }),
    new CopyPlugin({
      patterns: [
        { from: "manifest.json", to: "manifest.json" },
        { from: "sidepanel.html", to: "sidepanel.html" },
        { from: "styles", to: "styles" },
        { from: "images", to: "images" }
      ],
    }),
  ],
};