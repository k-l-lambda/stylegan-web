
import path from "path";
import vue from "rollup-plugin-vue";
import commonjs from "@rollup/plugin-commonjs";
import replace from "@rollup/plugin-replace";
//import alias from "@rollup/plugin-alias";
import resolve from "@rollup/plugin-node-resolve";



export default [
	"index",
	"projector",
	"merger",
].map(entry => ({
	input: `./app/${entry}.js`,

	output: {
		format: "iife",
		file: path.posix.join("dist", `${entry}.bundle.js`),
		/*globals: {
			"face-api.js": "face-api.js",
		},*/
	},

	plugins: [
		replace({
			"process.env.NODE_ENV": JSON.stringify("development"),
			"process.env.VUE_ENV": JSON.stringify("browser"),
		}),
		/*alias({
			//vue: require.resolve("vue/dist/vue.runtime.esm.js"),
			jszip: require.resolve("jszip/dist/jszip.min.js"),
			//"gif.js.optimized": require.resolve("gif.js.optimized/dist/gif.js"),
			//"js-md5": require.resolve("js-md5/build/md5.min.js"),
			//"face-api.js": require.resolve("face-api.js/dist/face-api.min.js"),
		}),*/
		commonjs(),
		resolve({
			preferBuiltins: false,
			browser: true,
		}),
		vue(),
	],
}));
