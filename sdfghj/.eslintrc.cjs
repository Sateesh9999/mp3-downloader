module.exports = {
  env: { browser: true, es2021: true },
  extends: ['eslint:recommended', 'plugin:react/recommended', 'plugin:react-hooks/recommended'],
  parserOptions: { ecmaVersion: 'latest', sourceType: 'module' },
  settings: { react: { version: 'detect' } },
  rules: {
    // This project does not use PropTypes; component inputs are validated by
    // the backend/API instead.
    'react/prop-types': 'off',
    // Fetch callbacks are deliberately declared in the component so they can
    // use the latest UI state without recreating polling intervals.
    'react-hooks/exhaustive-deps': 'off',
  },
}
