<template>
	<div @paste="onPaste" @copy.prevent="copyLatentCode">
		<header>
			<h2 v-if="spec" class="model" title="model name">{{spec.model}}</h2>
			<fieldset>
				<select v-model="fromW" class="latant-type" :title="`generate from ${fromW ? 'W' : 'Z'}`">
					<option :value="false">Z</option>
					<option :value="true">W</option>
				</select>&gt;
			</fieldset>
			<fieldset v-if="!fromW">
				<button @click="convertFromZToW" title="map Z to W">&#x2192;W</button>
			</fieldset>
			<fieldset v-show="!fromW">
				<input type="checkbox" v-model="noise" title="with random noise" :disabled="fromW" />noise
			</fieldset>
			<fieldset v-show="fromW">
				<input type="checkbox" v-model="extendFeature" />extend
			</fieldset>
			<fieldset>
				<span :title="`Randomize intensity: ${Math.exp(randomIntensity)}`">
					<input type="range" min="-14" max="2" step="0.1" v-model.number="randomIntensity" />
					{{Math.exp(randomIntensity).toFixed(4)}}
				</span>
				<button @click="randomizeFeatures">Randomize</button>
			</fieldset>
			<fieldset>
				<button @click="zeroFeatures">Zero</button>
			</fieldset>
			<fieldset>
				<a :href="tag">TAG</a>
				<button @click="copyLatentCode" title="copy latent code">&#x2398;</button>
			</fieldset>
			<fieldset v-if="hashLatents && !fromW">
				<em :title="`${latentDistance} RAD`">{{(latentDistance * 180 / Math.PI).toPrecision(4)}}&deg;</em>
				-<StoreInput v-model.number="slerpStep" localKey="explorerSlerpStep" :styleObj="{width: '1.6em', border: 0}" />&deg;
				<button @click="slerpToHash" :disabled="!latentDistance" title="Slerp towards to hash tag">Slerp</button>
			</fieldset>
			<!--fieldset v-if="hashLatents && fromW">
				<em :title="`${latentDistance}`">{{latentDistance.toPrecision(4)}}</em>
				&times;<StoreInput v-model.number="lerpFactor" localKey="explorerLerpStep" :styleObj="{width: '2em', border: 0}" />
				<button @click="lerpToHash" title="Lerp towards to hash tag">Lerp</button>
			</fieldset-->
			<fieldset v-show="!fromW" :class="{disabled: fromW}">
				<!--&Psi; not work?-->&#x03a8;:
				<input class="value" type="number" v-model.number="psi" step="0.001" :disabled="fromW" />
				<span class="psi-bar">
					<input v-show="!fromW" type="range" v-model.lazy="psi" :min="-2" :max="2" step="any" />
					<span class="scales">
						<span :style="{left: '25%'}">
							&#x25b2;<br/>-1
						</span>
						<span :style="{left: '50%'}">
							&#x25b2;<br/>0
						</span>
						<span :style="{left: '75%'}">
							&#x25b2;<br/>1
						</span>
					</span>
				</span>
			</fieldset>
			<fieldset v-show="fromW">
				Magnitude: <em :title="currentLatentsMagnitude">{{currentLatentsMagnitude.toFixed(3)}}</em>
			</fieldset>
		</header>
		<aside>
			<select v-show="useXLatents" class="layer" v-model="shownLayer" title="layer index">
				<option v-for="index of latentsLayers" :key="index" :value="index - 1">{{index - 1}}</option>
			</select>
			<p>
				<span class="scales">
					<span v-for="scale of asideScales" :key="scale" :style="{left: `${(Math.tanh(scale / featureNormalFactor()) + 1) * 50}%`}">
						{{scale}}<br/> &#x25be;<!--span class="line">&#xff5c;</span-->
					</span>
				</span>
			</p>
			<ol v-if="shownFeatures">
				<li v-for="(feature, index) of shownFeatures" :key="index">
					<input type="range" class="feature-bar" v-model.lazy="feature.normalized" :min="-0.99999999" :max="0.99999999" step="any" />
					<input class="value" type="number" v-model.number="feature.value" step="0.001" />
				</li>
			</ol>
		</aside>
		<article :class="{loading}">
			<img v-if="latentsBytes" class="result note-box" :class="{activated: copyActivated}" :src="imageURL" @load="loading = false" />
		</article>
		<div v-show="initializing" class="initializing">Model initializing, wait a moment...</div>
		<Navigator />
	</div>
</template>

<style src="./common.css"></style>

<script>
	import StoreInput from "./storeinput.vue";
	import Navigator from "./navigator.vue";

	import * as LatentCode from "./latentCode.js"



	function parseQueries (str) {
		return str.substr(1).split("&").reduce((dict, pair) => {
			const sections = pair.split("=");
			dict[sections[0]] = sections[1];

			return dict;
		}, {});
	}


	let featureNormalFactor = 0.6;


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
			Navigator,
		},


		data () {
			return {
				spec: null,
				latents_dimensions: null,
				latentsLayers: 0,
				features: null,
				featuresEx: null,
				psi: 0.5,
				initializing: false,
				loading: false,
				randomIntensity: -3,
				noise: true,
				fromW: false,
				hashLatents: null,
				slerpStep: 10,
				lerpFactor: 0.8,
				extendFeature: false,
				shownLayer: 0,
				copyActivated: false,
			};
		},


		computed: {
			useXLatents() {
				return this.fromW && this.extendFeature;
			},


			latentsBytes: {
				get () {
					if (!this.features)
						return null;

					return LatentCode.encodeFloat32(this.featureVector);
				},

				set (value) {
					const values = LatentCode.decodeFloat32(value);

					values.forEach((value, i) => {
						if (this.features && this.features[i])
							this.features[i].value = value;
					});
				},
			},


			latentsBytesEx: {
				get () {
					if (!this.featuresEx)
						return null;

					return LatentCode.encodeFixed16(this.featureVectorEx);
				},

				set (value) {
					const values = LatentCode.decodeFixed16(value);

					values.forEach((value, i) => {
						if (this.featuresEx && this.featuresEx[i])
							this.featuresEx[i].value = value;
					});
				},
			},


			latentsURL: {
				get () {
					if (!this.fromW)
						return `z:${this.psi},${this.latentsBytes}`;
					else if (!this.extendFeature)
						return `w:${this.latentsBytes}`;
					else
						return `w+:${this.latentsBytesEx}`;
				},

				set (value) {
					const [_, protocol, path] = value.match(/^([\w\+]+):(.+)$/);
					switch (protocol) {
					case "z":
						this.fromW = false;

						const [_, psi, bytes] = path.match(/^(.+),(.+)$/);
						this.psi = Number(this.psi);
						this.latentsBytes = bytes;

						break;
					case "w":
						this.fromW = true;
						this.extendFeature = false;

						this.latentsBytes = path;

						break;
					case "w+":
						this.fromW = true;
						this.extendFeature = true;
						
						this.latentsBytesEx = path;

						break;
					}
				},
			},


			shownFeatures () {
				if (!this.useXLatents)
					return this.features;

				return this.featuresEx.slice(this.shownLayer * this.latents_dimensions, (this.shownLayer + 1) * this.latents_dimensions);
			},


			featuresInUse () {
				return this.useXLatents ? this.featuresEx : this.features;
			},


			featureVector () {
				const normalized = this.fromW ? 1 : 1 / this.safeFeatureMagnitude;
				return this.features.map(f => f.value * normalized);
			},


			featureVectorEx () {
				return this.featuresEx && this.featuresEx.map(f => f.value);
			},


			featureMagnitude() {
				if (!this.features)
					return 0;

				const result = Math.sqrt(this.features.reduce((sum, f) => sum + f.value * f.value, 0));

				return result;
			},


			safeFeatureMagnitude() {
				const EPSILON = 1e-9;

				return this.featureMagnitude || EPSILON;
			},


			featureMagnitudeEx() {
				if (!this.featureVectorEx)
					return 0;

				const result = Math.sqrt(this.featureVectorEx.reduce((sum, v) => sum + v * v, 0));

				return result;
			},


			currentLatentsMagnitude () {
				return this.extendFeature ? this.featureMagnitudeEx / this.latentsLayers : this.featureMagnitude;
			},


			imageURL () {
				const latentStr = this.useXLatents ? `xlatents=${encodeURIComponent(this.latentsBytesEx)}` : `latents=${encodeURIComponent(this.latentsBytes)}`;

				return `/generate?${this.fromW ? "fromW=1" : "psi=" + this.psi.toString()}${this.noise ? "&randomize_noise=1" : ""}&${latentStr}`;
			},


			tag () {
				const latentStr = this.useXLatents ? `xlatents=${encodeURIComponent(this.latentsBytesEx)}` : `latents=${encodeURIComponent(this.latentsBytes)}`;

				return `#${this.fromW ? "fromW=1" : "psi=" + this.psi.toString()}&${latentStr}`;
			},


			latentDistance() {
				if (!this.hashLatents)
					return NaN;

				if (this.fromW)
					return LatentCode.distanceBetween(this.featureVector, this.hashLatents);
				else
					return LatentCode.angleBetween(this.featureVector, this.hashLatents);
			},

			asideScales() {
				return this.fromW ? [-10, 0, 10] : [-1, 0, 1];
			},
		},


		async mounted () {
			window.$main = this;

			this.initializing = true;
			const res = await fetch("/spec");
			this.spec = await res.json();
			console.log("model spec:", this.spec);

			this.latents_dimensions = this.spec.latents_dimensions;
			this.latentsLayers = this.spec.synthesis_input_shape[1];

			this.initializing = false;

			this.features = Array(this.spec.latents_dimensions).fill().map(() => new Feature(0));
			this.featuresEx = Array(this.spec.latents_dimensions * this.latentsLayers).fill().map(() => new Feature(0));

			window.onhashchange = () => this.loadHash();

			if (location.hash)
				this.loadHash();
		},


		methods: {
			randomizeFeatures() {
				if (this.shownFeatures)
					this.shownFeatures.forEach(f => f.randomize(Math.exp(this.randomIntensity)));
			},


			zeroFeatures() {
				if (this.featuresInUse)
					this.featuresInUse.forEach(f => f.value = 0);
			},


			loadHash () {
				const dict = parseQueries(location.hash);
				//console.log("dict:", dict);

				const psi = Number(dict.psi);
				if (Number.isFinite(psi))
					this.psi = psi;

				if (dict.xlatents) {
					this.latentsBytesEx = dict.xlatents;
					this.extendFeature = true;
				}
				else if (dict.latents) {
					this.latentsBytes = dict.latents;
					this.extendFeature = false;
				}

				this.fromW = dict.fromW ? true : false;

				this.updateHashLatents();
			},


			normalizeFeatures () {
				this.features.forEach(f => f.value /= this.safeFeatureMagnitude);
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
				this.features.forEach((f, i) => f.value = f.value * this.lerpFactor + this.hashLatents[i] * (1 - this.lerpFactor));
			},


			updateHashLatents() {
				if (this.latentsBytes) {
					const lvec = LatentCode.decodeFloat32(this.latentsBytes);
					this.hashLatents = this.fromW ? lvec : LatentCode.normalize(lvec);
				}
				else
					this.hashLatents = null;
			},


			copyLatentCode() {
				navigator.clipboard.writeText(this.latentsURL);
				console.log("Latent code copied into clipboard.");

				this.copyActivated = true;
				setTimeout(() => this.copyActivated = false, 100);
			},


			async onPaste(event) {
				//console.log("onPaste:", [...event.clipboardData.items]);
				const text = await new Promise(resolve => [...event.clipboardData.items][0].getAsString(resolve));
				//console.log("text:", text);
				try {
					// check if text is valid latent code
					/*const origin = atob(text);
					if (origin.length !== this.latents_dimensions * 4)
						throw new Error("invalid latent code");*/
					if (!/^[\w+]+:.+$/.test(text))
						throw new Error("invalid latent code");

					this.latentsURL = text;
				}
				catch(_) {
				}
			},


			featureNormalFactor() {
				return featureNormalFactor;
			},


			async convertFromZToW () {
				this.latentsBytes = await (await fetch(`/map-z-w?psi=${this.psi}&z=${encodeURIComponent(this.latentsBytes)}`)).text();
				this.fromW = true;
				this.extendFeature = false;
			},
		},


		watch: {
			imageURL () {
				this.loading = true;
			},


			fromW (value) {
				featureNormalFactor = value ? 12 : 0.6;

				this.updateHashLatents();
			},


			/*extendFeature (value) {
				// set featuresEX value by tiling features' value
				if (value)
					this.featuresEx.forEach((feature, i) => feature.value = this.features[i % this.features.length].value);
			},*/
		},
	};
</script>

<style>
	body
	{
		white-space: nowrap;
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

	header fieldset
	{
		display: inline-block;
		margin: 0 .6em;
		border: 0;
		padding: 0;
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
		height: calc(100vh - 72px);
	}

	aside
	{
		overflow-y: auto;
		font-size: 9px;
	}

	aside > *
	{
		padding-left: 3em;
	}

	aside .layer
	{
		position: absolute;
		top: 54px;
		left: 1em;
		padding-left: 0;
	}

	.disabled
	{
		color: #0006;
	}

	.feature-bar, aside .scales
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
		width: 4.1em;
	}

	.loading img
	{
		opacity: 0.7;
	}

	.scales > span
	{
		position: absolute;
		text-align: center;
		transform: translateX(-50%);
		pointer-events: none;
	}

	.psi-bar
	{
		display: inline-block;
		width: 600px;
		position: relative;
	}

	.psi-bar input
	{
		width: 100%;
	}

	.psi-bar .scales > span
	{
		font-size: 9px;
		bottom: -8px;
		color: #ccc;
	}

	aside .scales
	{
		position: absolute;
		display: inline-block;
		height: 2em;
		pointer-events: none;
		margin: 0;
		transform: translateY(-3em);
		color: #ccc;
	}

	/*.scales .line
	{
		transform: scale(1000);
	}*/
</style>
