// https://eslint.org/docs/user-guide/configuring

module.exports = {
	"root": true,
	"env": {
		"node": true,
	},
	"extends": [
		"plugin:vue/strongly-recommended",
		"@vue/standard",
	],
	"parserOptions": {
		"parser": "babel-eslint",
	},
	"rules": {
		"vue/no-async-in-computed-properties": "off",
		"vue/no-unused-components": "warn",
		"vue/no-unused-vars": "warn",
		"vue/no-use-v-if-with-v-for": "warn",
		"vue/require-v-for-key": "warn",
		"vue/no-multi-spaces": "off",
		"vue/max-attributes-per-line": "off",
		"vue/name-property-casing": "off",
		"vue/require-default-prop": "off",
		"vue/html-self-closing": "off",
		"vue/attribute-hyphenation": ["warn", "never"],
		"no-multiple-empty-lines": "off",
		"no-return-assign": "off",
		"no-sequences": "off",
		"no-extend-native": "off",
		"quotes": [
			"warn",
			"double",
		],
		"indent": [
			"warn",
			"tab",
		],
		"vue/html-indent": [
			"warn",
			"tab",
			{"baseIndent": 1},
		],
		"vue/script-indent": [
			"warn", "tab", {"baseIndent": 1},
		],
		"no-tabs": "off",
		"comma-dangle": ["warn", "always-multiline"],
		"semi": ["error", "always"],
		"curly": ["warn", "multi-or-nest"],
		"eqeqeq": "warn",
		"spaced-comment": "off",
		"object-curly-spacing": "warn",
		"brace-style": ["error", "stroustrup"],
		"camelcase": "off",
		"no-useless-escape": "warn",
		"no-unused-vars": ["warn", {varsIgnorePattern: "_"}],
		"quote-props": ["warn", "as-needed"],
		"prefer-const": "warn",
		"no-fallthrough": [
			"error",
			{
				"commentPattern": "break[\\s\\w]*omitted",
			},
		],
		"new-cap": "off",
		"no-proto": "off",
		"node/no-deprecated-api": [
			"error",
			{
				"ignoreModuleItems": [
					"url.parse",
				],
			}
		],
	},
	"plugins": [
		"eslint-plugin-html",
		"@vue/eslint-plugin",
	],
};
