<template>
	<div>
		<header>
			<h2 class="model" title="model name">{{model}}</h2>
			<section>
				<select v-model="fromW" class="latant-type" :title="`generate from ${fromW ? 'W' : 'Z'}`">
					<option :value="false">Z</option>
					<option :value="true">W</option>
				</select>&gt;
			</section>
			<section :class="{disabled: fromW}">
				<!--&Psi; not work?-->&#x03a8;:
				<input type="range" v-model.lazy="psi" :min="-2" :max="2" step="any" :style="{width: '600px'}" :disabled="fromW" />
				<input class="value" type="number" v-model.number="psi" step="0.001" :disabled="fromW" />
			</section>
			<section>
				<input type="checkbox" v-model="noise" title="with random noise" :disabled="fromW" />noise
			</section>
			<section>
				<input type="range" min="-14" max="2" step="0.1" v-model.number="randomIntensity" :title="`Intensity: ${Math.exp(randomIntensity)}`" />{{Math.exp(randomIntensity).toFixed(4)}}
				<button @click="randomizeFeatures">Randomize</button>
			</section>
			<section>
				<button @click="zeroFeatures">Zero</button>
			</section>
			<section>
				<a :href="tag">TAG</a>
			</section>
			<section v-if="hashLatents && !fromW">
				<em :title="`${latentDistance} RAD`">{{(latentDistance * 180 / Math.PI).toPrecision(4)}}&deg;</em>
				-<StoreInput v-model.number="slerpStep" localKey="explorerSlerpStep" :styleObj="{width: '1.6em', border: 0}" />&deg;
				<button @click="slerpToHash" :disabled="!latentDistance" title="Slerp towards to hash tag">Slerp</button>
			</section>
			<section v-if="hashLatents && fromW">
				<button @click="lerpToHash" title="Lerp towards to hash tag">Lerp</button>
			</section>
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
	import StoreInput from "./storeinput.vue";

	import * as LatentCode from "./latentCode.js"



	window.LatentCode = LatentCode;
	function parseQueries (str) {
		return str.substr(1).split("&").reduce((dict, pair) => {
			const sections = pair.split("=");
			dict[sections[0]] = sections[1];

			return dict;
		}, {});
	}


	let featureNormalFactor = 12;


	class Feature {
		constructor (value) {
			this.value = value;
		}


		get normalized () {
			return Math.tanh(this.value / featureNormalFactor);
		}


		set normalized (v) {
			this.value = Math.atanh(v) * featureNormalFactor;
		}


		randomize (intensity) {
			this.value += LatentCode.randn_bm() * intensity;
		}
	};



	export default {
		name: "index",


		components: {
			StoreInput,
		},


		data () {
			return {
				model: null,
				latents_dimensions: null,
				features: null,
				psi: 0.5,
				loading: false,
				randomIntensity: -3,
				pasteUrl: null,
				noise: true,
				fromW: false,
				hashLatents: null,
				slerpStep: 10,
			};
		},


		computed: {
			latentsBytes: {
				get () {
					if (!this.features)
						return null;

					return encodeURIComponent(btoa(String.fromCharCode.apply(null, new Uint8Array(new Float32Array(this.featureVector).buffer))));
				},

				set (value) {
					const values = LatentCode.decodeLatentsBytes(value);

					values.forEach((value, i) => {
						if (this.features && this.features[i])
							this.features[i].value = value;
					});
				},
			},


			featureVector () {
				const normalized = this.fromW ? 1 : 1 / Math.sqrt(this.features.reduce((sum, f) => sum + f.value * f.value, 0)) || 1;
				return this.features.map(f => f.value * normalized);
			},


			imageURL () {
				return `/generate?${this.fromW ? "fromW=1" : "psi=" + this.psi.toString()}${this.noise ? '' : '&randomize_noise=1'}&latents=${this.latentsBytes}`;
			},


			tag () {
				return `#${this.fromW ? "fromW=1" : "psi=" + this.psi.toString()}&latents=${this.latentsBytes}`;
			},


			latentDistance() {
				if (!this.hashLatents)
					return NaN;

				if (this.fromW)
					return LatentCode.distanceBetween(this.featureVector, this.hashLatents);
				else
					return LatentCode.angleBetween(this.featureVector, this.hashLatents);
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

				this.hashLatents = null;

				if (dict.latents) {
					this.latentsBytes = dict.latents;

					this.hashLatents = LatentCode.normalize(LatentCode.decodeLatentsBytes(dict.latents));
				}

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
					this.rotateFeatures(this.hashLatents, this.slerpStep * Math.PI / 180);
				}
			},


			lerpToHash () {
				// TODO:
			},
		},


		watch: {
			imageURL () {
				this.loading = true;
				this.pasteUrl = null;
			},


			fromW (value) {
				featureNormalFactor = value ? 12 : 0.4;
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
		margin: 20px 0;
	}

	header h2
	{
		display: inline;
	}

	header section
	{
		display: inline-block;
		margin: 0 .6em;
	}

	.latant-type
	{
		border: 0;
		font-weight: bold;
		-webkit-appearance: none;
		cursor: pointer;
	}

	/*.latant-type:hover
	{
		-webkit-appearance: menulist;
	}*/

	aside, article
	{
		display: inline-block;
		vertical-align: top;
		height: calc(100vh - 69px);
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
