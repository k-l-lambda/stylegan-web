<template>
	<div>
		<header>
			<span class="model">{{model}}</span>
			<span :class="{disabled: fromW}">
				<!--&Psi; not work?-->&#x03a8;:
				<input type="range" v-model.lazy="psi" :min="-2" :max="2" step="any" :style="{width: '600px'}" :disabled="fromW" />
				<input class="value" type="number" v-model.number="psi" step="0.001" :disabled="fromW" />
			</span>
			<input type="checkbox" v-model="fromW" :title="`generate from ${fromW ? 'W' : 'Z'}`" /><strong>{{fromW ? "W" : "Z"}}</strong>&gt;
			<input type="checkbox" v-model="noise" title="with random noise" />noise
			<input type="range" min="-14" max="2" step="0.1" v-model.number="randomIntensity" :title="`Intensity: ${Math.exp(randomIntensity)}`" />{{Math.exp(randomIntensity).toFixed(4)}}
			<button @click="randomizeFeatures">Randomize</button>
			<button @click="zeroFeatures">Zero</button>
			<a :href="tag">tag</a>	<button @click="slerpToHash">slerp</button>
		</header>
		<aside>
			<ol v-if="features">
				<li v-for="(feature, index) of features" :key="index">
					<input type="range" class="feature-bar" v-model.lazy="feature.normalized" :min="-0.99999999" :max="0.99999999" step="any" />
					<input class="value" type="number" v-model.number="feature.value" step="0.001" />
				</li>
			</ol>
		</aside>
		<article :class="{loading}">
			<img v-if="latentsBytes" class="result" :src="pasteUrl || imageURL" @load="loading = false" />
			<img v-if="pasteUrl" class="result" :src="pasteUrl" @load="loading = false" />
		</article>
	</div>
</template>

<script>
	import {randn_bm, decodeLatentsBytes} from "./latentCode.js"



	function parseQueries (str) {
		return str.substr(1).split("&").reduce((dict, pair) => {
			const sections = pair.split("=");
			dict[sections[0]] = sections[1];

			return dict;
		}, {});
	}


	class Feature {
		constructor (value) {
			this.value = value;
		}


		get normalized () {
			return Math.tanh(this.value);
		}


		set normalized (v) {
			this.value = Math.atanh(v);
		}


		randomize (intensity) {
			this.value += randn_bm() * intensity;
		}
	};



	export default {
		name: "index",


		data () {
			return {
				model: null,
				latents_dimensions: null,
				features: null,
				psi: 0.5,
				loading: false,
				randomIntensity: 0,
				pasteUrl: null,
				noise: true,
				fromW: false,
			};
		},


		computed: {
			latentsBytes: {
				get () {
					if (!this.features)
						return null;

					const normalized = this.fromW ? 1 : 1 / Math.sqrt(this.features.reduce((sum, f) => sum + f.value * f.value, 0)) || 1;
					const featureValues = this.features.map(f => f.value * normalized);

					return encodeURIComponent(btoa(String.fromCharCode.apply(null, new Uint8Array(new Float32Array(featureValues).buffer))));
				},

				set (value) {
					const values = decodeLatentsBytes(value);

					values.forEach((value, i) => {
						if (this.features && this.features[i])
							this.features[i].value = value;
					});
				},
			},


			imageURL () {
				return `/generate?${this.fromW ? "fromW=1" : "psi=" + this.psi.toString()}${this.noise ? '' : '&randomize_noise=1'}&latents=${this.latentsBytes}`;
			},


			tag () {
				return `#${this.fromW ? "fromW=1" : "psi=" + this.psi.toString()}&latents=${this.latentsBytes}`;
			},
		},


		async mounted () {
			window.$main = this;

			const res = await fetch("/spec");
			const spec = await res.json();
			console.log("spec:", spec);

			Object.assign(this, spec);

			this.features = Array(spec.latents_dimensions).fill().map(() => new Feature(0));

			window.onhashchange = () => this.loadHash();

			if (location.hash)
				this.loadHash();
		},


		methods: {
			randomizeFeatures() {
				if (this.features)
					this.features.forEach(f => f.randomize(Math.exp(this.randomIntensity)));
			},


			zeroFeatures() {
				if (this.features)
					this.features.forEach(f => f.value = 0);
			},


			loadHash () {
				const dict = parseQueries(location.hash);
				//console.log("dict:", dict);

				this.psi = Number(dict.psi);

				if (dict.latents)
					this.latentsBytes = dict.latents;

				this.fromW = dict.fromW ? true : false;
			},


			normalizeFeatures () {
				const length = Math.sqrt(this.features.reduce((sum, f) => sum + f.value * f.value, 0));

				if (length > 0)
					this.features.forEach(f => f.value /= length);
			},


			rotateFeatures (target, theta) {
				console.assert(target.length === this.features.length);

				this.normalizeFeatures();

				const dot = Math.min(1, Math.max(-1, target.reduce((sum, t, i) => sum + t * this.features[i].value, 0)));
				//console.assert(Math.abs(dot) <= 1, "unexpect dot:", dot, target);

				const sinOmega = Math.sqrt(1 - dot * dot);
				const sinTheta = Math.sin(theta);
				if (sinOmega < sinTheta) {
					this.features.forEach((f, i) => f.value = target[i]);
					return;
				}

				const side = target.map((t, i) => t - this.features[i].value * dot);
				const relative = side.map(v => v * sinTheta / sinOmega);

				const cosTheta = Math.cos(theta);
				this.features.forEach((f, i) => f.value = f.value * cosTheta + relative[i]);
			},


			slerpToHash () {
				const targetLatents = parseQueries(location.hash).latents;
				if (targetLatents) {
					const target = decodeLatentsBytes(targetLatents);
					const length = Math.sqrt(target.reduce((sum, value) => sum + value * value, 0));
					const normalizedTarget = target.map(v => v / length);

					this.rotateFeatures(normalizedTarget, Math.PI * 0.04);
				}
			},


			/*async discriminate () {
				const url = this.pasteUrl || this.imageURL;
				const response = await fetch(url);
				const blob = await response.blob();

				const form = new FormData();
				form.append("image", new File([blob], {type: "image/png"}));
				const res2 = await fetch("/project", {
					method: "POST",
					body: form,
				});

				this.discriminateResult = Number(await res2.text());

				console.log("project:", this.discriminateResult);
			},*/


			/*async onPaste (event) {
				console.log("onPaste:", event);
				console.log("onPaste:", [...event.clipboardData.items].map(i => i.type));
				const image = [...event.clipboardData.items].filter(item => item.type.match(/image/))[0];
				if (image) {
					//console.log("image:", image.getAsFile());
					const buffer = await new Promise(resolve => {
						const reader = new FileReader();
						reader.onload = event => resolve(event.target.result);
						reader.readAsArrayBuffer(image.getAsFile());
					});
					this.pasteUrl = URL.createObjectURL(new Blob([buffer], {type: image.type}));
				}
			},*/
		},


		watch: {
			imageURL () {
				this.loading = true;
				this.pasteUrl = null;
			},
		},
	};
</script>

<style>
	html
	{
		overflow: hidden;
		font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
	}

	header
	{
		height: 2em;
	}

	aside, article
	{
		display: inline-block;
		vertical-align: top;
		height: calc(100vh - 2em - 20px);
	}

	aside
	{
		overflow-y: auto;
		font-size: 9px;
	}

	.disabled
	{
		color: #0006;
	}

	.feature-bar
	{
		width: 240px;
	}

	.model
	{
		font-size: 20px;
		font-weight: bold;
		margin: 0 1em;
	}

	.result
	{
		height: 100%;
		width: auto;
	}

	.value
	{
		border: 0;
		width: 4em;
	}

	.loading img
	{
		opacity: 0.7;
	}
</style>
