
import path from "path";
import vue from "rollup-plugin-vue";
import commonjs from "rollup-plugin-commonjs";
import replace from "rollup-plugin-replace";
import alias from "rollup-plugin-alias";



export default [
	"index",
	"projector",
	"merger",
].map(entry => ({
	input: `./app/${entry}.js`,

	output: {
		format: "iife",
		file: path.posix.join("dist", `${entry}.bundle.js`),
	},

	plugins: [
		replace({
			"process.env.NODE_ENV": JSON.stringify("development"),
			"process.env.VUE_ENV": JSON.stringify("browser"),
		}),
		commonjs(),
		vue(),
		alias({
			vue: require.resolve("vue/dist/vue.runtime.esm.js"),
			jszip: require.resolve("jszip/dist/jszip.min.js"),
			"gif.js.optimized": require.resolve("gif.js.optimized/dist/gif.js"),
		}),
	],
}));
