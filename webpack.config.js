const path = require('path');

module.exports = {
  resolve: {
    // This will allow Webpack to find modules in node_modules
    modules: [path.resolve(__dirname, 'node_modules')],
  },
  // other webpack options...
};


module.exports = {
  // ... other webpack configuration
  resolve: {
    fallback: {
      "string_decoder": require.resolve("string_decoder/"),
      "timers": require.resolve("timers-browserify")
    }
  }
};