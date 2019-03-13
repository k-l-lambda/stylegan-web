<template>
	<div>
		<header>
			<span class="model">{{model}}</span>
			<!--&Psi; not work?-->{{'\u03a8:'}} <input type="range" v-model.lazy="psi" :min="-2" :max="2" step="any" :style="{width: '600px'}" /> <em class="value">{{psi}}</em>
		</header>
		<aside>
			<ol v-if="features">
				<li v-for="(feature, index) of features" :key="index">
					<input type="range" class="feature-bar" v-model.lazy="feature.normalized" :min="-0.99999999" :max="0.99999999" step="any" /> <em class="value">{{feature.value.toPrecision(4)}}</em>
				</li>
			</ol>
		</aside>
		<article>
			<img v-if="latentsBytes" :src="`/generate?psi=${psi}&latents=${latentsBytes}`" />
		</article>
	</div>
</template>

<script>
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
	};



	export default {
		name: "index",


		data () {
			return {
				model: null,
				latents_dimensions: null,
				features: null,
				psi: 0.7,
			};
		},


		computed: {
			latentsBytes () {
				if (!this.features)
					return null;

				return encodeURIComponent(btoa(String.fromCharCode.apply(null, new Uint8Array(new Float32Array(this.features.map(f => f.value)).buffer))));
			},
		},


		async mounted () {
			window.__main = this;

			const res = await fetch("/spec");
			const spec = await res.json();
			console.log("spec:", spec);

			Object.assign(this, spec);

			this.features = Array(spec.latents_dimensions).fill().map(() => new Feature(0));
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
</style>
