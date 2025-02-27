const purgecss = require('@fullhuman/postcss-purgecss').default;

module.exports = {
  plugins: [
    purgecss({
      content: ['./index.html', './wizard.html', './assets/js/**/*.js'],
      defaultExtractor: content => content.match(/[\w-/:]+(?<!:)/g) || []
    }),
    require('cssnano')({
      preset: 'default',
    }),
  ],
};
