<template>
	<div>
		<header>
			<fieldset class="vectors">
				<VectorInput ref="source" /> <span class="separator">&#x2192;</span> <VectorInput ref="target" />
			</fieldset>
			<fieldset>
				<StoreInput
					type="number"
					v-model.number="circlePointCount"
					:range="{min: 2}"
					localKey="mappingViewerCirclePointCount"
					title="point count"
					:styleObj="{width: '3em'}"
				/>
			</fieldset>
			<fieldset>
				<button @click="plot">plot</button>
			</fieldset>
		</header>
		<main>
			<CirclePlot v-if="wCircle" :center="wCenter" :circle="wCircle" />
			<canvas ref="canvas" v-show="false" />
		</main>
	</div>
</template>

<style src="./common.css"></style>
<script>
	import CirclePlot from "./circlePlot.vue";
	import VectorInput from "./vectorInput.vue";
	import StoreInput from "./storeinput.vue";

	import * as LatentCode from "./latentCode.js"
	import {downloadUrl} from "./utils.js";



	const normalizeVector = vec => {
		const magnitude = Math.max(Math.sqrt(vec.reduce(((sum, v) => sum + v * v), 0)), 1e-9);

		return vec.map(v => v / magnitude);
	};

	const rotateVector = (source, target, theta) => {
		console.assert(source.length === target.length);

		const dot = Math.min(1, Math.max(-1, target.reduce((sum, t, i) => sum + t * source[i], 0)));
		//console.assert(Math.abs(dot) <= 1, "unexpect dot:", dot, target);

		const sinOmega = Math.sqrt(1 - dot * dot);
		const sinTheta = Math.sin(theta);

		const side = target.map((t, i) => t - source[i] * dot);
		const relative = side.map(v => v * sinTheta / sinOmega);

		const cosTheta = Math.cos(theta);

		return {
			side,
			result: source.map((v, i) => v * cosTheta + relative[i]),
		};
	};

	const circleSamplePoints = (start, target, steps) => {
		let s = normalizeVector(start);
		let t = normalizeVector(target);

		const circle = [];

		const stepAngle = Math.PI * 2 / steps;

		for (let i = 0; i < steps; ++i) {
			const {side, result} = rotateVector(s, t, stepAngle);
			circle.push(result);

			s = normalizeVector(result);
			t = normalizeVector(side);
		}

		return circle;
	};



	export default {
		name: "mappingViewer",


		components: {
			CirclePlot,
			VectorInput,
			StoreInput,
		},

		
		data () {
			return {
				circlePointCount: 360,
				wCenter: null,
				wCircle: null,
			};
		},


		async created () {
			window.$main = this;

			this.wCenter = await this.mapZtoW(new Float32Array(512), 0);
		},


		methods: {
			async mapZtoW (z, psi = 1) {
				const zCode = LatentCode.encodeFloat32(z);
				const wCode = await (await fetch(`/map-z-w?psi=${psi}&z=${encodeURIComponent(zCode)}`)).text();

				return LatentCode.decodeFloat32(wCode);
			},


			async plot () {
				const zs = circleSamplePoints(this.$refs.source.vector, this.$refs.target.vector, this.circlePointCount);
				//console.log("zs:", zs);

				const ws = [];
				for (const z of zs) {
					ws.push(await this.mapZtoW(z));
				}
				//console.log("ws:", ws);

				this.wCircle = ws;
			},


			downloadSourceData () {
				const blob = new Blob([this.wCenter, ...this.wCircle]);
				downloadUrl(URL.createObjectURL(blob), "mappingSource.dat");
			},


			async downloadResultImages ({interval = 1, resolution = 256} = {}) {
				this.$refs.canvas.width = resolution;
				this.$refs.canvas.height = resolution;
				const ctx = this.$refs.canvas.getContext("2d");

				for (const [i, w] of this.wCircle.entries()) {
					if (i % interval)
						continue;

					const response = await fetch(`/generate?fromW=1&latents=${encodeURIComponent(LatentCode.encodeFloat32(w))}`);
					const blob = await response.blob();
					//downloadUrl(URL.createObjectURL(blob), `${i}.png`);

					const img = new Image();
					await new Promise(resolve => {
						img.onload = resolve;
						img.src = URL.createObjectURL(blob);
					});
					ctx.drawImage(img, 0, 0, this.$refs.canvas.width, this.$refs.canvas.height);
					const compressedBlob = await new Promise(resolve => this.$refs.canvas.toBlob(resolve, "image/webp"));

					downloadUrl(URL.createObjectURL(compressedBlob), `${i}.webp`);
				}
			},
		},
	};
</script>

<style>
	header .vectors, header .vectors > *
	{
		vertical-align: middle;
	}

	span.separator
	{
		display: inline-block;
		margin: 0 1em;
	}
</style>
