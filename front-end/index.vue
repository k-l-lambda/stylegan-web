<template>
	<div>
		<header>
			<span class="model">{{model}}</span>
			<!--&Psi; not work?-->{{'\u03a8:'}} <input type="range" v-model.lazy="psi" :min="-2" :max="2" step="any" :style="{width: '600px'}" /> <input class="value" type="number" v-model.number="psi" step="0.001" />
			<input type="checkbox" v-model="noise" title="with random noise" />
			<input type="range" min="-14" max="2" step="0.1" v-model.number="randomIntensity" :title="`Intensity: ${Math.exp(randomIntensity)}`" /> <button @click="randomizeFeatures">Randomize</button>
			<button @click="zeroFeatures">Zero</button>
			<a :href="tag">tag</a>	<button @click="slerpToHash">slerp</button>
			<button @click="discriminate">discriminate</button>
			<span v-if="discriminateResult">{{discriminateResult.toFixed(4)}}</span>
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
		</article>
	</div>
</template>

<script>
	function randn_bm() {
		const u = 1 - Math.random();
		const v = 1 - Math.random();

		return Math.sqrt( -2 * Math.log( u ) ) * Math.cos( 2 * Math.PI * v );
	}


	function decodeLatentsBytes (code) {
		const str = atob(decodeURIComponent(code));

		const uint8 = str.split("").map(c => c.charCodeAt(0));
		return new Float32Array(new Uint8Array(uint8).buffer);
	}


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
				discriminateResult: null,
				pasteUrl: null,
				noise: true,
			};
		},


		computed: {
			latentsBytes: {
				get () {
					if (!this.features)
						return null;

					const length = Math.sqrt(this.features.reduce((sum, f) => sum + f.value * f.value, 0)) || 1;

					return encodeURIComponent(btoa(String.fromCharCode.apply(null, new Uint8Array(new Float32Array(this.features.map(f => f.value / length)).buffer))));
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
				return `/generate?psi=${this.psi}${this.noise ? '' : '&randomize_noise=1'}&latents=${this.latentsBytes}`;
			},


			tag () {
				return `#psi=${this.psi}&latents=${this.latentsBytes}`;
			},
		},


		async mounted () {
			window.__main = this;

			const res = await fetch("/spec");
			const spec = await res.json();
			console.log("spec:", spec);

			Object.assign(this, spec);

			this.features = Array(spec.latents_dimensions).fill().map(() => new Feature(0));

			window.onhashchange = () => this.loadHash();

			if (location.hash)
				this.loadHash();

			document.onpaste = event => this.onPaste(event);
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


			async discriminate () {
				const url = this.pasteUrl || this.imageURL;
				const response = await fetch(url);
				const blob = await response.blob();

				const form = new FormData();
				form.append("image", blob);
				const res2 = await fetch("/discriminate", {
					method: "POST",
					body: form,
				});

				this.discriminateResult = Number(await res2.text());

				console.log("discriminate:", this.discriminateResult);
			},


			async onPaste (event) {
				//console.log("onPaste:", [...event.clipboardData.items].map(i => i.type));
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
			},
		},


		watch: {
			imageURL () {
				this.loading = true;
				this.discriminateResult = null;
				this.pasteUrl = null;
			},
		},
	};
</script>

<style>
	html
	{
		overflow: hidden;
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

	/*ol
	{
		padding: 0;
	}

	li
	{
		list-style: none;
	}*/

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
